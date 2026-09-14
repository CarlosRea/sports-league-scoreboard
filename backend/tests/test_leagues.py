def test_list_leagues(client):
    res = client.get("/api/leagues")
    assert res.status_code == 200
    leagues = res.json()
    assert len(leagues) >= 1
    assert leagues[0]["id"] == "league-metro-2026"
    assert leagues[0]["pointsWin"] == 3
    assert leagues[0]["pointsDraw"] == 1
    assert leagues[0]["pointsLoss"] == 0


def test_get_league_by_id(client):
    res = client.get("/api/leagues/league-metro-2026")
    assert res.status_code == 200
    assert res.json()["name"] == "Metropolitan Amateur Premier League"


def test_get_league_not_found(client):
    res = client.get("/api/leagues/nonexistent-league")
    assert res.status_code == 404


def test_create_league_requires_admin(client, scorekeeper_headers):
    payload = {"name": "Sunday League", "season": "2026"}

    # Clear residual session cookies from fixtures to test anonymous access
    client.cookies.clear()
    res_anon = client.post("/api/leagues", json=payload)
    assert res_anon.status_code == 401

    # With Scorekeeper token -> 403 (Admin required)
    res_sk = client.post("/api/leagues", json=payload, headers=scorekeeper_headers)
    assert res_sk.status_code == 403


def test_create_league_success_with_admin(client, admin_headers):
    payload = {
        "name": "Community Futsal Cup",
        "season": "Summer 2026",
        "sportType": "Futsal",
        "pointsWin": 3,
        "pointsDraw": 1,
        "pointsLoss": 0,
    }
    res = client.post("/api/leagues", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Community Futsal Cup"
    assert data["sportType"] == "Futsal"
    assert "id" in data
