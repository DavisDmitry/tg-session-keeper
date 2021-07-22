from typing import List

from ..session import Session
from . import exceptions as exc
from .abstract import AbstractStorage


class MemoryStorage(AbstractStorage):
    def __init__(self):
        super().__init__()
        self._sessions = []

    @property
    def api_id(self) -> int:
        return self._api_id

    @property
    def api_hash(self) -> str:
        return self._api_hash

    async def add_session(self, session: Session) -> None:
        self._sessions.append(session)

    async def remove_session(self, number: int) -> None:
        return self._sessions.pop(number)

    @property
    def sessions(self) -> List[Session]:
        return self._sessions

    async def setup(self, api_id: int, api_hash: str) -> None:
        if self._api_id and self._api_hash:
            raise exc.StorageSettedError("Storage already has been setted.")
        self._api_id = api_id
        self._api_hash = api_hash

    async def start(self) -> None:
        pass

    async def save(self) -> None:
        pass

    async def stop(self) -> None:
        pass
