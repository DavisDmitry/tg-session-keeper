import asyncio

from session_keeper import repositories


async def transform_e_json_to_e_bin(
    repository: repositories.EncryptedJsonRepository, password: str
) -> repositories.EncryptedBinaryRepository:
    """Transforms deprecated EncryptedJSONRepository to EncryptedBinaryRepository."""
    new_repo = repositories.EncryptedBinaryRepository(
        repository.api_id,
        repository.api_hash,
        repository.filename,
        password,
        test_mode=repository.test_mode,
    )
    await asyncio.gather(
        *(new_repo.add(storage) for storage in await repository.iter())
    )
    await new_repo.save()
    return new_repo
