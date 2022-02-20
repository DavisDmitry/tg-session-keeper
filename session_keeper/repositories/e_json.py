import asyncio
import base64 as b64
import json
import struct
from typing import ClassVar, Iterator, List, Optional, Sequence, Type, Union

from cryptography import fernet as _fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import pbkdf2
from pyrogram import storage as _storage
from pyrogram import utils

from session_keeper.repositories import abc, errors

PASS_HASH_SALT = b""
PASS_HASH_ITERATES = 8


class EncryptedJsonRepository(abc.Repository):
    REPOSITORY_VERSION: ClassVar[bytes] = b"1"

    _storages: List[_storage.Storage]

    def __init__(
        self, api_id: int, api_hash: str, filename: str, *, test_mode: bool = False
    ):
        self._api_id, self._api_hash = api_id, api_hash
        self._filename = filename
        self._test_mode = test_mode
        self._storages = []

    @property
    def filename(self) -> str:
        return self._filename

    @classmethod
    async def from_file(
        cls: Type["EncryptedJsonRepository"], password: Union[bytes, str], filename: str
    ) -> "EncryptedJsonRepository":
        """Creates repository instance from file.

        Raises:
            InvalidRepositoryVersionError: If file with invalid repository version is
                loaded.
            WrongPasswordError: If wrong password was passed.
        """
        with open(filename, "rb") as file:
            data = file.read()
        version, encrypted_data = data[:1], data[1:]
        if version != cls.REPOSITORY_VERSION:
            raise errors.InvalidRepositoryVersionError
        try:
            data = cls._decrypt(encrypted_data, password)
        except _fernet.InvalidToken as error:
            raise errors.WrongPasswordError from error
        data_dct: dict = json.loads(data)
        repo = cls(data_dct["api_id"], data_dct["api_hash"], filename)
        sessions: Optional[List[dict]] = data_dct.get("sessions")
        if sessions is not None:
            await asyncio.gather(
                *(repo._convert_session_to_storage(session) for session in sessions)
            )
        return repo

    @classmethod
    def _decrypt(cls, data: bytes, password: Union[bytes, str]) -> bytes:
        if isinstance(password, str):
            password = cls._transform_password(
                password, PASS_HASH_SALT, PASS_HASH_ITERATES
            )
        fernet = _fernet.Fernet(password)
        data = fernet.decrypt(data)
        return b64.urlsafe_b64decode(data)

    @staticmethod
    def _transform_password(
        password: str, hash_salt: bytes, hash_iterates: int
    ) -> bytes:
        kdf = pbkdf2.PBKDF2HMAC(hashes.SHA256(), 32, hash_salt, hash_iterates)
        return b64.urlsafe_b64encode(kdf.derive(password.encode()))

    async def _convert_session_to_storage(self, session: dict) -> None:
        user_id = session["id"]
        str_format = (
            _storage.Storage.SESSION_STRING_FORMAT
            if user_id < utils.MAX_USER_ID_OLD
            else _storage.MemoryStorage.SESSION_STRING_FORMAT_64
        )
        storage_str = struct.pack(
            str_format,
            session["dc_id"],
            False,
            b64.urlsafe_b64decode(session["auth_key"]),
            user_id,
            False,
        )
        storage = _storage.MemoryStorage(
            b64.urlsafe_b64encode(storage_str).decode().rstrip("=")
        )
        await storage.open()
        await self.add(storage)

    async def add(self, storage: _storage.Storage) -> None:
        self._storages.append(storage)

    async def remove(self, user_id: int) -> None:
        raise NotImplementedError(
            "JSON storage is no longer supported. "
            "You can only load the old one to convert it to the new one."
        )

    async def get_many(
        self, *, offset: int = 0, limit: int = 20
    ) -> Sequence[_storage.Storage]:
        return self._storages[offset : offset + limit]

    async def iter(self) -> Iterator[_storage.Storage]:
        return (storage for storage in self._storages)

    async def get_or_none(self, user_id: int) -> Optional[_storage.Storage]:
        raise NotImplementedError(
            "JSON storage is no longer supported. "
            "You can only load the old one to convert it to the new one."
        )

    async def get(self, user_id: int) -> _storage.Storage:
        raise NotImplementedError(
            "JSON storage is no longer supported. "
            "You can only load the old one to convert it to the new one."
        )

    async def save(self) -> None:
        raise NotImplementedError(
            "JSON storage is no longer supported. "
            "You can only load the old one to convert it to the new one."
        )
