import asyncio
import getpass
import sys
from argparse import ArgumentParser, Namespace
from typing import Optional

from tabulate import tabulate
from telethon import TelegramClient

from .base import BaseKeeper
from ..session import Session
from ..storage import InvalidPassword, MismatchedVersionError
from ..version import __version__ as keeper_version


__all__ = ('CLIKeeper',)


class CLIKeeper(BaseKeeper):
    """
    TODO: docs
    """
    @staticmethod
    def _answer_password() -> str:
        return getpass.getpass('Please enter a password to access sessions: ')

    @staticmethod
    def _parse_args() -> Namespace:
        parser = ArgumentParser()
        parser.add_argument('--filename',
                            type=Optional[str], required=False,
                            help='path to a sessions file')
        parser.add_argument('--test',
                            action='store_true',
                            help='run keeper on test Telegram server')
        return parser.parse_args()

    @staticmethod
    def _print_help() -> None:
        print('COMMANDS:\n'
              'add\t\t\tadd telegram session\n'
              'remove <NUMBER>\t\tremove session\n'
              'list\t\t\tsessions list\n'
              'get <NUMBER>\t\tget last message from Telegram for session\n'
              'exit\t\t\texit from program')

    @staticmethod
    def _print_incorrect_command() -> None:
        print('You entered the command incorrectly. Enter help to find out '
              'the correct option.')

    @staticmethod
    def _print_non_existent_session() -> None:
        print('There is no session with this number or messages from Telegram '
              'are missing.')

    @classmethod
    def _get_session_number(cls, command: str) -> Optional[int]:
        number = None
        params = command.split(' ')
        if len(params) == 2:
            number = params[1]
        if len(params) > 2:
            cls._print_incorrect_command()
            return

        while True:
            if number is None:
                number = input('Please enter the session number (you can see '
                               'it by the list command): ')
            try:
                return int(number)
            except ValueError:
                number = None

    async def add(self) -> None:
        client = TelegramClient(
            Session(), self._storage.api_id, self._storage.api_hash,
            app_version=f'Session Keeper {keeper_version}'
        )
        if self.test_mode:
            client.session.set_dc(2, '149.154.167.40', 443)
        await client.start()

        await self._storage.add_session(client.session)
        self._clients.append(client)
        print('Session added to storage.')

    async def remove(self, command: str) -> None:
        number = self._get_session_number(command)
        if number is None:
            return
        try:
            await super().remove(number)
        except IndexError:
            self._print_non_existent_session()
            return
        print('Session removed from storage.')

    async def list(self) -> None:
        table = [(number, session.id, session.phone, session.mention)
                 for number, session in enumerate(await super().list())]
        print(tabulate(table,
                       headers=('№', 'Telegram ID', 'Phone', 'Mention'),
                       tablefmt='pretty'))

    async def get(self, command: str) -> None:
        number = self._get_session_number(command)
        if number is None:
            return

        try:
            message = await super().get(number)
        except IndexError:
            self._print_non_existent_session()
            return
        print(tabulate(((message.message,),
                        (message.date.strftime('%H:%M %d.%m.%Y UTC'),)),
                       headers=('Last message from Telegram',),
                       tablefmt='grid'))

    async def setup_storage(self) -> None:
        api_id = None
        while not api_id:
            api_id = input('Please enter api id: ')
            try:
                api_id = int(api_id)
            except ValueError:
                print('You entered an invalid value.')
        api_hash = getpass.getpass('Please enter api hash: ')
        await self._storage.setup(api_id, api_hash)

    async def start(self) -> None:
        args = self._parse_args()
        password = self._answer_password()
        await super().start(
            password, test_mode=args.test, filename=args.filename
        )

    async def process_command(self) -> None:
        command = input('> ')

        if command == 'exit':
            sys.exit()
        if command == 'help':
            self._print_help()
            return
        if command == 'add':
            await self.add()
            return
        if command.startswith('remove'):
            await self.remove(command)
            return
        if command == 'list':
            await self.list()
            return
        if command.startswith('get'):
            await self.get(command)
            return

        print('Incorrect command. Enter help to see the list of commands.')

    async def _run(self) -> None:
        try:
            await self.start()
        except MismatchedVersionError as e:
            print(e)
            return
        except InvalidPassword:
            print('Invalid password')

        self._print_help()

        try:
            while True:
                await self.process_command()
        except (SystemExit, KeyboardInterrupt):
            await self.stop()
        except Exception as e:
            print(e)

    @classmethod
    def run(cls) -> None:
        # TODO: maybe change args parsing (after gui added)
        asyncio.run(cls()._run())


if __name__ == '__main__':
    CLIKeeper.run()
