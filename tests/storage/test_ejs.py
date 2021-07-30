import pytest
from telethon import TelegramClient

from session_keeper.storage import (
    InvalidPassword,
    MismatchedVersionError,
    StorageNotFound,
    StorageSettedError,
)
from session_keeper.storage.ejs import (
    FileEncryptedJsonStorage,
    MemoryEncryptedJsonStorage,
)

PASSWORD = "qwerty"


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def memory_storage(api_id: int, api_hash: str) -> MemoryEncryptedJsonStorage:
    storage = MemoryEncryptedJsonStorage(PASSWORD)
    await storage.setup(api_id, api_hash)
    return storage


@pytest.fixture
async def file_storage(
    temp_file: str, api_id: int, api_hash: str
) -> FileEncryptedJsonStorage:
    storage = FileEncryptedJsonStorage(PASSWORD, temp_file)
    await storage.setup(api_id, api_hash)
    return storage


@pytest.fixture
async def memory_storage_with_session(
    client_with_session: TelegramClient, memory_storage: MemoryEncryptedJsonStorage
) -> MemoryEncryptedJsonStorage:
    await memory_storage.add_session(client_with_session.session)
    return memory_storage


@pytest.fixture
async def file_storage_with_session(
    client_with_session: TelegramClient, file_storage: FileEncryptedJsonStorage
) -> FileEncryptedJsonStorage:
    await file_storage.add_session(client_with_session.session)
    return file_storage


class TestEncryptAndDecrypt:
    async def test_memory(
        self, memory_storage_with_session: MemoryEncryptedJsonStorage
    ):
        storage1 = memory_storage_with_session
        async with MemoryEncryptedJsonStorage(
            PASSWORD, encrypted_data=storage1.encrypted_data
        ) as storage2:
            assert storage1.api_id == storage2.api_id
            assert storage1.api_hash == storage2.api_hash
            client = TelegramClient(
                storage2.sessions[0], storage2.api_id, storage2.api_hash
            )
            async with client:
                assert storage1.sessions[0].as_dict() == storage2.sessions[0].as_dict()

    async def test_file(self, file_storage_with_session: FileEncryptedJsonStorage):
        storage1 = file_storage_with_session
        await storage1.save()

        async with FileEncryptedJsonStorage(PASSWORD, storage1.filename) as storage2:
            assert storage1.api_id == storage2.api_id
            assert storage1.api_hash == storage2.api_hash
            client = TelegramClient(
                storage2.sessions[0], storage2.api_id, storage2.api_hash
            )
            async with client:
                assert storage1.sessions[0].as_dict() == storage2.sessions[0].as_dict()


async def test_invalid_password(memory_storage: MemoryEncryptedJsonStorage):
    storage2 = MemoryEncryptedJsonStorage(
        "invalid password", encrypted_data=memory_storage.encrypted_data
    )
    with pytest.raises(InvalidPassword):
        await storage2.start()


class TestStorageNotFound:
    async def test_file_doesnt_exist(self):
        storage = FileEncryptedJsonStorage(PASSWORD, filename="qwerty")
        with pytest.raises(StorageNotFound):
            await storage.start()

    async def test_file_without_data(self, temp_file: str):
        storage = FileEncryptedJsonStorage(PASSWORD, temp_file)
        with pytest.raises(StorageNotFound):
            await storage.start()


async def test_storage_setted_error(
    file_storage: FileEncryptedJsonStorage, api_id: int, api_hash: str
):
    with pytest.raises(StorageSettedError):
        await file_storage.setup(api_id, api_hash)


async def test_mismatched_version_error():
    storage = MemoryEncryptedJsonStorage(PASSWORD, encrypted_data=b"5_fake_data")
    with pytest.raises(MismatchedVersionError):
        await storage.start()
