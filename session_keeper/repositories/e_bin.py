import asyncio
import base64
import io
import pathlib
import struct
from typing import ClassVar, Dict, Iterator, List, Optional, Sequence, Type, Union

from cryptography import fernet as _fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import pbkdf2
from pyrogram import storage as pyro_storage

from session_keeper import storage as _storage
from session_keeper.repositories import abc, errors


class EncryptedBinaryRepository(abc.Repository):
    REPOSITORY_VERSION: ClassVar[bytes] = b"binary1"
    _API_DATA_FORMAT: ClassVar[str] = ">I32s?"

    _storages: Dict[int, _storage.KeeperStorage]

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        file_path: Union[str, pathlib.Path],
        password_or_fernet: Union[bytes, str, _fernet.Fernet],
        *,
        test_mode: bool = False,
        pass_hash_salt: bytes = b"TGSK",
        pass_hash_iterations: int = 8,
    ):
        self._api_id, self._api_hash = api_id, api_hash
        self._file_path = file_path
        if isinstance(password_or_fernet, _fernet.Fernet):
            self._fernet = password_or_fernet
        else:
            self._fernet = self._create_fernet(
                password_or_fernet, pass_hash_salt, pass_hash_iterations
            )
        self._test_mode = test_mode
        self._storages = {}

    @classmethod
    async def from_file(
        cls: Type["EncryptedBinaryRepository"],
        file_path: Union[str, pathlib.Path],
        password: Union[bytes, str],
        *,
        pass_hash_salt: bytes = b"TGSK",
        pass_hash_iterations: int = 8,
    ) -> "EncryptedBinaryRepository":
        """Creates repository instance from file.

        Raises:
            InvalidRepositoryVersionError: If file with invalid repository version is
                loaded.
            WrongPasswordError: If wrong password was passed.
        """
        with open(file_path, "rb") as file:
            version, data = file.read().split(b"\n", 1)

        if version != cls.REPOSITORY_VERSION:
            raise errors.InvalidRepositoryVersionError

        fernet = cls._create_fernet(password, pass_hash_salt, pass_hash_iterations)
        try:
            data = fernet.decrypt(data)
        except _fernet.InvalidToken as error:
            raise errors.WrongPasswordError from error

        api_data, data = data.split(b"\n", 1)
        api_hash: bytes
        api_id, api_hash, test_mode = struct.unpack(cls._API_DATA_FORMAT, api_data)

        repo = cls(api_id, api_hash.decode(), file_path, fernet, test_mode=test_mode)
        await asyncio.gather(
            *(
                repo.add_storage_from_string(_data)
                for _data in cls._split_storages_data(data)
            )
        )

        return repo

    @staticmethod
    def _split_storages_data(data: bytes) -> List[bytes]:
        length = struct.calcsize(_storage.KeeperStorage.SESSION_STRING_FORMAT)
        storages_io = io.BytesIO(data)
        result: List[bytes] = []
        storage_data = storages_io.read(length)
        while storage_data != b"":
            result.append(storage_data)
            storage_data = storages_io.read(length)
        return result

    @property
    def file_path(self) -> str:
        return str(self._file_path)

    @classmethod
    def _create_fernet(
        cls, password: Union[bytes, str], hash_salt: bytes, hash_iterations: int
    ) -> _fernet.Fernet:
        return _fernet.Fernet(
            cls._create_encryption_key(password, hash_salt, hash_iterations)
        )

    @staticmethod
    def _create_encryption_key(
        password: Union[bytes, str], hash_salt: bytes, hash_iterations: int
    ) -> bytes:
        password = password.encode() if isinstance(password, str) else password
        kdf = pbkdf2.PBKDF2HMAC(hashes.SHA256(), 32, hash_salt, hash_iterations)
        return base64.urlsafe_b64encode(kdf.derive(password))

    async def add_storage_from_string(self, data: bytes) -> None:
        """Adds storage from string."""
        storage = _storage.KeeperStorage(data, self._test_mode)
        await storage.open()
        await self.add(storage)

    async def add(self, storage: pyro_storage.Storage) -> None:
        user_id = await storage.user_id()
        if self._storages.get(user_id) is not None:
            raise errors.StorageAlreadyInRepositoryError
        dc_id, auth_key = await asyncio.gather(storage.dc_id(), storage.auth_key())
        data = struct.pack(
            _storage.KeeperStorage.SESSION_STRING_FORMAT, dc_id, auth_key, user_id
        )
        new_storage = self._storages[user_id] = _storage.KeeperStorage(
            data, self._test_mode
        )
        await new_storage.open()

    async def remove(self, user_id: int) -> None:
        try:
            del self._storages[user_id]
        except KeyError as error:
            raise errors.StorageDoesNotExistInRepositoryError from error

    async def get_many(
        self, *, offset: int = 0, limit: int = 20
    ) -> Sequence[pyro_storage.Storage]:
        return tuple(self._storages.values())[offset : offset + limit]

    async def iter(self) -> Iterator[pyro_storage.Storage]:
        return (storage for storage in self._storages.values())

    async def get_or_none(self, user_id: int) -> Optional[pyro_storage.Storage]:
        return self._storages.get(user_id)

    async def get(self, user_id: int) -> pyro_storage.Storage:
        try:
            return self._storages[user_id]
        except KeyError as error:
            raise errors.StorageDoesNotExistInRepositoryError from error

    async def save(self) -> None:
        api_data = struct.pack(
            self._API_DATA_FORMAT,
            self._api_id,
            self._api_hash.encode(),
            self._test_mode,
        )
        storages = await asyncio.gather(
            *(storage.export_session_string() for storage in self._storages.values())
        )
        data = b"".join(storages)
        data = b"\n".join((api_data, data))
        data = self._fernet.encrypt(data)
        data = b"\n".join((self.REPOSITORY_VERSION, data))
        with open(self._file_path, "wb") as file:
            file.write(data)
            file.flush()
