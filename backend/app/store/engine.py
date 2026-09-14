from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.team import Team
from app.models.match import Match, MatchStatus
from app.models.standings import TeamStanding, MatchResultChar

def calculate_standings(
    teams: List[Team],
    matches: List[Match],
    points_win: int = 3,
    points_draw: int = 1,
    points_loss: int = 0,
    include_in_progress: bool = False
) -> List[TeamStanding]:
    """
    Pure standings calculation engine conforming strictly to docs/spec.md:
    - 3 points Win, 1 point Draw, 0 points Loss (configurable)
    - Tie-breakers: Points -> Goal Difference -> Goals For -> Head-to-Head -> Alphabetical
    - Form guide: Last 5 completed matches (newest first)
    """
    # 1. Initialize stats for each team
    stats: Dict[str, Dict[str, Any]] = {}
    for team in teams:
        stats[team.id] = {
            "team": team,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "points": 0,
            "form_chronological": []
        }

    # 2. Filter relevant matches
    relevant_matches: List[Match] = []
    for m in matches:
        if m.status == MatchStatus.FINISHED or (include_in_progress and m.status == MatchStatus.IN_PROGRESS):
            relevant_matches.append(m)

    # Sort matches chronologically to produce accurate form guide
    def match_time(m: Match) -> float:
        dt_str = m.finishedAt or m.scheduledAt
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0.0

    relevant_matches.sort(key=match_time)

    # 3. Process matches
    for m in relevant_matches:
        home = stats.get(m.homeTeamId)
        away = stats.get(m.awayTeamId)
        if not home or not away:
            continue

        home["played"] += 1
        away["played"] += 1

        home["goals_for"] += m.homeScore
        home["goals_against"] += m.awayScore
        away["goals_for"] += m.awayScore
        away["goals_against"] += m.homeScore

        if m.homeScore > m.awayScore:
            home["won"] += 1
            home["points"] += points_win
            away["lost"] += 1
            away["points"] += points_loss
            home["form_chronological"].append(MatchResultChar.W)
            away["form_chronological"].append(MatchResultChar.L)
        elif m.homeScore < m.awayScore:
            away["won"] += 1
            away["points"] += points_win
            home["lost"] += 1
            home["points"] += points_loss
            away["form_chronological"].append(MatchResultChar.W)
            home["form_chronological"].append(MatchResultChar.L)
        else:
            home["drawn"] += 1
            home["points"] += points_draw
            away["drawn"] += 1
            away["points"] += points_draw
            home["form_chronological"].append(MatchResultChar.D)
            away["form_chronological"].append(MatchResultChar.D)

    # Head-to-head helper
    def get_head_to_head_points(team_a_id: str, team_b_id: str) -> int:
        diff = 0
        for m in relevant_matches:
            if m.homeTeamId == team_a_id and m.awayTeamId == team_b_id:
                if m.homeScore > m.awayScore:
                    diff += points_win
                elif m.homeScore < m.awayScore:
                    diff -= points_win
            elif m.homeTeamId == team_b_id and m.awayTeamId == team_a_id:
                if m.awayScore > m.homeScore:
                    diff += points_win
                elif m.awayScore < m.homeScore:
                    diff -= points_win
        return diff

    # 4. Build standing records
    rows: List[Dict[str, Any]] = []
    for team_id, data in stats.items():
        team_obj: Team = data["team"]
        gd = data["goals_for"] - data["goals_against"]
        # Last 5 matches, newest first
        form = list(reversed(data["form_chronological"][-5:]))

        rows.append({
            "team_id": team_id,
            "team_name": team_obj.name,
            "short_name": team_obj.shortName,
            "logo_color": team_obj.logoColor,
            "played": data["played"],
            "won": data["won"],
            "drawn": data["drawn"],
            "lost": data["lost"],
            "goals_for": data["goals_for"],
            "goals_against": data["goals_against"],
            "goal_difference": gd,
            "points": data["points"],
            "form": form,
        })

    # 5. Sort by tie-breaking hierarchy:
    # 1. Points (descending)
    # 2. Goal Difference (descending)
    # 3. Goals For (descending)
    # 4. Head-to-Head points
    # 5. Team Name (alphabetical ascending)
    def compare_rows(a: Dict[str, Any], b: Dict[str, Any]) -> int:
        if b["points"] != a["points"]:
            return b["points"] - a["points"]
        if b["goal_difference"] != a["goal_difference"]:
            return b["goal_difference"] - a["goal_difference"]
        if b["goals_for"] != a["goals_for"]:
            return b["goals_for"] - a["goals_for"]
        h2h = get_head_to_head_points(b["team_id"], a["team_id"])
        if h2h != 0:
            return h2h
        return -1 if a["team_name"].lower() < b["team_name"].lower() else 1

    import functools
    sorted_rows = sorted(rows, key=functools.cmp_to_key(compare_rows))

    # 6. Assign final 1-based ranks
    standings: List[TeamStanding] = []
    for rank, r in enumerate(sorted_rows, start=1):
        standings.append(
            TeamStanding(
                rank=rank,
                teamId=r["team_id"],
                teamName=r["team_name"],
                shortName=r["short_name"],
                logoColor=r["logo_color"],
                played=r["played"],
                won=r["won"],
                drawn=r["drawn"],
                lost=r["lost"],
                goalsFor=r["goals_for"],
                goalsAgainst=r["goals_against"],
                goalDifference=r["goal_difference"],
                points=r["points"],
                form=r["form"]
            )
        )

    return standings
