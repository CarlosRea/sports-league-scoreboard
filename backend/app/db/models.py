from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

from app.models.auth import User, UserRole
from app.models.league import League
from app.models.match import Match, MatchEvent, MatchEventType, MatchPeriod, MatchStatus
from app.models.team import Team

Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"

    username = Column(String(64), primary_key=True, index=True)
    role = Column(String(32), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    def to_pydantic(self) -> User:
        return User(
            username=self.username,
            role=UserRole(self.role),
            hashed_password=self.hashed_password,
            is_active=self.is_active,
        )


class LeagueDB(Base):
    __tablename__ = "leagues"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    season = Column(String(64), nullable=False)
    sport_type = Column(String(64), nullable=False, default="Soccer")
    points_win = Column(Integer, nullable=False, default=3)
    points_draw = Column(Integer, nullable=False, default=1)
    points_loss = Column(Integer, nullable=False, default=0)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    teams = relationship("TeamDB", back_populates="league", cascade="all, delete-orphan")
    matches = relationship("MatchDB", back_populates="league", cascade="all, delete-orphan")

    def to_pydantic(self) -> League:
        return League(
            id=self.id,
            name=self.name,
            season=self.season,
            sportType=self.sport_type,
            pointsWin=self.points_win,
            pointsDraw=self.points_draw,
            pointsLoss=self.points_loss,
            createdAt=self.created_at,
            updatedAt=self.updated_at,
        )


class TeamDB(Base):
    __tablename__ = "teams"

    id = Column(String(64), primary_key=True, index=True)
    league_id = Column(
        String(64), ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(128), nullable=False)
    short_name = Column(String(16), nullable=False)
    logo_color = Column(String(32), nullable=False, default="#10b981")
    logo_url = Column(String(255), nullable=True)
    created_at = Column(String(64), nullable=False)

    league = relationship("LeagueDB", back_populates="teams")

    def to_pydantic(self) -> Team:
        return Team(
            id=self.id,
            leagueId=self.league_id,
            name=self.name,
            shortName=self.short_name,
            logoColor=self.logo_color,
            logoUrl=self.logo_url,
            createdAt=self.created_at,
        )


class MatchDB(Base):
    __tablename__ = "matches"

    id = Column(String(64), primary_key=True, index=True)
    league_id = Column(
        String(64), ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    home_team_id = Column(
        String(64), ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    away_team_id = Column(
        String(64), ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    matchday = Column(Integer, nullable=False, default=1)
    scheduled_at = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="SCHEDULED")
    home_score = Column(Integer, nullable=False, default=0)
    away_score = Column(Integer, nullable=False, default=0)
    current_period = Column(String(32), nullable=False, default="Not Started")
    elapsed_minutes = Column(Integer, nullable=True)
    started_at = Column(String(64), nullable=True)
    finished_at = Column(String(64), nullable=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    league = relationship("LeagueDB", back_populates="matches")
    events = relationship(
        "MatchEventDB",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchEventDB.recorded_at",
        lazy="selectin",
    )

    def to_pydantic(self) -> Match:
        return Match(
            id=self.id,
            leagueId=self.league_id,
            homeTeamId=self.home_team_id,
            awayTeamId=self.away_team_id,
            matchday=self.matchday,
            scheduledAt=self.scheduled_at,
            status=MatchStatus(self.status),
            homeScore=self.home_score,
            awayScore=self.away_score,
            currentPeriod=MatchPeriod(self.current_period),
            elapsedMinutes=self.elapsed_minutes,
            startedAt=self.started_at,
            finishedAt=self.finished_at,
            createdAt=self.created_at,
            updatedAt=self.updated_at,
            events=[e.to_pydantic() for e in (self.events or [])],
        )


class MatchEventDB(Base):
    __tablename__ = "match_events"

    id = Column(String(64), primary_key=True, index=True)
    match_id = Column(
        String(64), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = Column(String(32), nullable=False)
    minute = Column(Integer, nullable=False)
    home_score_after = Column(Integer, nullable=False)
    away_score_after = Column(Integer, nullable=False)
    note = Column(String(255), nullable=True)
    recorded_at = Column(String(64), nullable=False)

    match = relationship("MatchDB", back_populates="events")

    def to_pydantic(self) -> MatchEvent:
        return MatchEvent(
            id=self.id,
            matchId=self.match_id,
            type=MatchEventType(self.type),
            minute=self.minute,
            homeScoreAfter=self.home_score_after,
            awayScoreAfter=self.away_score_after,
            note=self.note,
            recordedAt=self.recorded_at,
        )
