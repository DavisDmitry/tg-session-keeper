import base64 as b64

from telethon.sessions import MemorySession


class Session(MemorySession):
    @property
    def entities(self) -> tuple:
        return list(self._entities)[0]

    @property
    def id(self) -> int:
        return self.entities[0]

    @property
    def phone(self) -> str:
        return '+' + self.entities[3]

    @property
    def mention(self) -> str:
        if self.entities[2]:
            return '@' + self.entities[2]
        return self.entities[4]

    def _encode_auth_key(self) -> str:
        key = self.auth_key.key
        key = b64.urlsafe_b64encode(key)
        return key.decode()

    def as_dict(self) -> dict:
        return {'id': self.id, 'phone': self.phone, 'mention': self.mention,
                'dc_id': self.dc_id, 'server_address': self.server_address,
                'port': self.port, 'auth_key': self._encode_auth_key()}


class KeeperSession(Session):
    def __init__(self, **kwargs):
        from telethon.crypto import AuthKey

        super().__init__()

        self._dc_id, self._server_address, self._port, auth_key = [
            kwargs.get(key) for key in ('dc_id', 'server_address', 'port',
                                        'auth_key')
        ]
        self._auth_key = AuthKey(self._decode_auth_key(auth_key))

    @staticmethod
    def _decode_auth_key(encoded_key: str) -> bytes:
        key = encoded_key.encode()
        return b64.urlsafe_b64decode(key)
