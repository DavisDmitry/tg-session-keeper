import abc
from typing import ClassVar, Iterator, Optional, Sequence

from pyrogram import storage as _storage


class Repository(abc.ABC):
    REPOSITORY_VERSION: ClassVar[bytes]

    _api_id: int
    _api_hash: str
    _test_mode: bool

    @property
    def api_id(self) -> int:
        """Telegram app ID.

        https://core.telegram.org/api/obtaining_api_id
        """
        return self._api_id

    @property
    def api_hash(self) -> str:
        """Telegram app hash.

        https://core.telegram.org/api/obtaining_api_id
        """
        return self._api_hash

    @property
    def test_mode(self) -> bool:
        """Should clients connect to Telegram test servers."""
        return self._test_mode

    @abc.abstractmethod
    async def add(self, storage: _storage.Storage) -> None:
        """Adds a storage to repository.

        Raises:
            StorageAlreadyInRepositoryError: If storage already added to this
                repository.
        """

    @abc.abstractmethod
    async def remove(self, user_id: int) -> None:
        """Removes a storage by user ID.

        Raises:
            StorageDoesNotExistInRepositoryError: If repository doesn't contain a
                storage with this `user_id`.
        """

    @abc.abstractmethod
    async def get_many(
        self, *, offset: int = 0, limit: int = 20
    ) -> Sequence[_storage.Storage]:
        """Gets many storages."""

    @abc.abstractmethod
    async def iter(self) -> Iterator[_storage.Storage]:
        """Iters storages."""

    @abc.abstractmethod
    async def get_or_none(self, user_id: int) -> Optional[_storage.Storage]:
        """Gets a storage by user ID, if it exists."""

    @abc.abstractmethod
    async def get(self, user_id: int) -> _storage.Storage:
        """
        Gets a storage by user ID.

        Raises:
            StorageDoesNotExistInRepositoryError: If repository doesn't contain a
                storage with this `user_id`.
        """

    @abc.abstractmethod
    async def save(self) -> None:
        """Force saves repository."""
