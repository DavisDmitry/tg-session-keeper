import random
import string
import struct

import pytest

from session_keeper import repositories
from session_keeper import storage as _storage

_API_ID = 1234567
_API_HASH = "".join(random.choices(string.ascii_letters + string.digits, k=32))
_PASSWORD = "SuperStrongPassword123"


pytestmark = pytest.mark.asyncio


async def test_bin_repo_success(temp_file: str):
    storage_bytes = struct.pack(
        _storage.KeeperStorage.SESSION_STRING_FORMAT,
        2,
        "".join(random.choices(string.ascii_letters + string.digits, k=256)).encode(),
        12345678,
    )
    storage = _storage.KeeperStorage(storage_bytes, False)
    await storage.open()
    repository: repositories.EncryptedBinaryRepository = (
        repositories.EncryptedBinaryRepository(_API_ID, _API_HASH, temp_file, _PASSWORD)
    )
    await repository.add(storage)
    await repository.save()
    with pytest.raises(repositories.StorageAlreadyInRepositoryError):
        await repository.add(storage)
    assert await storage.user_id() == await (await repository.get_many())[0].user_id()
    await repository.get_or_none(await storage.user_id())
    await repository.get(await storage.user_id())
    repository = await repositories.EncryptedBinaryRepository.from_file(
        repository.file_path, _PASSWORD
    )
    await repository.remove(await storage.user_id())
    with pytest.raises(repositories.StorageDoesNotExistInRepositoryError):
        await repository.remove(await storage.user_id())
    assert len(await repository.get_many()) == 0
    assert len(tuple(__storage for __storage in await repository.iter())) == 0
    assert await repository.get_or_none(await storage.user_id()) is None
    with pytest.raises(repositories.StorageDoesNotExistInRepositoryError):
        await repository.get(await storage.user_id())
    assert repository.api_id == _API_ID
    assert repository.api_hash == _API_HASH
    assert repository.test_mode is False
    assert repository.file_path == temp_file


async def test_invalid_version(temp_file: str):
    with open(temp_file, "wb") as file:
        file.write(b"qwerty\n1234567")
        file.flush()
    with pytest.raises(repositories.InvalidRepositoryVersionError):
        await repositories.EncryptedBinaryRepository.from_file(temp_file, _PASSWORD)


async def test_wrong_password(temp_file: str):
    # pylint: disable=W0212
    data = struct.pack(
        repositories.EncryptedBinaryRepository._API_DATA_FORMAT,
        _API_ID,
        _API_HASH.encode(),
        False,
    )
    fernet = repositories.EncryptedBinaryRepository._create_fernet(
        _PASSWORD, b"TGSK", 8
    )
    data = fernet.encrypt(data)
    data = b"\n".join((repositories.EncryptedBinaryRepository.REPOSITORY_VERSION, data))
    with open(temp_file, "wb") as file:
        file.write(data)
        file.flush()
    with pytest.raises(repositories.WrongPasswordError):
        await repositories.EncryptedBinaryRepository.from_file(
            temp_file, "invalid password"
        )
