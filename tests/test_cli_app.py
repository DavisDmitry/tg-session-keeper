from typing import Iterator

import pytest
from telethon import TelegramClient, functions

from session_keeper import CLIApp
from session_keeper.session import Session

from .test_keeper import send_code_request_by_another_session

PASSWORD = "qwerty"
TEST_MODE = True


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def app(temp_file: str, api_id: str, api_hash: str) -> Iterator[CLIApp]:
    app = CLIApp(PASSWORD, filename=temp_file, test_mode=TEST_MODE)
    await app._keeper.setup_storage(api_id, api_hash)
    await app._keeper.start()
    yield app
    await app._keeper.stop()


@pytest.fixture
async def app_with_session(app: CLIApp, client_with_session: TelegramClient) -> CLIApp:
    await app._keeper._storage.add_session(client_with_session.session)
    app._keeper._clients.append(client_with_session)
    return app


def test_print_help(app: CLIApp):
    app._print_help()


def test_print_incorrect_command(app: CLIApp):
    app._print_incorrect_command()


class TestGetSessionNumber:
    def test_with_correct_params_len(self, app: CLIApp):
        number = 0
        assert app._get_session_number(f"get {number}") == number

    def test_with_incorrect_params_len(self, app: CLIApp):
        assert not app._get_session_number("get session 0")


class TestRemove:
    async def test_without_number(self, app: CLIApp):
        assert not await app.remove("remove session 0")

    async def test_with_session(self, app_with_session: CLIApp):
        app = app_with_session
        await app.remove("remove 0")
        assert len(app._keeper._storage.sessions) == 0
        assert len(app._keeper._clients) == 0

    async def test_without_sessions(self, app: CLIApp):
        assert not await app.remove("remove 0")


class TestList:
    async def test_with_session(self, app_with_session: CLIApp):
        await app_with_session.list()

    async def test_without_sessions(self, app: CLIApp):
        await app.list()


class TestGet:
    async def test_without_number(self, app: CLIApp):
        assert not await app.remove("get session 0")

    async def test_with_session(
        self, app_with_session: CLIApp, api_id: int, api_hash: str
    ):
        app = app_with_session
        await send_code_request_by_another_session(
            api_id, api_hash, (await app._keeper.list())[0]
        )
        await app.get("get 0")

    async def test_without_sessions(self, app: CLIApp):
        assert not await app.remove("get 0")

    async def test_with_session__without_messages(
        self, app_with_session: CLIApp, api_id: int, api_hash: str
    ):
        app = app_with_session
        await send_code_request_by_another_session(
            api_id, api_hash, (await app._keeper.list())[0]
        )
        client = app._keeper._clients[0]
        await client(functions.messages.DeleteHistoryRequest(777000, 0))
        await app.get("get 0")
