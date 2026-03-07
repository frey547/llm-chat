import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message


@pytest.fixture(scope="session")
def event_loop():
    """整个测试会话共用一个 event loop，避免异步客户端跨 loop 报错"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_tables():
    _clean()
    yield
    _clean()


def _clean():
    db = SessionLocal()
    try:
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
