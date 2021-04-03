import base64 as b64
import json
from typing import List, Union

from .session import KeeperSession, Session


FILENAME = 'sessions.tgsk'
CURRENT_VERSION = b'1'
PASS_HASH_SALT = b''
PASS_HASH_ITERATES = 8


# TODO: add abstract storage
# TODO: add exceptions processing


class EncryptedJsonStorage:
    def __init__(self, password: Union[bytes, str], *,
                 filename: str = FILENAME,
                 version: Union[bytes, int] = CURRENT_VERSION):
        self.filename = filename
        self._version = bytes(version)
        self._set_fernet(password)
        self._api_id = None
        self._api_hash = None
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

    @api_id.setter
    def api_id(self, value: int):
        self._api_id = value

    @property
    def api_hash(self) -> str:
        return self._api_hash

    @api_hash.setter
    def api_hash(self, value: str):
        self._api_hash = value

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
            raise StorageSettedError('Storage already has been setted.')
        self.api_id = api_id
        self.api_hash = api_hash
        await self.save()

    async def start(self):
        with open(self.filename, 'rb') as file:
            data = file.read()
            version, data = data[:1], data[1:]
            if version != self._version:
                raise MismatchedVersionError('The version of the file '
                                             'doesn\'t match the version of '
                                             'the storage.')
            await self._decrypt_sessions(data)

    async def save(self) -> None:
        with open(self.filename, 'wb') as file:
            file.write(self._version + self._encrypt_sessions())
            file.flush()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.save()
        return self


class StorageSettedError(Exception):
    pass


class MismatchedVersionError(Exception):
    pass
