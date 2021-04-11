import base64 as b64
import json
import os
from typing import List, Union

from . import exceptions as exc
from .abstract import AbstractStorage
from ..session import KeeperSession, Session


FILENAME = 'sessions.tgsk'
CURRENT_VERSION = b'1'
PASS_HASH_SALT = b''
PASS_HASH_ITERATES = 8


__all__ = ('FILENAME', 'CURRENT_VERSION',
           'PASS_HASH_SALT', 'PASS_HASH_ITERATES',
           'EncryptedJsonStorage')


class EncryptedJsonStorage(AbstractStorage):
    """
    TODO: docs
    """
    def __init__(self, password: Union[bytes, str], *,
                 filename: str = FILENAME,
                 version: Union[bytes, int] = CURRENT_VERSION):
        super().__init__()
        self._filename = filename
        self._version = bytes(version)
        self._set_fernet(password)
        self._sessions = []

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
            self, password: Union[bytes, str],
            hash_salt: bytes = PASS_HASH_SALT,
            hash_iterates: int = PASS_HASH_ITERATES
    ) -> None:
        from cryptography.fernet import Fernet

        if isinstance(password, str):
            password = self.transform_password(password, hash_salt,
                                               hash_iterates)
        self._fernet = Fernet(password)

    @property
    def api_id(self) -> int:
        return self._api_id

    @property
    def api_hash(self) -> str:
        return self._api_hash

    async def add_session(self, session: Session) -> None:
        self._sessions.append(session)

    async def remove_session(self, number: int) -> None:
        self._sessions.pop(number)

    @property
    def sessions(self) -> List[Session]:
        return self._sessions

    def _as_dict(self) -> dict:
        sessions = []
        for session in self.sessions:
            sessions.append(session.as_dict())
        return {'api_id': self._api_id,
                'api_hash': self._api_hash,
                'sessions': sessions}

    def _as_json(self) -> str:
        return json.dumps(self._as_dict())

    async def _from_json(self, data: str) -> None:
        data = json.loads(data)
        self._api_id = data['api_id']
        self._api_hash = data['api_hash']
        for session in data.get('sessions'):
            await self.add_session(KeeperSession(**session))

    def _encrypt_sessions(self) -> bytes:
        data = self._as_json().encode()
        data = b64.urlsafe_b64encode(data)
        return self._fernet.encrypt(data)

    async def _decrypt_sessions(self, data: bytes) -> None:
        data = self._fernet.decrypt(data)
        data = b64.urlsafe_b64decode(data)
        await self._from_json(data.decode())

    async def setup(self, api_id: int, api_hash: str) -> None:
        if self._api_id and self._api_hash:
            raise exc.StorageSettedError('Storage already has been setted.')
        self._api_id = api_id
        self._api_hash = api_hash
        await self.save()

    async def start(self) -> None:
        # TODO: invalid password exception
        if not os.path.isfile(self._filename):
            raise exc.StorageNotFoundError(self._filename)
        with open(self._filename, 'rb') as file:
            data = file.read()
            version, data = data[:1], data[1:]
            if version != self._version:
                raise exc.MismatchedVersionError('The version of the file '
                                                 'does not match the version '
                                                 'of the storage.')
            await self._decrypt_sessions(data)
        self._started = True

    async def save(self) -> None:
        with open(self._filename, 'wb') as file:
            file.write(self._version + self._encrypt_sessions())
            file.flush()

    async def stop(self) -> None:
        await self.save()
        self._started = False
