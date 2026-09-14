def test_cors_preflight_allowed(client):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    res = client.options("/api/matches/m-1/start", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in res.headers.get("access-control-allow-methods", "")


def test_cors_origin_127_0_0_1(client):
    headers = {
        "Origin": "http://127.0.0.1:5173",
        "Access-Control-Request-Method": "GET",
    }
    res = client.options("/api/leagues", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_cors_get_request_headers(client):
    headers = {"Origin": "http://localhost:5173"}
    res = client.get("/api/leagues", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"
