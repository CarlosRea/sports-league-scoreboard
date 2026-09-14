import asyncio
from datetime import UTC, datetime

from app.auth.security import hash_password
from app.models.auth import User, UserRole
from app.models.common import ServiceEvent
from app.models.league import CreateLeagueDto, League
from app.models.match import (
    CreateMatchDto,
    Match,
    MatchEvent,
    MatchEventType,
    MatchPeriod,
    MatchStatus,
    UpdateScoreDto,
)
from app.models.standings import StandingsResponse
from app.models.team import CreateTeamDto, Team
from app.store.engine import calculate_standings
from app.store.sql_store import store

__all__ = ["MemoryStore", "store"]

# Pre-computed bcrypt hashes for fast in-memory resets
ADMIN_PASSWORD_HASH = hash_password("AdminPassword123!")
SCOREKEEPER_PASSWORD_HASH = hash_password("RefereePassword123!")


class MemoryStore:
    def __init__(self):
        self.users: dict[str, User] = {}
        self.leagues: dict[str, League] = {}
        self.teams: dict[str, Team] = {}
        self.matches: dict[str, Match] = {}
        self.subscribers: set[asyncio.Queue] = set()
        self.reset_data()

    def reset_data(self):
        """Reset the in-memory database to default seed data."""
        self.users.clear()
        self.leagues.clear()
        self.teams.clear()
        self.matches.clear()

        # Seed Users
        self.users["admin"] = User(
            username="admin",
            role=UserRole.ADMIN,
            hashed_password=ADMIN_PASSWORD_HASH,
            is_active=True,
        )
        self.users["scorekeeper"] = User(
            username="scorekeeper",
            role=UserRole.SCOREKEEPER,
            hashed_password=SCOREKEEPER_PASSWORD_HASH,
            is_active=True,
        )

        # Seed League
        league_id = "league-metro-2026"
        self.leagues[league_id] = League(
            id=league_id,
            name="Metropolitan Amateur Premier League",
            season="2026 / 2027",
            sportType="Soccer",
            pointsWin=3,
            pointsDraw=1,
            pointsLoss=0,
            createdAt="2026-08-01T00:00:00.000Z",
            updatedAt="2026-08-01T00:00:00.000Z",
        )

        # Seed Teams
        initial_teams = [
            Team(
                id="team-riverside",
                leagueId=league_id,
                name="Riverside FC",
                shortName="RFC",
                logoColor="#10b981",
                createdAt="2026-08-01T01:00:00.000Z",
            ),
            Team(
                id="team-apex",
                leagueId=league_id,
                name="Apex United",
                shortName="APX",
                logoColor="#0284c7",
                createdAt="2026-08-01T01:05:00.000Z",
            ),
            Team(
                id="team-redstar",
                leagueId=league_id,
                name="Red Star Athletic",
                shortName="RSA",
                logoColor="#ef4444",
                createdAt="2026-08-01T01:10:00.000Z",
            ),
            Team(
                id="team-oakwood",
                leagueId=league_id,
                name="Oakwood Rovers",
                shortName="OAK",
                logoColor="#f59e0b",
                createdAt="2026-08-01T01:15:00.000Z",
            ),
            Team(
                id="team-harbor",
                leagueId=league_id,
                name="Harbor City SC",
                shortName="HBC",
                logoColor="#6366f1",
                createdAt="2026-08-01T01:20:00.000Z",
            ),
            Team(
                id="team-knights",
                leagueId=league_id,
                name="Northern Knights",
                shortName="NOK",
                logoColor="#a855f7",
                createdAt="2026-08-01T01:25:00.000Z",
            ),
        ]
        for t in initial_teams:
            self.teams[t.id] = t

        # Seed Matches (Round 1 & 2 Finished, Round 3 Live & Scheduled)
        initial_matches = [
            # Round 1
            Match(
                id="match-101",
                leagueId=league_id,
                homeTeamId="team-riverside",
                awayTeamId="team-oakwood",
                matchday=1,
                scheduledAt="2026-09-01T14:00:00.000Z",
                status=MatchStatus.FINISHED,
                homeScore=3,
                awayScore=1,
                currentPeriod=MatchPeriod.FULL_TIME,
                elapsedMinutes=90,
                startedAt="2026-09-01T14:00:00.000Z",
                finishedAt="2026-09-01T15:50:00.000Z",
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-09-01T15:50:00.000Z",
            ),
            Match(
                id="match-102",
                leagueId=league_id,
                homeTeamId="team-apex",
                awayTeamId="team-harbor",
                matchday=1,
                scheduledAt="2026-09-01T16:00:00.000Z",
                status=MatchStatus.FINISHED,
                homeScore=2,
                awayScore=2,
                currentPeriod=MatchPeriod.FULL_TIME,
                elapsedMinutes=90,
                startedAt="2026-09-01T16:00:00.000Z",
                finishedAt="2026-09-01T17:55:00.000Z",
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-09-01T17:55:00.000Z",
            ),
            Match(
                id="match-103",
                leagueId=league_id,
                homeTeamId="team-redstar",
                awayTeamId="team-knights",
                matchday=1,
                scheduledAt="2026-09-02T15:00:00.000Z",
                status=MatchStatus.FINISHED,
                homeScore=1,
                awayScore=0,
                currentPeriod=MatchPeriod.FULL_TIME,
                elapsedMinutes=90,
                startedAt="2026-09-02T15:00:00.000Z",
                finishedAt="2026-09-02T16:50:00.000Z",
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-09-02T16:50:00.000Z",
            ),
            # Round 2
            Match(
                id="match-201",
                leagueId=league_id,
                homeTeamId="team-oakwood",
                awayTeamId="team-apex",
                matchday=2,
                scheduledAt="2026-09-08T14:00:00.000Z",
                status=MatchStatus.FINISHED,
                homeScore=2,
                awayScore=1,
                currentPeriod=MatchPeriod.FULL_TIME,
                elapsedMinutes=90,
                startedAt="2026-09-08T14:00:00.000Z",
                finishedAt="2026-09-08T15:52:00.000Z",
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-09-08T15:52:00.000Z",
            ),
            Match(
                id="match-202",
                leagueId=league_id,
                homeTeamId="team-knights",
                awayTeamId="team-riverside",
                matchday=2,
                scheduledAt="2026-09-08T16:00:00.000Z",
                status=MatchStatus.FINISHED,
                homeScore=1,
                awayScore=4,
                currentPeriod=MatchPeriod.FULL_TIME,
                elapsedMinutes=90,
                startedAt="2026-09-08T16:00:00.000Z",
                finishedAt="2026-09-08T17:50:00.000Z",
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-09-08T17:50:00.000Z",
            ),
            Match(
                id="match-203",
                leagueId=league_id,
                homeTeamId="team-harbor",
                awayTeamId="team-redstar",
                matchday=2,
                scheduledAt="2026-09-09T15:00:00.000Z",
                status=MatchStatus.FINISHED,
                homeScore=0,
                awayScore=0,
                currentPeriod=MatchPeriod.FULL_TIME,
                elapsedMinutes=90,
                startedAt="2026-09-09T15:00:00.000Z",
                finishedAt="2026-09-09T16:48:00.000Z",
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-09-09T16:48:00.000Z",
            ),
            # Round 3 (Live In Progress)
            Match(
                id="match-301",
                leagueId=league_id,
                homeTeamId="team-riverside",
                awayTeamId="team-redstar",
                matchday=3,
                scheduledAt="2026-09-14T18:00:00.000Z",
                status=MatchStatus.IN_PROGRESS,
                homeScore=2,
                awayScore=1,
                currentPeriod=MatchPeriod.SECOND_HALF,
                elapsedMinutes=68,
                startedAt="2026-09-14T18:00:00.000Z",
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-09-14T19:20:00.000Z",
                events=[
                    MatchEvent(
                        id="ev-1",
                        matchId="match-301",
                        type=MatchEventType.GOAL_HOME,
                        minute=18,
                        homeScoreAfter=1,
                        awayScoreAfter=0,
                        note="Goal scored by Riverside FC",
                        recordedAt="2026-09-14T18:18:00.000Z",
                    ),
                    MatchEvent(
                        id="ev-2",
                        matchId="match-301",
                        type=MatchEventType.GOAL_AWAY,
                        minute=34,
                        homeScoreAfter=1,
                        awayScoreAfter=1,
                        note="Equalizer by Red Star Athletic",
                        recordedAt="2026-09-14T18:34:00.000Z",
                    ),
                    MatchEvent(
                        id="ev-3",
                        matchId="match-301",
                        type=MatchEventType.GOAL_HOME,
                        minute=57,
                        homeScoreAfter=2,
                        awayScoreAfter=1,
                        note="Go-ahead goal by Riverside FC",
                        recordedAt="2026-09-14T19:12:00.000Z",
                    ),
                ],
            ),
            # Round 3 (Scheduled)
            Match(
                id="match-302",
                leagueId=league_id,
                homeTeamId="team-apex",
                awayTeamId="team-knights",
                matchday=3,
                scheduledAt="2026-09-14T20:00:00.000Z",
                status=MatchStatus.SCHEDULED,
                homeScore=0,
                awayScore=0,
                currentPeriod=MatchPeriod.NOT_STARTED,
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-08-15T10:00:00.000Z",
            ),
            Match(
                id="match-303",
                leagueId=league_id,
                homeTeamId="team-oakwood",
                awayTeamId="team-harbor",
                matchday=3,
                scheduledAt="2026-09-15T15:00:00.000Z",
                status=MatchStatus.SCHEDULED,
                homeScore=0,
                awayScore=0,
                currentPeriod=MatchPeriod.NOT_STARTED,
                createdAt="2026-08-15T10:00:00.000Z",
                updatedAt="2026-08-15T10:00:00.000Z",
            ),
        ]
        for m in initial_matches:
            self.matches[m.id] = m

        self.broadcast_sync("RESET_DATA", None)

    # --- Real-Time Pub/Sub ---
    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self.subscribers.discard(q)

    def broadcast_sync(self, event_type: str, payload: any):
        event = ServiceEvent(type=event_type, payload=payload)
        for q in list(self.subscribers):
            try:
                q.put_nowait(event)
            except Exception:
                pass

    # --- Leagues ---
    def get_leagues(self) -> list[League]:
        return list(self.leagues.values())

    def get_league(self, league_id: str) -> League | None:
        return self.leagues.get(league_id)

    def create_league(self, dto: CreateLeagueDto) -> League:
        now_str = datetime.now(UTC).isoformat()
        league_id = f"league-{int(datetime.now().timestamp() * 1000)}"
        new_league = League(
            id=league_id,
            name=dto.name.strip(),
            season=dto.season.strip(),
            sportType=dto.sportType.strip() if dto.sportType else "Soccer",
            pointsWin=dto.pointsWin if dto.pointsWin is not None else 3,
            pointsDraw=dto.pointsDraw if dto.pointsDraw is not None else 1,
            pointsLoss=dto.pointsLoss if dto.pointsLoss is not None else 0,
            createdAt=now_str,
            updatedAt=now_str,
        )
        self.leagues[new_league.id] = new_league
        return new_league

    # --- Teams ---
    def get_teams(self, league_id: str) -> list[Team]:
        return [t for t in self.teams.values() if t.leagueId == league_id]

    def get_team(self, team_id: str) -> Team | None:
        return self.teams.get(team_id)

    def create_team(self, league_id: str, dto: CreateTeamDto) -> Team:
        clean_name = dto.name.strip()
        # Check duplicate team name in league
        for t in self.teams.values():
            if t.leagueId == league_id and t.name.lower() == clean_name.lower():
                raise ValueError(f"A team named '{clean_name}' already exists in this league.")

        team_id = f"team-{int(datetime.now().timestamp() * 1000)}"
        now_str = datetime.now(UTC).isoformat()
        new_team = Team(
            id=team_id,
            leagueId=league_id,
            name=clean_name,
            shortName=dto.shortName.strip().upper() if dto.shortName else clean_name[:3].upper(),
            logoColor=dto.logoColor or "#10b981",
            logoUrl=dto.logoUrl,
            createdAt=now_str,
        )
        self.teams[new_team.id] = new_team
        self.broadcast_sync("STANDINGS_RECALCULATED", {"leagueId": league_id})
        return new_team

    # --- Matches ---
    def get_matches(
        self, league_id: str, status: str | None = None, matchday: int | None = None
    ) -> list[Match]:
        res = [m for m in self.matches.values() if m.leagueId == league_id]
        if status and status != "ALL":
            res = [m for m in res if m.status.value == status]
        if matchday:
            res = [m for m in res if m.matchday == matchday]

        def sort_key(m: Match):
            status_order = {
                MatchStatus.IN_PROGRESS: 1,
                MatchStatus.SCHEDULED: 2,
                MatchStatus.FINISHED: 3,
                MatchStatus.CANCELLED: 4,
            }
            return (status_order.get(m.status, 9), m.scheduledAt)

        return sorted(res, key=sort_key)

    def get_match(self, match_id: str) -> Match | None:
        return self.matches.get(match_id)

    def create_match(self, league_id: str, dto: CreateMatchDto) -> Match:
        if dto.homeTeamId == dto.awayTeamId:
            raise ValueError("A team cannot play against itself.")

        if dto.homeTeamId not in self.teams:
            raise ValueError(f"Home team '{dto.homeTeamId}' does not exist.")
        if dto.awayTeamId not in self.teams:
            raise ValueError(f"Away team '{dto.awayTeamId}' does not exist.")

        now_str = datetime.now(UTC).isoformat()
        match_id = f"match-{int(datetime.now().timestamp() * 1000)}"
        new_match = Match(
            id=match_id,
            leagueId=league_id,
            homeTeamId=dto.homeTeamId,
            awayTeamId=dto.awayTeamId,
            matchday=max(1, dto.matchday),
            scheduledAt=dto.scheduledAt,
            status=MatchStatus.SCHEDULED,
            homeScore=0,
            awayScore=0,
            currentPeriod=MatchPeriod.NOT_STARTED,
            createdAt=now_str,
            updatedAt=now_str,
            events=[],
        )
        self.matches[new_match.id] = new_match
        self.broadcast_sync("MATCH_CREATED", new_match.model_dump())
        return new_match

    def start_match(self, match_id: str) -> Match:
        match = self.matches.get(match_id)
        if not match:
            raise KeyError(f"Match '{match_id}' not found.")

        if match.status == MatchStatus.FINISHED:
            raise ValueError("Cannot start a match that has already finished.")

        now_str = datetime.now(UTC).isoformat()
        start_event = MatchEvent(
            id=f"ev-{int(datetime.now().timestamp() * 1000)}",
            matchId=match_id,
            type=MatchEventType.MATCH_STARTED,
            minute=0,
            homeScoreAfter=match.homeScore,
            awayScoreAfter=match.awayScore,
            note="Match kicked off",
            recordedAt=now_str,
        )

        match.status = MatchStatus.IN_PROGRESS
        match.currentPeriod = MatchPeriod.FIRST_HALF
        match.elapsedMinutes = 1
        match.startedAt = match.startedAt or now_str
        match.updatedAt = now_str
        match.events.append(start_event)

        self.broadcast_sync("MATCH_UPDATED", match.model_dump())
        return match

    def update_score(self, match_id: str, dto: UpdateScoreDto) -> Match:
        match = self.matches.get(match_id)
        if not match:
            raise KeyError(f"Match '{match_id}' not found.")

        if match.status == MatchStatus.FINISHED:
            raise ValueError("Scores cannot be modified once a match is FINISHED.")

        now_str = datetime.now(UTC).isoformat()
        new_home = max(0, dto.homeScore)
        new_away = max(0, dto.awayScore)

        event_type = MatchEventType.SCORE_ADJUST
        note = dto.note or "Score updated"
        if new_home > match.homeScore:
            event_type = MatchEventType.GOAL_HOME
            note = dto.note or "Home goal"
        elif new_away > match.awayScore:
            event_type = MatchEventType.GOAL_AWAY
            note = dto.note or "Away goal"
        elif dto.period and dto.period != match.currentPeriod:
            event_type = MatchEventType.PERIOD_CHANGE
            note = dto.note or f"Period changed to {dto.period.value}"

        minute = dto.minute if dto.minute is not None else (match.elapsedMinutes or 0)

        event = MatchEvent(
            id=f"ev-{int(datetime.now().timestamp() * 1000)}",
            matchId=match_id,
            type=event_type,
            minute=minute,
            homeScoreAfter=new_home,
            awayScoreAfter=new_away,
            note=note,
            recordedAt=now_str,
        )

        match.homeScore = new_home
        match.awayScore = new_away
        if dto.period:
            match.currentPeriod = dto.period
        if dto.minute is not None:
            match.elapsedMinutes = dto.minute
        match.updatedAt = now_str
        match.events.append(event)

        self.broadcast_sync("MATCH_UPDATED", match.model_dump())
        return match

    def finish_match(self, match_id: str) -> Match:
        match = self.matches.get(match_id)
        if not match:
            raise KeyError(f"Match '{match_id}' not found.")

        if match.status == MatchStatus.FINISHED:
            raise ValueError("Match is already finished.")

        now_str = datetime.now(UTC).isoformat()
        end_event = MatchEvent(
            id=f"ev-{int(datetime.now().timestamp() * 1000)}",
            matchId=match_id,
            type=MatchEventType.MATCH_FINISHED,
            minute=90,
            homeScoreAfter=match.homeScore,
            awayScoreAfter=match.awayScore,
            note=f"Final Whistle: {match.homeScore} - {match.awayScore}",
            recordedAt=now_str,
        )

        match.status = MatchStatus.FINISHED
        match.currentPeriod = MatchPeriod.FULL_TIME
        match.finishedAt = now_str
        match.updatedAt = now_str
        match.events.append(end_event)

        self.broadcast_sync("MATCH_FINISHED", match.model_dump())
        self.broadcast_sync("STANDINGS_RECALCULATED", {"leagueId": match.leagueId})
        return match

    # --- Standings ---
    def get_standings(self, league_id: str, live_provisional: bool = False) -> StandingsResponse:
        league = self.leagues.get(league_id)
        if not league:
            raise KeyError(f"League '{league_id}' not found.")

        teams = self.get_teams(league_id)
        matches = [m for m in self.matches.values() if m.leagueId == league_id]

        standings = calculate_standings(
            teams=teams,
            matches=matches,
            points_win=league.pointsWin,
            points_draw=league.pointsDraw,
            points_loss=league.pointsLoss,
            include_in_progress=live_provisional,
        )

        return StandingsResponse(
            leagueId=league_id,
            leagueName=league.name,
            calculatedAt=datetime.now(UTC).isoformat(),
            isLiveProvisional=live_provisional,
            standings=standings,
        )
