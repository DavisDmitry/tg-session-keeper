from abc import ABC, abstractmethod
from typing import List, Optional

from telethon import TelegramClient
from telethon.tl.types import Message

from ..session import Session
from ..storage import AbstractStorage, EncryptedJsonStorage, StorageNotFound


class BaseKeeper(ABC):
    _storage: AbstractStorage
    _clients: List[TelegramClient]
    _test_mode: bool

    def __init__(self):
        self._clients = []
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    @property
    def test_mode(self) -> bool:
        return self._test_mode

    # TODO: implement this method with custom login instead telethon start
    @abstractmethod
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

    @abstractmethod
    async def setup_storage(self) -> None:
        pass

    async def start(
        self,
        password: str,
        *,
        test_mode: bool = False,
        filename: Optional[str] = None,
    ) -> None:
        self._test_mode = test_mode
        kwargs = {"password": password}
        if filename:
            kwargs.update({"filename": filename})
        storage = None
        while not storage:
            self._storage = storage = EncryptedJsonStorage(**kwargs)
            try:
                await storage.start()
            except StorageNotFound:
                await self.setup_storage()
                storage = None

        for session in storage.sessions:
            client = TelegramClient(session, storage.api_id, storage.api_hash)
            await client.start()
            self._clients.append(client)

        self._storage = storage
        self._started = True

    async def stop(self) -> None:
        for client in self._clients:
            await client.disconnect()
        await self._storage.stop()
        self._started = False

    @classmethod
    @abstractmethod
    def run(cls) -> None:
        pass
