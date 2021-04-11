from tempfile import NamedTemporaryFile
from typing import Iterator

import pytest
from session_keeper.storage import (EncryptedJsonStorage,
                                    MismatchedVersionError, StorageNotFound,
                                    StorageSettedError)
from telethon import TelegramClient


PASSWORD = 'qwerty'


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def storage(
        temp_file: str, api_id: int, api_hash: str
) -> EncryptedJsonStorage:
    storage = EncryptedJsonStorage(PASSWORD, filename=temp_file)
    await storage.setup(api_id, api_hash)
    return storage


@pytest.fixture
async def storage_with_session(
        client_with_session: TelegramClient, storage: EncryptedJsonStorage
) -> EncryptedJsonStorage:
    await storage.add_session(client_with_session.session)
    return storage


@pytest.fixture
def storage_file() -> Iterator[str]:
    with NamedTemporaryFile('wb') as file:
        file.write(b'5_')
        file.flush()
        yield file.name


async def test_encrypt_and_decrypt(storage_with_session: EncryptedJsonStorage):
    filename = storage_with_session.filename

    storage1 = storage_with_session
    await storage1.save()

    async with EncryptedJsonStorage(PASSWORD, filename=filename) as storage2:
        client = TelegramClient(storage2.sessions[0],
                                storage2.api_id,
                                storage2.api_hash)
        async with client:
            assert storage2.api_id == storage1.api_id
            assert storage2.api_hash == storage1.api_hash
            assert len(storage2.sessions) > 0


async def test_remove_session(storage_with_session: EncryptedJsonStorage):
    storage = storage_with_session
    await storage.remove_session(0)
    assert len(storage.sessions) == 0


async def test_storage_not_found():
    storage = EncryptedJsonStorage(PASSWORD, filename='qwerty')
    with pytest.raises(StorageNotFound):
        await storage.start()


async def test_storage_setted_error(storage: EncryptedJsonStorage,
                                    api_id: int, api_hash: str):
    with pytest.raises(StorageSettedError):
        await storage.setup(api_id, api_hash)


async def test_mismatched_version_error(storage_file: str):
    storage = EncryptedJsonStorage(PASSWORD,
                                   filename=storage_file,
                                   version=1)
    with pytest.raises(MismatchedVersionError):
        await storage.start()
