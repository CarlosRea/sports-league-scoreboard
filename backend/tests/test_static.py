from starlette.testclient import TestClient


def test_serve_root_index_html(client: TestClient):
    """Verify GET / returns index.html for the frontend SPA."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!doctype html>" in response.text.lower()
    assert '<div id="root">' in response.text


def test_serve_static_asset(client: TestClient):
    """Verify static assets such as favicon.svg can be served."""
    response = client.get("/favicon.svg")
    assert response.status_code == 200
    assert "svg" in response.headers.get("content-type", "")


def test_spa_client_side_routing(client: TestClient):
    """Verify frontend SPA client-side routes (e.g. /standings, /matches) serve index.html."""
    for path in ["/standings", "/matches", "/scorekeeper", "/teams"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "<!doctype html>" in response.text.lower()
        assert '<div id="root">' in response.text


def test_api_404_not_swallowed_by_spa(client: TestClient):
    """Verify nonexistent API routes return 404 JSON instead of index.html."""
    response = client.get("/api/unknown_endpoint")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_docs_and_health_not_swallowed_by_spa(client: TestClient):
    """Verify health and docs routes behave appropriately."""
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    docs_404_resp = client.get("/docs/nonexistent")
    assert docs_404_resp.status_code == 404


def test_path_traversal_protection(client: TestClient):
    """Verify path traversal requests cannot escape static directory."""
    response = client.get("/../../etc/passwd")
    assert "root:x:0:0:" not in response.text
