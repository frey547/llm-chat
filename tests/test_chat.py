import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_llm():
    """拦截所有测试中的 LLM 调用，不真实请求 API"""
    with patch(
        "app.services.llm_service.LLMService.chat",
        new_callable=AsyncMock,
        return_value=("[Mock回复] 这是测试回复", 100),
    ):
        yield


@pytest.fixture
def auth_client(client):
    client.post("/api/v1/auth/register", json={
        "username": "chatuser",
        "email": "chat@example.com",
        "password": "pass123",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "chatuser",
        "password": "pass123",
    })
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_conversation(client, auth_client):
    resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "测试会话"},
        headers=auth_client,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "测试会话"
    assert "id" in data


def test_list_conversations(client, auth_client):
    client.post("/api/v1/chat/conversations", json={"title": "会话1"}, headers=auth_client)
    client.post("/api/v1/chat/conversations", json={"title": "会话2"}, headers=auth_client)
    resp = client.get("/api/v1/chat/conversations", headers=auth_client)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2


def test_send_message_mock(client, auth_client):
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "mock对话"},
        headers=auth_client,
    )
    conv_id = conv_resp.json()["data"]["id"]

    resp = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"content": "你好"},
        headers=auth_client,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "reply" in data
    assert len(data["reply"]) > 0


def test_get_message_history(client, auth_client):
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "历史测试"},
        headers=auth_client,
    )
    conv_id = conv_resp.json()["data"]["id"]

    client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"content": "第一条消息"},
        headers=auth_client,
    )
    client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={"content": "第二条消息"},
        headers=auth_client,
    )

    resp = client.get(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=auth_client,
    )
    assert resp.status_code == 200
    messages = resp.json()["data"]
    assert len(messages) == 4


def test_delete_conversation(client, auth_client):
    conv_resp = client.post(
        "/api/v1/chat/conversations",
        json={"title": "待删除"},
        headers=auth_client,
    )
    conv_id = conv_resp.json()["data"]["id"]

    resp = client.delete(
        f"/api/v1/chat/conversations/{conv_id}",
        headers=auth_client,
    )
    assert resp.status_code == 200

    resp = client.get(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=auth_client,
    )
    assert resp.status_code == 404


def test_send_message_to_nonexistent_conversation(client, auth_client):
    resp = client.post(
        "/api/v1/chat/conversations/99999/messages",
        json={"content": "不存在的会话"},
        headers=auth_client,
    )
    assert resp.status_code == 404
