import os
import sys
import traceback
from argparse import ArgumentParser, Namespace
from typing import List, Optional

from tabulate import tabulate
from telethon import TelegramClient
from telethon.tl.types import Message

from .session import Session
from .storage import EncryptedJsonStorage


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('--filename',
                        type=Optional[str], required=False,
                        help='path to a sessions file')
    return parser.parse_args()


def print_help() -> None:
    print('COMMANDS:\n'
          'add <PHONE>\t\tadd telegram session\n'
          'remove <NUMBER>\t\tremove session\n'
          'list\t\t\tsessions list\n'
          'get <NUMBER>\t\tget last message from Telegram for session\n'
          'exit\t\t\texit from program')


async def process_add(
        command: str,
        storage: EncryptedJsonStorage,
        clients: List[TelegramClient]
) -> None:
    params = command.split(' ')
    if len(params) == 2:
        phone = params[1]
    elif len(params) == 1:
        phone = None
    else:
        print('You entered the command incorrectly. Enter help to find out '
              'the correct option.')
        return

    client = TelegramClient(Session(), storage.api_id, storage.api_hash)
    if phone:
        await client.start(lambda: phone)
    else:
        await client.start()

    await storage.add_session(client.session)
    clients.append(client)
    print('Session added to storage.')


async def process_remove(
        command: str,
        storage: EncryptedJsonStorage,
        clients: List[TelegramClient]
) -> None:
    params = command.split(' ')
    if len(params) == 2:
        number = int(params[1])
    elif len(params) == 1:
        print('Please enter the session number (you can see it by the list '
              'command):')
        number = int(input())
    else:
        print('You entered the command incorrectly. Enter help to find out '
              'the correct option.')
        return

    client = clients.pop(number)
    await storage.remove_session(number)
    await client.log_out()

    print('Session removed from storage.')


async def process_list(storage: EncryptedJsonStorage) -> None:
    table = []
    for number, session in enumerate(storage.sessions):
        table.append((number, session.id, session.phone, session.mention))

    print(tabulate(table,
                   headers=('№', 'Telegram ID', 'Phone', 'Mention'),
                   tablefmt='pretty'))


async def process_get(
        command: str,
        clients: List[TelegramClient]
) -> None:
    params = command.split(' ')
    if len(params) == 2:
        number = int(params[1])
    elif len(params) == 1:
        print('Please enter the session number (you can see it by the list '
              'command):')
        number = int(input())
    else:
        print('You entered the command incorrectly. Enter help to find out '
              'the correct option.')
        return

    client = clients[number]
    messages = await client.get_messages(777000)
    message: Message = messages[0]
    print(tabulate(
        ((message.message,), (message.date.strftime('%H:%M %d.%m.%Y UTC'),)),
        headers=('Last message from Telegram',),
        tablefmt='grid'
    ))


async def process_command(
        command: str,
        storage: EncryptedJsonStorage,
        clients: List[TelegramClient]
) -> None:
    if command == 'exit':
        for client in clients:
            await client.disconnect()
        sys.exit()

    if command == 'help':
        print_help()
        return

    if command.startswith('add'):
        await process_add(command, storage, clients)
        return

    if command.startswith('remove'):
        await process_remove(command, storage, clients)
        return

    if command == 'list':
        await process_list(storage)
        return

    if command.startswith('get'):
        await process_get(command, clients)
        return

    print('Incorrect command. Enter help to see the list of commands.')


async def main() -> None:
    args = parse_args()
    kwargs = {}
    if args.filename:
        kwargs.update({'filename': args.filename})
    print('Please enter a password to access sessions:')
    kwargs.update({'password': input()})
    storage = EncryptedJsonStorage(**kwargs)
    if not os.path.isfile(storage.filename):
        print('Please enter api id:')
        api_id = int(input())
        print('Please enter api hash:')
        api_hash = input()
        await storage.setup(api_id, api_hash)
    print_help()
    async with storage:
        try:
            clients = []
            for session in storage.sessions:
                client = TelegramClient(
                    session, storage.api_id, storage.api_hash
                )
                await client.start()
                clients.append(client)
            while True:
                await process_command(input(), storage, clients)
        except SystemExit:
            pass
        except Exception:
            traceback.print_exc()
