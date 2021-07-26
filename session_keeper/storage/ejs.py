import base64 as b64
import json
import os
from typing import Optional, Union

from ..session import KeeperSession
from . import exceptions as exc
from .memory import MemoryStorage

CURRENT_VERSION = b"1"
PASS_HASH_SALT = b""
PASS_HASH_ITERATES = 8


class MemoryEncryptedJsonStorage(MemoryStorage):
    def __init__(
        self, password: Union[bytes, str], *, unencrytped_data: Optional[bytes] = None
    ):
        super().__init__()
        self._set_fernet(password)
        self._unencrypted_data = unencrytped_data
        self._encrypted_data = None

    @property
    def encrypted_data(self) -> bytes:
        self._save()
        return self._encrypted_data

    @staticmethod
    def transform_password(
        password: str, hash_salt: bytes, hash_iterates: int
    ) -> bytes:
        password = password.encode()

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        kdf = PBKDF2HMAC(hashes.SHA256(), 32, hash_salt, hash_iterates)
        return b64.urlsafe_b64encode(kdf.derive(password))

    def _set_fernet(
        self,
        password: Union[bytes, str],
        hash_salt: bytes = PASS_HASH_SALT,
        hash_iterates: int = PASS_HASH_ITERATES,
    ) -> None:
        from cryptography.fernet import Fernet

        if isinstance(password, str):
            password = self.transform_password(password, hash_salt, hash_iterates)
        self._fernet = Fernet(password)

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
        data = json.loads(data)
        self._api_id = data["api_id"]
        self._api_hash = data["api_hash"]
        for session in data.get("sessions"):
            await self.add_session(KeeperSession(**session))

    def _encrypt_sessions(self) -> bytes:
        data = self._as_json().encode()
        data = b64.urlsafe_b64encode(data)
        return self._fernet.encrypt(data)

    async def _decrypt_sessions(self, data: bytes) -> None:
        from cryptography.fernet import InvalidToken

        try:
            data = self._fernet.decrypt(data)
        except InvalidToken:
            raise exc.InvalidPassword("You entered an invalid password.")

        data = b64.urlsafe_b64decode(data)
        await self._from_json(data.decode())

    def _save(self) -> None:
        self._encrypted_data = CURRENT_VERSION + self._encrypt_sessions()

    async def setup(self, api_id: int, api_hash: str) -> None:
        await super().setup(api_id, api_hash)
        await self.save()

    async def start(self) -> None:
        data = self._unencrypted_data
        if data:
            version, data = data[:1], data[1:]
            if version != CURRENT_VERSION:
                raise exc.MismatchedVersionError(
                    "The version of the file does not match the version of the storage."
                )
            await self._decrypt_sessions(data)

    async def save(self) -> None:
        self._save()


class FileEncryptedJsonStorage(MemoryEncryptedJsonStorage):
    def __init__(self, password: Union[bytes, str], filename: str):
        super().__init__(password)
        self._filename = filename

    @property
    def filename(self) -> str:
        return self._filename

    async def start(self):
        if not os.path.isfile(self.filename):
            raise exc.StorageNotFound(f"File {self.filename} does not exist.")
        with open(self.filename, "rb") as file:
            data = self._unencrypted_data = file.read()
            if not data:
                raise exc.StorageNotFound(f"File {self.filename} is empty.")
            await (super()).start()

    async def save(self) -> None:
        self._save()
        with open(self.filename, "wb") as file:
            file.write(self.encrypted_data)
            file.flush()

    async def stop(self) -> None:
        await self.save()
