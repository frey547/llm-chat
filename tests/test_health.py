def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


def test_ready_returns_checks(client):
    """/ready 必须返回 checks 字段，包含 database 和 redis 状态"""
    response = client.get("/api/v1/ready")
    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]


def test_request_id_in_response_header(client):
    response = client.get("/api/v1/health")
    assert "x-request-id" in response.headers


def test_docs_accessible(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_metrics_endpoint_accessible(client):
    response = client.get("/metrics")
    assert response.status_code == 200
