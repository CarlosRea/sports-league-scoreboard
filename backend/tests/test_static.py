import pytest
from starlette.testclient import TestClient

from app.config import settings


@pytest.fixture(autouse=True)
def setup_test_static_assets(tmp_path, monkeypatch):
    """Ensure a hermetic static directory with index.html and assets exists for testing."""
    static_dir = tmp_path / "mock_static"
    static_dir.mkdir(parents=True, exist_ok=True)

    index_html = static_dir / "index.html"
    index_html.write_text(
        '<!doctype html><html lang="en"><body><div id="root">Scoreboard SPA</div></body></html>',
        encoding="utf-8",
    )

    favicon_svg = static_dir / "favicon.svg"
    favicon_svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle r="50"/></svg>',
        encoding="utf-8",
    )

    monkeypatch.setenv("STATIC_DIR", str(static_dir))
    return static_dir


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


def test_static_not_configured_returns_404(client: TestClient, monkeypatch):
    """Verify that when static dir is not configured, SPA routes return 404 cleanly."""
    monkeypatch.setattr(type(settings), "STATIC_DIR", property(lambda self: None))
    response = client.get("/")
    assert response.status_code == 404
