def test_get_official_standings(client):
    res = client.get("/api/leagues/league-metro-2026/standings")
    assert res.status_code == 200
    data = res.json()
    assert data["leagueId"] == "league-metro-2026"
    assert data["isLiveProvisional"] is False
    standings = data["standings"]
    assert len(standings) == 6

    # Verify 1st place
    leader = standings[0]
    assert leader["rank"] == 1
    # Check that points and matches adhere to 3-1-0
    for s in standings:
        calculated_points = (s["won"] * 3) + (s["drawn"] * 1)
        assert s["points"] == calculated_points
        assert s["goalDifference"] == s["goalsFor"] - s["goalsAgainst"]
        assert s["played"] == s["won"] + s["drawn"] + s["lost"]


def test_provisional_live_standings(client):
    res_official = client.get("/api/leagues/league-metro-2026/standings")
    res_live = client.get("/api/leagues/league-metro-2026/standings?live=true")

    assert res_live.status_code == 200
    data_live = res_live.json()
    assert data_live["isLiveProvisional"] is True

    # In-progress match-301 (Riverside 2 - 1 Red Star)
    # Riverside should have 1 more match counted in provisional live standings than in official
    official_riverside = next(
        s for s in res_official.json()["standings"] if s["teamId"] == "team-riverside"
    )
    live_riverside = next(s for s in data_live["standings"] if s["teamId"] == "team-riverside")

    assert live_riverside["played"] == official_riverside["played"] + 1
    assert live_riverside["points"] == official_riverside["points"] + 3


def test_finish_match_updates_official_standings(client, scorekeeper_headers):
    # Check official points before final whistle
    res_before = client.get("/api/leagues/league-metro-2026/standings")
    riverside_before = next(
        s for s in res_before.json()["standings"] if s["teamId"] == "team-riverside"
    )

    # Finalize match
    res_finish = client.post("/api/matches/match-301/finish", headers=scorekeeper_headers)
    assert res_finish.status_code == 200

    # Official standings should now immediately count this win
    res_after = client.get("/api/leagues/league-metro-2026/standings")
    riverside_after = next(
        s for s in res_after.json()["standings"] if s["teamId"] == "team-riverside"
    )

    assert riverside_after["played"] == riverside_before["played"] + 1
    assert riverside_after["points"] == riverside_before["points"] + 3
    assert riverside_after["form"][0] == "W"
