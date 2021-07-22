import pytest
from telethon import TelegramClient

from session_keeper.storage import MemoryStorage, StorageSettedError

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def storage(api_id: int, api_hash: str) -> MemoryStorage:
    storage = MemoryStorage()
    await storage.setup(api_id, api_hash)
    return storage


@pytest.fixture
async def storage_with_session(
    client_with_session: TelegramClient, storage: MemoryStorage
) -> MemoryStorage:
    await storage.add_session(client_with_session.session)
    return storage


def test_properties(storage: MemoryStorage, api_id: int, api_hash: str):
    assert storage.api_id == api_id
    assert storage.api_hash == api_hash


async def test_remove_session(storage_with_session: MemoryStorage):
    storage = storage_with_session
    await storage.remove_session(0)
    assert len(storage.sessions) == 0


async def test_storage_setted_error(storage: MemoryStorage, api_id: int, api_hash: str):
    with pytest.raises(StorageSettedError):
        await storage.setup(api_id, api_hash)


async def test_passed(storage: MemoryStorage):
    await storage.start()
    await storage.save()
    await storage.stop()
