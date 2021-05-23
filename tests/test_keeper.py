from typing import Iterator

import pytest
from session_keeper import BaseKeeper
from session_keeper.session import Session
from telethon import TelegramClient


PASSWORD = "qwerty"
TEST_MODE = True


pytestmark = pytest.mark.asyncio


class Keeper(BaseKeeper):
    async def add(self):
        pass

    async def setup_storage(self) -> None:
        await self._storage.setup(self.api_id, self.api_hash)

    @classmethod
    def run(cls) -> None:
        pass


@pytest.fixture
async def keeper(
    api_id: str,
    api_hash: str,
    temp_file: str,
    client_with_session: TelegramClient,
) -> Iterator[Keeper]:
    keeper = Keeper()
    keeper.api_id = api_id
    keeper.api_hash = api_hash
    await keeper.start(PASSWORD, test_mode=TEST_MODE, filename=temp_file)
    await keeper._storage.add_session(client_with_session.session)
    keeper._clients.append(client_with_session)
    yield keeper
    await keeper.stop()


async def send_code_request_by_another_session(
    api_id: int, api_hash: str, session: Session
) -> None:
    client = TelegramClient(Session(), api_id, api_hash)
    client.session.set_dc(session.dc_id, session.server_address, session.port)
    await client.connect()
    await client.send_code_request(session.phone)
    await client.disconnect()


async def test_properties(keeper: Keeper):
    assert keeper.started is True
    assert keeper.test_mode is TEST_MODE


async def test_remove(keeper: Keeper):
    await keeper.remove(0)
    assert len(keeper._storage.sessions) == 0
    assert len(keeper._clients) == 0


async def test_list(keeper: Keeper):
    assert len(await keeper.list()) == 1


async def test_get(keeper: Keeper, api_id: int, api_hash: str):
    await send_code_request_by_another_session(
        api_id, api_hash, (await keeper.list())[0]
    )
    msg = await keeper.get(0)
    assert msg
