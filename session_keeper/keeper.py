from typing import List

from telethon import TelegramClient
from telethon.tl.types import Message

from .session import Session
from .storage import AbstractStorage, EncryptedJsonStorage


class Keeper:
    _clients: List[TelegramClient]

    def __init__(
        self, password: str, *, filename: str = "sessions.tgsk", test_mode: bool = False
    ):
        self._storage = EncryptedJsonStorage(password, filename=filename)
        self._test_mode = test_mode
        self._clients = []
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    @property
    def test_mode(self) -> bool:
        return self._test_mode

    # TODO: implement this method with custom login instead telethon start
    async def add(self) -> None:
        pass

    async def remove(self, number: int) -> None:
        client = self._clients.pop(number)
        await self._storage.remove_session(number)
        await client.log_out()

    async def list(self) -> List[Session]:
        return self._storage.sessions

    async def get(self, number: int) -> Message:
        client = self._clients[number]
        return (await client.get_messages(777000))[0]

    async def setup_storage(self, api_id: int, api_hash: str) -> None:
        await self._storage.setup(api_id, api_hash)

    async def start(self) -> None:
        storage = self._storage

        await storage.start()

        for session in storage.sessions:
            client = TelegramClient(session, storage.api_id, storage.api_hash)
            await client.start()
            self._clients.append(client)

        self._started = True

    async def stop(self) -> None:
        for client in self._clients:
            await client.disconnect()
        await self._storage.stop()
        self._started = False
