from typing import Iterator, Tuple

import pytest
from telethon import TelegramClient

from session_keeper import Keeper
from session_keeper.session import Session

PASSWORD = "qwerty"
TEST_MODE = True


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def keeper(
    api_id: str,
    api_hash: str,
    temp_file: str,
    client_with_session: TelegramClient,
) -> Iterator[Keeper]:
    keeper = Keeper.init_with_file_ejs(PASSWORD, temp_file, test_mode=TEST_MODE)
    await keeper.setup_storage(api_id, api_hash)
    await keeper.start()
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


async def test_add__login_add_code_and_password(
    keeper: Keeper, client_with_session: TelegramClient, dc: Tuple[int, str, int]
):
    dc_id, _, __ = dc
    phone = client_with_session.session.phone
    await keeper.add(phone)
    assert keeper._client_for_login
    await keeper.login_add_code_and_password(str(dc_id) * 6)
    assert not keeper._client_for_login
    assert len(keeper._clients) == 2
    assert len(keeper._storage.sessions) == 2
    assert keeper._clients[1].is_connected()


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


async def test_start(keeper: Keeper):
    await keeper.stop()
    await keeper.start()
    assert keeper.started
