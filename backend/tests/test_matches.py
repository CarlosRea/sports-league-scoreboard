def test_list_matches(client):
    res = client.get("/api/leagues/league-metro-2026/matches")
    assert res.status_code == 200
    matches = res.json()
    assert len(matches) >= 8


def test_filter_matches_by_status(client):
    res = client.get("/api/leagues/league-metro-2026/matches?status=IN_PROGRESS")
    assert res.status_code == 200
    matches = res.json()
    assert len(matches) == 1
    assert matches[0]["id"] == "match-301"


def test_filter_matches_by_matchday(client):
    res = client.get("/api/leagues/league-metro-2026/matches?matchday=1")
    assert res.status_code == 200
    matches = res.json()
    assert len(matches) == 3
    assert all(m["matchday"] == 1 for m in matches)


def test_get_match_detail(client):
    res = client.get("/api/matches/match-301")
    assert res.status_code == 200
    data = res.json()
    assert data["homeScore"] == 2
    assert data["awayScore"] == 1
    assert len(data["events"]) >= 3


def test_create_match_validation(client, admin_headers):
    # Same home and away team
    payload_same_team = {
        "homeTeamId": "team-riverside",
        "awayTeamId": "team-riverside",
        "matchday": 4,
        "scheduledAt": "2026-09-20T15:00:00Z",
    }
    res = client.post(
        "/api/leagues/league-metro-2026/matches", json=payload_same_team, headers=admin_headers
    )
    assert res.status_code == 400
    assert "itself" in res.json()["detail"]


def test_create_match_success(client, admin_headers):
    payload = {
        "homeTeamId": "team-riverside",
        "awayTeamId": "team-apex",
        "matchday": 5,
        "scheduledAt": "2026-09-22T18:00:00Z",
    }
    res = client.post("/api/leagues/league-metro-2026/matches", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "SCHEDULED"
    assert data["homeScore"] == 0
    assert data["awayScore"] == 0
