import argparse
import asyncio
import getpass
import sys
from typing import Optional

import tabulate
import telethon

from session_keeper import keeper, session, storage

from .version import __version__ as keeper_version


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filename",
        type=str,
        required=False,
        help="path to a sessions file",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="run keeper on test Telegram server",
    )
    return parser.parse_args()


def _answer_password() -> str:
    return getpass.getpass("Please enter a password to access sessions: ")


def run() -> None:
    args = _parse_args()
    app = CLIApp(_answer_password(), filename=args.filename, test_mode=args.test)
    asyncio.run(app.run())


class CLIApp:
    def __init__(
        self, password: str, *, filename: str = "sessions.tgsk", test_mode: bool = False
    ):
        self._keeper = keeper.Keeper.init_with_ejs(
            password, filename=filename, test_mode=test_mode
        )

    @staticmethod
    def _print_help() -> None:
        print(
            "COMMANDS:\n"
            "add\t\t\tadd telegram session\n"
            "remove <NUMBER>\t\tremove session\n"
            "list\t\t\tsessions list\n"
            "get <NUMBER>\t\tget last message from Telegram for session\n"
            "exit\t\t\texit from program"
        )

    @staticmethod
    def _print_incorrect_command() -> None:
        print(
            "You entered the command incorrectly. Enter help to find out the correct "
            "option."
        )

    @classmethod
    def _get_session_number(cls, command: str) -> Optional[int]:
        number = None
        params = command.split(" ")
        if len(params) == 2:
            number = params[1]
        if len(params) > 2:
            cls._print_incorrect_command()
            return None

        while True:
            if number is None:
                number = input(
                    "Please enter the session number (you can see it by the list "
                    "command): "
                )
            try:
                return int(number)
            except ValueError:
                number = None

    async def add(self) -> None:
        client = telethon.TelegramClient(
            session.Session(),
            self._keeper.storage.api_id,
            self._keeper.storage.api_hash,
            app_version=f"Session Keeper {keeper_version}",
        )
        if self._keeper.test_mode:
            client.session.set_dc(2, "149.154.167.40", 443)
        await client.start()

        await self._keeper.storage.add_session(client.session)
        self._keeper._clients.append(client)  # pylint: disable=W0212
        print("Session added to storage.")

    async def remove(self, command: str) -> None:
        number = self._get_session_number(command)
        if number is None:
            return
        try:
            await self._keeper.remove(number)
        except IndexError as error:
            print(error)
            return
        print("Session removed from storage.")

    async def list(self) -> None:
        table = [
            (number, session.id, session.phone, session.mention)
            for number, session in enumerate(await self._keeper.list())
        ]
        print(
            tabulate.tabulate(
                table,
                headers=("№", "Telegram ID", "Phone", "Mention"),
                tablefmt="pretty",
            )
        )

    async def get(self, command: str) -> None:
        number = self._get_session_number(command)
        if number is None:
            return

        try:
            message = await self._keeper.get(number)
        except IndexError as error:
            print(error)
            return
        print(
            tabulate.tabulate(
                (
                    (message.message,),
                    (message.date.strftime("%H:%M %d.%m.%Y UTC"),),
                ),
                headers=("Last message from Telegram",),
                tablefmt="grid",
            )
        )

    async def setup_storage(self) -> None:
        api_id = None
        while not api_id:
            try:
                api_id = int(input("Please enter api id: "))
            except ValueError:
                print("You entered an invalid value.")
        api_hash = getpass.getpass("Please enter api hash: ")
        await self._keeper.setup_storage(api_id, api_hash)

    async def process_command(self) -> None:
        command = input("> ")

        if command == "exit":
            sys.exit()
        if command == "help":
            self._print_help()
            return
        if command == "add":
            await self.add()
            return
        if command.startswith("remove"):
            await self.remove(command)
            return
        if command == "list":
            await self.list()
            return
        if command.startswith("get"):
            await self.get(command)
            return

        print("Incorrect command. Enter help to see the list of commands.")

    async def run(self) -> None:
        try:
            await self._keeper.start()
        except storage.StorageNotFound:
            await self.setup_storage()
        except (storage.InvalidPassword, storage.MismatchedVersionError) as error:
            print(error)
            return

        self._print_help()

        try:
            while True:
                await self.process_command()
        except (SystemExit, KeyboardInterrupt):
            await self._keeper.stop()
        except Exception as error:  # pylint: disable=W0703
            print(error)


if __name__ == "__main__":
    run()
