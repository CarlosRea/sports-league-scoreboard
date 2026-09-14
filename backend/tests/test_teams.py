def test_list_teams(client):
    res = client.get("/api/leagues/league-metro-2026/teams")
    assert res.status_code == 200
    teams = res.json()
    assert len(teams) == 6
    names = [t["name"] for t in teams]
    assert "Riverside FC" in names
    assert "Apex United" in names

def test_list_teams_invalid_league(client):
    res = client.get("/api/leagues/invalid-id/teams")
    assert res.status_code == 404

def test_create_team_requires_admin(client, scorekeeper_headers):
    payload = {"name": "Test Club", "shortName": "TST"}
    res = client.post("/api/leagues/league-metro-2026/teams", json=payload, headers=scorekeeper_headers)
    assert res.status_code == 403

def test_create_team_success(client, admin_headers):
    payload = {
        "name": "Olympia Sporting",
        "shortName": "OLY",
        "logoColor": "#8b5cf6"
    }
    res = client.post("/api/leagues/league-metro-2026/teams", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Olympia Sporting"
    assert data["shortName"] == "OLY"
    assert data["logoColor"] == "#8b5cf6"

def test_create_team_duplicate_name_rejected(client, admin_headers):
    payload = {
        "name": "Riverside FC", # Already exists
        "shortName": "RFC",
    }
    res = client.post("/api/leagues/league-metro-2026/teams", json=payload, headers=admin_headers)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]
