import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_tables():
    """测试前后都清表，保证完全隔离"""
    _clean()      # 测试开始前清
    yield
    _clean()      # 测试结束后清


def _clean():
    db = SessionLocal()
    try:
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
