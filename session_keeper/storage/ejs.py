import base64 as b64
import json
import os
from typing import Union

from cryptography import fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import pbkdf2

from session_keeper import session as _session
from session_keeper.storage import exceptions as exc
from session_keeper.storage import memory

CURRENT_VERSION = b"1"
PASS_HASH_SALT = b""
PASS_HASH_ITERATES = 8


class EncryptedJsonStorage(memory.MemoryStorage):
    def __init__(
        self,
        password: Union[bytes, str],
        filename: str,
        *,
        version: Union[bytes, int] = CURRENT_VERSION,
    ):
        super().__init__()
        self._filename = filename
        self._version = bytes(version)
        self._set_fernet(password)

    @staticmethod
    def transform_password(
        password: str, hash_salt: bytes, hash_iterates: int
    ) -> bytes:
        kdf = pbkdf2.PBKDF2HMAC(hashes.SHA256(), 32, hash_salt, hash_iterates)
        return b64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _set_fernet(
        self,
        password: Union[bytes, str],
        hash_salt: bytes = PASS_HASH_SALT,
        hash_iterates: int = PASS_HASH_ITERATES,
    ) -> None:
        if isinstance(password, str):
            password = self.transform_password(password, hash_salt, hash_iterates)
        self._fernet = fernet.Fernet(password)

    @property
    def filename(self) -> str:
        return self._filename

    def _as_dict(self) -> dict:
        sessions = []
        for session in self.sessions:
            sessions.append(session.as_dict())
        return {
            "api_id": self._api_id,
            "api_hash": self._api_hash,
            "sessions": sessions,
        }

    def _as_json(self) -> str:
        return json.dumps(self._as_dict())

    async def _from_json(self, data: str) -> None:
        data_dct = json.loads(data)
        self._api_id = data_dct["api_id"]
        self._api_hash = data_dct["api_hash"]
        for session in data_dct.get("sessions"):
            await self.add_session(_session.KeeperSession(**session))

    def _encrypt_sessions(self) -> bytes:
        data = self._as_json().encode()
        data = b64.urlsafe_b64encode(data)
        return self._fernet.encrypt(data)

    async def _decrypt_sessions(self, data: bytes) -> None:
        try:
            data = self._fernet.decrypt(data)
        except fernet.InvalidToken as error:
            raise exc.InvalidPassword("You entered an invalid password.") from error

        data = b64.urlsafe_b64decode(data)
        await self._from_json(data.decode())

    async def setup(self, api_id: int, api_hash: str) -> None:
        await super().setup(api_id, api_hash)
        await self.save()

    async def start(self):
        if not os.path.isfile(self.filename):
            raise exc.StorageNotFound(f"File {self.filename} does not exist.")
        with open(self.filename, "rb") as file:
            data = file.read()
            version, data = data[:1], data[1:]
            if not data:
                raise exc.StorageNotFound(f"File {self.filename} is empty.")
            if version != self._version:
                raise exc.MismatchedVersionError(
                    "The version of the file does not match the version of the storage."
                )
            await self._decrypt_sessions(data)

    async def save(self) -> None:
        with open(self.filename, "wb") as file:
            file.write(self._version + self._encrypt_sessions())
            file.flush()

    async def stop(self) -> None:
        await self.save()
