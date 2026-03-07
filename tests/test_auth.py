import pytest


def test_register_success(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["username"] == "testuser"
    assert data["data"]["email"] == "test@example.com"


def test_register_duplicate_username(client):
    payload = {"username": "dupeuser", "email": "dupe@example.com", "password": "pass123"}
    client.post("/api/v1/auth/register", json=payload)
    # 第二次注册相同用户名
    response = client.post("/api/v1/auth/register", json={
        "username": "dupeuser",
        "email": "other@example.com",
        "password": "pass123",
    })
    assert response.status_code == 409


def test_login_success(client):
    # 先注册
    client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "pass123",
    })
    # 再登录
    response = client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "pass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_login_wrong_password(client):
    response = client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_get_me_with_valid_token(client):
    # 注册并登录拿到 token
    client.post("/api/v1/auth/register", json={
        "username": "meuser",
        "email": "me@example.com",
        "password": "pass123",
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "meuser",
        "password": "pass123",
    })
    token = login_resp.json()["data"]["access_token"]

    # 用 token 访问 /me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "meuser"


def test_get_me_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403
