import sqlite3
import struct

from pyrogram.storage import sqlite_storage


class KeeperStorage(sqlite_storage.SQLiteStorage):
    SESSION_STRING_FORMAT = ">B256sQ"

    def __init__(self, data: bytes, test_mode: bool):
        super().__init__(data)  # type: ignore
        self.__test_mode = test_mode

    async def open(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.create()

        dc_id, auth_key, user_id = struct.unpack(self.SESSION_STRING_FORMAT, self.name)
        await self.dc_id(dc_id)
        await self.auth_key(auth_key)
        await self.user_id(user_id)
        await self.test_mode(self.__test_mode)
        await self.is_bot(False)
        await self.date(0)

    async def delete(self):
        pass

    async def export_session_string(self) -> bytes:
        return struct.pack(
            self.SESSION_STRING_FORMAT,
            await self.dc_id(),
            await self.auth_key(),
            await self.user_id(),
        )
