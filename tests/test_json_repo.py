import pytest

from session_keeper import repositories, utils

_API_ID = 1234567
_API_HASH = "zzSMPBZv6Jo3GxEuQzURnK8Jq80MkQoe"
_PASSWORD = "qwerty"
_AUTH_KEY = (
    "gYY40NMfyJvIKXi9vrtCnRnReWhiLCNcPyM6X3H7qknAo0wiF0TUPuMmO1OqATcPwO4xuUhx9hkM9EURuz"
    "IDrFt0GBeY0qd7r9CoVTOuvQoHHfMFqMLoG7jOeKS9wY2oXCuYN5JTxpBMFeXOUA4srD4w8YUpYJDeNSAC"
    "wlpZtwrYE0YCZlxi9skNfKUNcEmmUIWSpWqlKOe1lbOCJTZnOQElqoCNYShPDpwD9fbIIoHaqpl41NVXOP"
    "jE4c1IGrIE"
)


pytestmark = pytest.mark.asyncio


@pytest.fixture
def e_json_file(temp_file: str) -> None:
    # file created with session keeper version 0.1.2, but some data was replaced
    with open("tests/e_json.tgsk", "rb") as file, open(temp_file, "wb") as tmp:
        tmp.write(file.read())
        tmp.flush()


@pytest.mark.usefixtures("e_json_file")
async def test_transform_success(temp_file: str):
    json_repository = await repositories.EncryptedJsonRepository.from_file(
        _PASSWORD, temp_file
    )
    assert len(await json_repository.get_many()) == 1
    repository = await utils.transform_e_json_to_e_bin(json_repository, _PASSWORD)
    assert repository.api_id == _API_ID
    assert repository.api_hash == _API_HASH
    storage = tuple(await repository.iter())[0]
    assert await storage.auth_key() == _AUTH_KEY.encode()


async def test_invalid_version(temp_file: str):
    with open(temp_file, "wb") as file:
        file.write(b"qwerty")
    with pytest.raises(repositories.InvalidRepositoryVersionError):
        await repositories.EncryptedJsonRepository.from_file(_PASSWORD, temp_file)


@pytest.mark.usefixtures("e_json_file")
async def test_wrong_password(temp_file: str):
    with pytest.raises(repositories.WrongPasswordError):
        await repositories.EncryptedJsonRepository.from_file(
            "invalid password", temp_file
        )


@pytest.mark.parametrize(
    ("method", "pass_user_id"),
    (("remove", True), ("get_or_none", True), ("get", True), ("save", False)),
)
async def test_not_implemented(method: str, pass_user_id: bool):
    repository = repositories.EncryptedJsonRepository(
        _API_ID, _API_HASH, "sessions.tgsk"
    )
    func = getattr(repository, method)
    with pytest.raises(NotImplementedError):
        if pass_user_id:
            await func(1)
            return
        await func()
