import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """
    同步测试客户端，整个测试会话共用一个
    """
    with TestClient(app) as c:
        yield c
