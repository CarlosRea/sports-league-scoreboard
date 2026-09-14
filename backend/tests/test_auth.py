def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"
    assert "session_id" in res.cookies

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword"})
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]

def test_login_unknown_user(client):
    res = client.post("/api/auth/login", json={"username": "nonexistent", "password": "SomePassword123!"})
    assert res.status_code == 401

def test_get_me_with_bearer_token(client, admin_headers):
    res = client.get("/api/auth/me", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"

def test_get_me_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401

def test_oauth2_form_token_endpoint(client):
    res = client.post(
        "/api/auth/token",
        data={"username": "scorekeeper", "password": "RefereePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "scorekeeper"
    assert "access_token" in data
