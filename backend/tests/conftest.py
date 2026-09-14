import pytest
from starlette.testclient import TestClient
from app.main import app
from app.store.memory_store import store

@pytest.fixture(autouse=True)
def reset_store_before_each_test():
    """Ensure in-memory store is reset to clean seed data before every test."""
    store.reset_data()

@pytest.fixture
def client():
    client_instance = TestClient(app)
    yield client_instance
    client_instance.cookies.clear()

@pytest.fixture
def admin_token():
    with TestClient(app) as c:
        res = c.post("/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
        assert res.status_code == 200
        return res.json()["access_token"]

@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def scorekeeper_token():
    with TestClient(app) as c:
        res = c.post("/api/auth/login", json={"username": "scorekeeper", "password": "RefereePassword123!"})
        assert res.status_code == 200
        return res.json()["access_token"]

@pytest.fixture
def scorekeeper_headers(scorekeeper_token):
    return {"Authorization": f"Bearer {scorekeeper_token}"}
