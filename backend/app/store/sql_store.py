import asyncio
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.auth.security import hash_password
from app.db.models import Base, LeagueDB, MatchDB, MatchEventDB, TeamDB, UserDB
from app.db.session import engine, get_db_context
from app.models.auth import User, UserRole
from app.models.common import ServiceEvent
from app.models.league import CreateLeagueDto, League
from app.models.match import (
    CreateMatchDto,
    Match,
    MatchEventType,
    MatchPeriod,
    MatchStatus,
    UpdateScoreDto,
)
from app.models.standings import StandingsResponse
from app.models.team import CreateTeamDto, Team
from app.store.engine import calculate_standings

# Pre-computed bcrypt hashes for fast seed resets
ADMIN_PASSWORD_HASH = hash_password("AdminPassword123!")
SCOREKEEPER_PASSWORD_HASH = hash_password("RefereePassword123!")


class UsersFacade:
    """Provides dictionary-like interface for user lookup backwards compatibility."""

    def __init__(self, store: "SqlStore"):
        self._store = store

    def get(self, username: str) -> User | None:
        return self._store.get_user(username)

    def __getitem__(self, username: str) -> User:
        user = self._store.get_user(username)
        if not user:
            raise KeyError(f"User '{username}' not found.")
        return user


class SqlStore:
    """
    Production database-backed store implementation using SQLAlchemy.
    Completely database-agnostic (supports SQLite, PostgreSQL, MySQL, etc.)
    with automatic schema initialization and initial seed data.
    """

    def __init__(self):
        self.subscribers: set[asyncio.Queue] = set()
        self.users = UsersFacade(self)
        self.init_db()

    def init_db(self):
        """Create tables if they don't exist and seed if empty."""
        Base.metadata.create_all(bind=engine)
        with get_db_context() as session:
            existing_league = session.scalar(select(LeagueDB).limit(1))
            if not existing_league:
                self._seed_data(session)

    def reset_data(self):
        """Reset the database to default seed data in an isolated transaction."""
        Base.metadata.create_all(bind=engine)
        with get_db_context() as session:
            session.execute(delete(MatchEventDB))
            session.execute(delete(MatchDB))
            session.execute(delete(TeamDB))
            session.execute(delete(LeagueDB))
            session.execute(delete(UserDB))
            session.commit()
            self._seed_data(session)

        self.broadcast_sync("RESET_DATA", None)

    def _seed_data(self, session):
        """Seed default admin users, league, teams, and sample fixtures."""
        # 1. Users
        admin_user = UserDB(
            username="admin",
            role=UserRole.ADMIN.value,
            hashed_password=ADMIN_PASSWORD_HASH,
            is_active=True,
        )
        scorekeeper_user = UserDB(
            username="scorekeeper",
            role=UserRole.SCOREKEEPER.value,
            hashed_password=SCOREKEEPER_PASSWORD_HASH,
            is_active=True,
        )
        session.add_all([admin_user, scorekeeper_user])

        # 2. League
        league_id = "league-metro-2026"
        league = LeagueDB(
            id=league_id,
            name="Metropolitan Amateur Premier League",
            season="2026 / 2027",
            sport_type="Soccer",
            points_win=3,
            points_draw=1,
            points_loss=0,
            created_at="2026-08-01T00:00:00.000Z",
            updated_at="2026-08-01T00:00:00.000Z",
        )
        session.add(league)
        session.flush()

        # 3. Teams
        initial_teams = [
            TeamDB(
                id="team-riverside",
                league_id=league_id,
                name="Riverside FC",
                short_name="RFC",
                logo_color="#10b981",
                created_at="2026-08-01T01:00:00.000Z",
            ),
            TeamDB(
                id="team-apex",
                league_id=league_id,
                name="Apex United",
                short_name="APX",
                logo_color="#0284c7",
                created_at="2026-08-01T01:05:00.000Z",
            ),
            TeamDB(
                id="team-redstar",
                league_id=league_id,
                name="Red Star Athletic",
                short_name="RSA",
                logo_color="#ef4444",
                created_at="2026-08-01T01:10:00.000Z",
            ),
            TeamDB(
                id="team-oakwood",
                league_id=league_id,
                name="Oakwood Rovers",
                short_name="OAK",
                logo_color="#f59e0b",
                created_at="2026-08-01T01:15:00.000Z",
            ),
            TeamDB(
                id="team-harbor",
                league_id=league_id,
                name="Harbor City SC",
                short_name="HBC",
                logo_color="#6366f1",
                created_at="2026-08-01T01:20:00.000Z",
            ),
            TeamDB(
                id="team-knights",
                league_id=league_id,
                name="Northern Knights",
                short_name="NOK",
                logo_color="#a855f7",
                created_at="2026-08-01T01:25:00.000Z",
            ),
        ]
        session.add_all(initial_teams)
        session.flush()

        # 4. Matches & Events
        m101 = MatchDB(
            id="match-101",
            league_id=league_id,
            home_team_id="team-riverside",
            away_team_id="team-oakwood",
            matchday=1,
            scheduled_at="2026-09-01T14:00:00.000Z",
            status=MatchStatus.FINISHED.value,
            home_score=3,
            away_score=1,
            current_period=MatchPeriod.FULL_TIME.value,
            elapsed_minutes=90,
            started_at="2026-09-01T14:00:00.000Z",
            finished_at="2026-09-01T15:50:00.000Z",
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-09-01T15:50:00.000Z",
        )
        m102 = MatchDB(
            id="match-102",
            league_id=league_id,
            home_team_id="team-apex",
            away_team_id="team-harbor",
            matchday=1,
            scheduled_at="2026-09-01T16:00:00.000Z",
            status=MatchStatus.FINISHED.value,
            home_score=2,
            away_score=2,
            current_period=MatchPeriod.FULL_TIME.value,
            elapsed_minutes=90,
            started_at="2026-09-01T16:00:00.000Z",
            finished_at="2026-09-01T17:55:00.000Z",
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-09-01T17:55:00.000Z",
        )
        m103 = MatchDB(
            id="match-103",
            league_id=league_id,
            home_team_id="team-redstar",
            away_team_id="team-knights",
            matchday=1,
            scheduled_at="2026-09-02T15:00:00.000Z",
            status=MatchStatus.FINISHED.value,
            home_score=1,
            away_score=0,
            current_period=MatchPeriod.FULL_TIME.value,
            elapsed_minutes=90,
            started_at="2026-09-02T15:00:00.000Z",
            finished_at="2026-09-02T16:50:00.000Z",
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-09-02T16:50:00.000Z",
        )
        m201 = MatchDB(
            id="match-201",
            league_id=league_id,
            home_team_id="team-oakwood",
            away_team_id="team-apex",
            matchday=2,
            scheduled_at="2026-09-08T14:00:00.000Z",
            status=MatchStatus.FINISHED.value,
            home_score=2,
            away_score=1,
            current_period=MatchPeriod.FULL_TIME.value,
            elapsed_minutes=90,
            started_at="2026-09-08T14:00:00.000Z",
            finished_at="2026-09-08T15:52:00.000Z",
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-09-08T15:52:00.000Z",
        )
        m202 = MatchDB(
            id="match-202",
            league_id=league_id,
            home_team_id="team-knights",
            away_team_id="team-riverside",
            matchday=2,
            scheduled_at="2026-09-08T16:00:00.000Z",
            status=MatchStatus.FINISHED.value,
            home_score=1,
            away_score=4,
            current_period=MatchPeriod.FULL_TIME.value,
            elapsed_minutes=90,
            started_at="2026-09-08T16:00:00.000Z",
            finished_at="2026-09-08T17:50:00.000Z",
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-09-08T17:50:00.000Z",
        )
        m203 = MatchDB(
            id="match-203",
            league_id=league_id,
            home_team_id="team-harbor",
            away_team_id="team-redstar",
            matchday=2,
            scheduled_at="2026-09-09T15:00:00.000Z",
            status=MatchStatus.FINISHED.value,
            home_score=0,
            away_score=0,
            current_period=MatchPeriod.FULL_TIME.value,
            elapsed_minutes=90,
            started_at="2026-09-09T15:00:00.000Z",
            finished_at="2026-09-09T16:48:00.000Z",
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-09-09T16:48:00.000Z",
        )
        m301 = MatchDB(
            id="match-301",
            league_id=league_id,
            home_team_id="team-riverside",
            away_team_id="team-redstar",
            matchday=3,
            scheduled_at="2026-09-14T18:00:00.000Z",
            status=MatchStatus.IN_PROGRESS.value,
            home_score=2,
            away_score=1,
            current_period=MatchPeriod.SECOND_HALF.value,
            elapsed_minutes=68,
            started_at="2026-09-14T18:00:00.000Z",
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-09-14T19:20:00.000Z",
        )
        m302 = MatchDB(
            id="match-302",
            league_id=league_id,
            home_team_id="team-apex",
            away_team_id="team-knights",
            matchday=3,
            scheduled_at="2026-09-14T20:00:00.000Z",
            status=MatchStatus.SCHEDULED.value,
            home_score=0,
            away_score=0,
            current_period=MatchPeriod.NOT_STARTED.value,
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-08-15T10:00:00.000Z",
        )
        m303 = MatchDB(
            id="match-303",
            league_id=league_id,
            home_team_id="team-oakwood",
            away_team_id="team-harbor",
            matchday=3,
            scheduled_at="2026-09-15T15:00:00.000Z",
            status=MatchStatus.SCHEDULED.value,
            home_score=0,
            away_score=0,
            current_period=MatchPeriod.NOT_STARTED.value,
            created_at="2026-08-15T10:00:00.000Z",
            updated_at="2026-08-15T10:00:00.000Z",
        )
        session.add_all([m101, m102, m103, m201, m202, m203, m301, m302, m303])
        session.flush()

        # Events for live match-301
        ev1 = MatchEventDB(
            id="ev-1",
            match_id="match-301",
            type=MatchEventType.GOAL_HOME.value,
            minute=18,
            home_score_after=1,
            away_score_after=0,
            note="Goal scored by Riverside FC",
            recorded_at="2026-09-14T18:18:00.000Z",
        )
        ev2 = MatchEventDB(
            id="ev-2",
            match_id="match-301",
            type=MatchEventType.GOAL_AWAY.value,
            minute=34,
            home_score_after=1,
            away_score_after=1,
            note="Equalizer by Red Star Athletic",
            recorded_at="2026-09-14T18:34:00.000Z",
        )
        ev3 = MatchEventDB(
            id="ev-3",
            match_id="match-301",
            type=MatchEventType.GOAL_HOME.value,
            minute=57,
            home_score_after=2,
            away_score_after=1,
            note="Go-ahead goal by Riverside FC",
            recorded_at="2026-09-14T19:12:00.000Z",
        )
        session.add_all([ev1, ev2, ev3])
        session.flush()

        session.commit()

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

    async def broadcast(self, event: ServiceEvent):
        for q in list(self.subscribers):
            try:
                await q.put(event)
            except Exception:
                pass

    # --- Users ---
    def get_user(self, username: str) -> User | None:
        with get_db_context() as session:
            db_user = session.get(UserDB, username)
            return db_user.to_pydantic() if db_user else None

    # --- Leagues ---
    def get_leagues(self) -> list[League]:
        with get_db_context() as session:
            db_leagues = session.scalars(select(LeagueDB).order_by(LeagueDB.created_at)).all()
            return [lg.to_pydantic() for lg in db_leagues]

    def get_league(self, league_id: str) -> League | None:
        with get_db_context() as session:
            db_league = session.get(LeagueDB, league_id)
            return db_league.to_pydantic() if db_league else None

    def create_league(self, dto: CreateLeagueDto) -> League:
        now_str = datetime.now(UTC).isoformat()
        league_id = f"league-{int(datetime.now().timestamp() * 1000)}"
        new_db = LeagueDB(
            id=league_id,
            name=dto.name.strip(),
            season=dto.season.strip(),
            sport_type=dto.sportType.strip() if dto.sportType else "Soccer",
            points_win=dto.pointsWin if dto.pointsWin is not None else 3,
            points_draw=dto.pointsDraw if dto.pointsDraw is not None else 1,
            points_loss=dto.pointsLoss if dto.pointsLoss is not None else 0,
            created_at=now_str,
            updated_at=now_str,
        )
        with get_db_context() as session:
            session.add(new_db)
            session.commit()
            return new_db.to_pydantic()

    # --- Teams ---
    def get_teams(self, league_id: str) -> list[Team]:
        with get_db_context() as session:
            stmt = select(TeamDB).where(TeamDB.league_id == league_id).order_by(TeamDB.created_at)
            db_teams = session.scalars(stmt).all()
            return [t.to_pydantic() for t in db_teams]

    def get_team(self, team_id: str) -> Team | None:
        with get_db_context() as session:
            db_team = session.get(TeamDB, team_id)
            return db_team.to_pydantic() if db_team else None

    def create_team(self, league_id: str, dto: CreateTeamDto) -> Team:
        clean_name = dto.name.strip()
        with get_db_context() as session:
            # Check duplicate team name in league (case-insensitive)
            duplicate_stmt = select(TeamDB).where(
                TeamDB.league_id == league_id, func.lower(TeamDB.name) == clean_name.lower()
            )
            if session.scalar(duplicate_stmt):
                raise ValueError(f"A team named '{clean_name}' already exists in this league.")

            team_id = f"team-{int(datetime.now().timestamp() * 1000)}"
            now_str = datetime.now(UTC).isoformat()
            new_team = TeamDB(
                id=team_id,
                league_id=league_id,
                name=clean_name,
                short_name=dto.shortName.strip().upper()
                if dto.shortName
                else clean_name[:3].upper(),
                logo_color=dto.logoColor or "#10b981",
                logo_url=dto.logoUrl,
                created_at=now_str,
            )
            session.add(new_team)
            session.commit()
            created_pydantic = new_team.to_pydantic()

        self.broadcast_sync("STANDINGS_RECALCULATED", {"leagueId": league_id})
        return created_pydantic

    # --- Matches ---
    def get_matches(
        self, league_id: str, status: str | None = None, matchday: int | None = None
    ) -> list[Match]:
        with get_db_context() as session:
            stmt = (
                select(MatchDB)
                .options(selectinload(MatchDB.events))
                .where(MatchDB.league_id == league_id)
            )
            if status and status != "ALL":
                stmt = stmt.where(MatchDB.status == status)
            if matchday:
                stmt = stmt.where(MatchDB.matchday == matchday)

            db_matches = session.scalars(stmt).all()
            pydantic_matches = [m.to_pydantic() for m in db_matches]

        def sort_key(m: Match):
            status_order = {
                MatchStatus.IN_PROGRESS: 1,
                MatchStatus.SCHEDULED: 2,
                MatchStatus.FINISHED: 3,
                MatchStatus.CANCELLED: 4,
            }
            return (status_order.get(m.status, 9), m.scheduledAt)

        return sorted(pydantic_matches, key=sort_key)

    def get_match(self, match_id: str) -> Match | None:
        with get_db_context() as session:
            stmt = (
                select(MatchDB).options(selectinload(MatchDB.events)).where(MatchDB.id == match_id)
            )
            db_match = session.scalar(stmt)
            return db_match.to_pydantic() if db_match else None

    def create_match(self, league_id: str, dto: CreateMatchDto) -> Match:
        if dto.homeTeamId == dto.awayTeamId:
            raise ValueError("A team cannot play against itself.")

        with get_db_context() as session:
            home_team = session.get(TeamDB, dto.homeTeamId)
            if not home_team:
                raise ValueError(f"Home team '{dto.homeTeamId}' does not exist.")
            away_team = session.get(TeamDB, dto.awayTeamId)
            if not away_team:
                raise ValueError(f"Away team '{dto.awayTeamId}' does not exist.")

            now_str = datetime.now(UTC).isoformat()
            match_id = f"match-{int(datetime.now().timestamp() * 1000)}"
            new_match = MatchDB(
                id=match_id,
                league_id=league_id,
                home_team_id=dto.homeTeamId,
                away_team_id=dto.awayTeamId,
                matchday=max(1, dto.matchday),
                scheduled_at=dto.scheduledAt,
                status=MatchStatus.SCHEDULED.value,
                home_score=0,
                away_score=0,
                current_period=MatchPeriod.NOT_STARTED.value,
                created_at=now_str,
                updated_at=now_str,
            )
            session.add(new_match)
            session.commit()
            created_pydantic = new_match.to_pydantic()

        self.broadcast_sync("MATCH_CREATED", created_pydantic.model_dump())
        return created_pydantic

    def start_match(self, match_id: str) -> Match:
        with get_db_context() as session:
            stmt = (
                select(MatchDB).options(selectinload(MatchDB.events)).where(MatchDB.id == match_id)
            )
            match = session.scalar(stmt)
            if not match:
                raise KeyError(f"Match '{match_id}' not found.")

            if match.status == MatchStatus.FINISHED.value:
                raise ValueError("Cannot start a match that has already finished.")

            now_str = datetime.now(UTC).isoformat()
            start_event = MatchEventDB(
                id=f"ev-{int(datetime.now().timestamp() * 1000)}",
                match_id=match_id,
                type=MatchEventType.MATCH_STARTED.value,
                minute=0,
                home_score_after=match.home_score,
                away_score_after=match.away_score,
                note="Match kicked off",
                recorded_at=now_str,
            )

            match.status = MatchStatus.IN_PROGRESS.value
            match.current_period = MatchPeriod.FIRST_HALF.value
            match.elapsed_minutes = 1
            match.started_at = match.started_at or now_str
            match.updated_at = now_str
            match.events.append(start_event)
            session.commit()
            session.refresh(match)

            updated_pydantic = match.to_pydantic()

        self.broadcast_sync("MATCH_UPDATED", updated_pydantic.model_dump())
        return updated_pydantic

    def update_score(self, match_id: str, dto: UpdateScoreDto) -> Match:
        with get_db_context() as session:
            stmt = (
                select(MatchDB).options(selectinload(MatchDB.events)).where(MatchDB.id == match_id)
            )
            match = session.scalar(stmt)
            if not match:
                raise KeyError(f"Match '{match_id}' not found.")

            if match.status == MatchStatus.FINISHED.value:
                raise ValueError("Scores cannot be modified once a match is FINISHED.")

            now_str = datetime.now(UTC).isoformat()
            new_home = max(0, dto.homeScore)
            new_away = max(0, dto.awayScore)

            event_type = MatchEventType.SCORE_ADJUST.value
            note = dto.note or "Score updated"
            if new_home > match.home_score:
                event_type = MatchEventType.GOAL_HOME.value
                note = dto.note or "Home goal"
            elif new_away > match.away_score:
                event_type = MatchEventType.GOAL_AWAY.value
                note = dto.note or "Away goal"
            elif dto.period and dto.period.value != match.current_period:
                event_type = MatchEventType.PERIOD_CHANGE.value
                note = dto.note or f"Period changed to {dto.period.value}"

            minute = dto.minute if dto.minute is not None else (match.elapsed_minutes or 0)

            event = MatchEventDB(
                id=f"ev-{int(datetime.now().timestamp() * 1000)}",
                match_id=match_id,
                type=event_type,
                minute=minute,
                home_score_after=new_home,
                away_score_after=new_away,
                note=note,
                recorded_at=now_str,
            )

            match.home_score = new_home
            match.away_score = new_away
            if dto.period:
                match.current_period = dto.period.value
            if dto.minute is not None:
                match.elapsed_minutes = dto.minute
            match.updated_at = now_str

            match.events.append(event)
            session.commit()
            session.refresh(match)
            updated_pydantic = match.to_pydantic()

        self.broadcast_sync("MATCH_UPDATED", updated_pydantic.model_dump())
        return updated_pydantic

    def finish_match(self, match_id: str) -> Match:
        with get_db_context() as session:
            stmt = (
                select(MatchDB).options(selectinload(MatchDB.events)).where(MatchDB.id == match_id)
            )
            match = session.scalar(stmt)
            if not match:
                raise KeyError(f"Match '{match_id}' not found.")

            if match.status == MatchStatus.FINISHED.value:
                raise ValueError("Match is already finished.")

            now_str = datetime.now(UTC).isoformat()
            end_event = MatchEventDB(
                id=f"ev-{int(datetime.now().timestamp() * 1000)}",
                match_id=match_id,
                type=MatchEventType.MATCH_FINISHED.value,
                minute=90,
                home_score_after=match.home_score,
                away_score_after=match.away_score,
                note=f"Final Whistle: {match.home_score} - {match.away_score}",
                recorded_at=now_str,
            )

            match.status = MatchStatus.FINISHED.value
            match.current_period = MatchPeriod.FULL_TIME.value
            match.finished_at = now_str
            match.updated_at = now_str
            league_id = match.league_id

            match.events.append(end_event)
            session.commit()
            session.refresh(match)
            updated_pydantic = match.to_pydantic()

        self.broadcast_sync("MATCH_FINISHED", updated_pydantic.model_dump())
        self.broadcast_sync("STANDINGS_RECALCULATED", {"leagueId": league_id})
        return updated_pydantic

    # --- Standings ---
    def get_standings(self, league_id: str, live_provisional: bool = False) -> StandingsResponse:
        with get_db_context() as session:
            league = session.get(LeagueDB, league_id)
            if not league:
                raise KeyError(f"League '{league_id}' not found.")

            teams = [
                t.to_pydantic()
                for t in session.scalars(select(TeamDB).where(TeamDB.league_id == league_id)).all()
            ]
            matches = [
                m.to_pydantic()
                for m in session.scalars(
                    select(MatchDB).where(MatchDB.league_id == league_id)
                ).all()
            ]

        standings = calculate_standings(
            teams=teams,
            matches=matches,
            points_win=league.points_win,
            points_draw=league.points_draw,
            points_loss=league.points_loss,
            include_in_progress=live_provisional,
        )

        return StandingsResponse(
            leagueId=league_id,
            leagueName=league.name,
            calculatedAt=datetime.now(UTC).isoformat(),
            isLiveProvisional=live_provisional,
            standings=standings,
        )


# Global singleton store instance
store = SqlStore()
