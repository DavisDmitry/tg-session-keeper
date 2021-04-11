import os
from random import randint
from tempfile import NamedTemporaryFile
from typing import Iterator, Tuple

import pytest
from session_keeper.session import Session
from telethon import TelegramClient


@pytest.fixture
def api_id() -> int:
    return int(os.environ['API_ID'])


@pytest.fixture
def api_hash() -> str:
    return os.environ['API_HASH']


@pytest.fixture
def dc() -> Tuple[int, str, int]:
    return (int(os.environ['DC_ID']), os.environ['DC_ADDRESS'],
            int(os.environ['DC_PORT']))


@pytest.fixture
def phone(dc: Tuple[int, str, int]) -> str:
    dc_id, _, __ = dc
    rand_ints = ''.join([str(randint(0, 9)) for _ in range(4)])
    return f'99966{dc_id}{rand_ints}'


@pytest.fixture
@pytest.mark.asyncio
async def client_with_session(
        api_id: int, api_hash: str, dc: Tuple[int, str, int], phone: str
) -> Iterator[TelegramClient]:
    client = TelegramClient(Session(), api_id, api_hash)
    dc_id, dc_address, dc_port = dc
    client.session.set_dc(dc_id, dc_address, dc_port)
    auth_code = str(dc_id) * 6
    await client.start(phone=lambda: phone, code_callback=lambda: auth_code)
    yield client
    await client.disconnect()


@pytest.fixture
def temp_file() -> Iterator[str]:
    file = NamedTemporaryFile('wb')
    yield file.name
