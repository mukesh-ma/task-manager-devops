def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_duplicate(client):
    resp = client.post("/auth/register", json={"email": "a@example.com", "password": "pw123456"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "a@example.com"

    dup = client.post("/auth/register", json={"email": "a@example.com", "password": "pw123456"})
    assert dup.status_code == 400


def test_login_success_and_failure(client):
    client.post("/auth/register", json={"email": "b@example.com", "password": "pw123456"})

    good = client.post("/auth/login", data={"username": "b@example.com", "password": "pw123456"})
    assert good.status_code == 200
    assert "access_token" in good.json()

    bad = client.post("/auth/login", data={"username": "b@example.com", "password": "wrong"})
    assert bad.status_code == 401


def test_tasks_require_auth(client):
    resp = client.get("/tasks")
    assert resp.status_code == 401


def test_task_crud_flow(client, auth_headers):
    create = client.post(
        "/tasks",
        json={"title": "Write README", "description": "Explain the project", "status": "todo"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    task_id = create.json()["id"]

    listed = client.get("/tasks", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(f"/tasks/{task_id}", json={"status": "done"}, headers=auth_headers)
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    deleted = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert deleted.status_code == 204

    missing = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert missing.status_code == 404


def test_metrics_endpoint_exposed(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
