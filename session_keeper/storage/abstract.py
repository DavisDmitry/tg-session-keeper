from abc import ABC, abstractmethod
from typing import List

from ..session import Session


__all__ = ('AbstractStorage',)


class AbstractStorage(ABC):
    def __init__(self):
        self._api_id = None
        self._api_hash = None
        self._started = False

    @property
    @abstractmethod
    def api_id(self) -> int:
        pass

    @property
    @abstractmethod
    def api_hash(self) -> str:
        pass

    @property
    def started(self) -> bool:
        return self._started

    @abstractmethod
    async def add_session(self, session: Session) -> None:
        pass

    @abstractmethod
    async def remove_session(self, number: int) -> None:
        pass

    @property
    @abstractmethod
    def sessions(self) -> List[Session]:
        pass

    @abstractmethod
    async def setup(self, api_id: int, api_hash: str) -> None:
        pass

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def save(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    async def __aenter__(self) -> 'AbstractStorage':
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
