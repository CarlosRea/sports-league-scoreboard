import os
import pytest
import httpx
from starlette.testclient import TestClient

from app.main import app

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8009")


@pytest.fixture
def api_client():
    """Returns a client for testing either against the running Docker stack or in-process TestClient."""
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=1.0)
        if r.status_code == 200:
            client = httpx.Client(base_url=BASE_URL, timeout=5.0)
            yield client
            client.close()
            return
    except Exception:
        pass

    with TestClient(app) as client:
        yield client


def test_health_check_returns_200_and_status(api_client):
    """GET /health returns 200 and status ok / healthy."""
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy")


def test_get_api_leagues_returns_200(api_client):
    """GET /api/leagues returns valid 200 response with list of leagues."""
    response = api_client.get("/api/leagues")
    assert response.status_code == 200
    leagues = response.json()
    assert isinstance(leagues, list)
    assert len(leagues) > 0
    assert "id" in leagues[0]
    assert "name" in leagues[0]


def test_get_api_matches_returns_200(api_client):
    """GET /api/leagues/{leagueId}/matches returns valid 200 response with fixture data."""
    leagues_res = api_client.get("/api/leagues")
    league_id = leagues_res.json()[0]["id"]

    response = api_client.get(f"/api/leagues/{league_id}/matches")
    assert response.status_code == 200
    matches = response.json()
    assert isinstance(matches, list)
    assert len(matches) > 0
    first_match = matches[0]
    assert "id" in first_match
    assert "homeTeamId" in first_match
    assert "awayTeamId" in first_match
    assert "homeScore" in first_match
    assert "awayScore" in first_match


def test_get_api_single_match_returns_200(api_client):
    """GET /api/matches/{matchId} returns valid 200 response."""
    response = api_client.get("/api/matches/match-101")
    assert response.status_code == 200
    match = response.json()
    assert match["id"] == "match-101"
    assert "status" in match


def test_get_api_standings_returns_200(api_client):
    """GET /api/leagues/{leagueId}/standings returns valid 200 response with calculated standings table."""
    leagues_res = api_client.get("/api/leagues")
    league_id = leagues_res.json()[0]["id"]

    response = api_client.get(f"/api/leagues/{league_id}/standings")
    assert response.status_code == 200
    standings_payload = response.json()
    assert "standings" in standings_payload
    standings = standings_payload["standings"]
    assert isinstance(standings, list)
    assert len(standings) > 0
    top_row = standings[0]
    assert "rank" in top_row or "position" in top_row
    assert "teamName" in top_row
    assert "points" in top_row


def test_get_api_teams_returns_200(api_client):
    """GET /api/leagues/{leagueId}/teams returns valid 200 response with team roster."""
    leagues_res = api_client.get("/api/leagues")
    league_id = leagues_res.json()[0]["id"]

    response = api_client.get(f"/api/leagues/{league_id}/teams")
    assert response.status_code == 200
    teams = response.json()
    assert isinstance(teams, list)
    assert len(teams) > 0
    assert "shortName" in teams[0]
