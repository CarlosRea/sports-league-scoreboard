def test_start_match(client, scorekeeper_headers):
    # match-302 is SCHEDULED
    res = client.post("/api/matches/match-302/start", headers=scorekeeper_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["currentPeriod"] == "1st Half"
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "MATCH_STARTED"


def test_update_live_score(client, scorekeeper_headers):
    # match-301 is IN_PROGRESS (currently 2 - 1)
    payload = {
        "homeScore": 3,
        "awayScore": 1,
        "period": "2nd Half",
        "minute": 75,
        "note": "Brace scored by Riverside striker",
    }
    res = client.patch("/api/matches/match-301/score", json=payload, headers=scorekeeper_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["homeScore"] == 3
    assert data["awayScore"] == 1
    assert data["elapsedMinutes"] == 75
    # Verify new event logged
    latest_event = data["events"][-1]
    assert latest_event["type"] == "GOAL_HOME"
    assert latest_event["homeScoreAfter"] == 3


def test_finish_match(client, scorekeeper_headers):
    # Finalize match-301
    res = client.post("/api/matches/match-301/finish", headers=scorekeeper_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FINISHED"
    assert data["currentPeriod"] == "Full Time"
    assert data["finishedAt"] is not None

    # Scores should now be locked
    res_edit = client.patch(
        "/api/matches/match-301/score",
        json={"homeScore": 4, "awayScore": 1},
        headers=scorekeeper_headers,
    )
    assert res_edit.status_code == 400
    assert "FINISHED" in res_edit.json()["detail"]


def test_scorekeeper_unauthorized_without_token(client):
    res = client.post("/api/matches/match-301/finish")
    assert res.status_code == 401
