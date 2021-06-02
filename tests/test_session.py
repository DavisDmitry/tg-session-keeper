from telethon import TelegramClient

from session_keeper.session import KeeperSession, Session


def test_session_as_dict(client_with_session: TelegramClient):
    session = client_with_session.session.as_dict()
    for key in ("id", "phone", "mention", "auth_key"):
        assert key in session.keys()


def test_keeper_session_init(client_with_session: TelegramClient):
    session: Session = client_with_session.session
    auth_key = session.as_dict()["auth_key"]
    KeeperSession(
        dc_id=session.dc_id,
        server_address=session.server_address,
        server_port=session.port,
        auth_key=auth_key,
    )
