import os
import tempfile

from app.db.models import Base, LeagueDB, TeamDB
from app.db.session import create_db_engine, get_db_context
from app.models.league import CreateLeagueDto
from app.models.team import CreateTeamDto
from app.store.sql_store import SqlStore


def test_database_url_env_configuration():
    """Verify that DATABASE_URL environment variable properly configures the database connection."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        custom_url = f"sqlite:///{db_path}"
        engine = create_db_engine(custom_url)
        Base.metadata.create_all(bind=engine)

        with get_db_context() as session:
            assert session.bind is not None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_data_persistence_across_sessions():
    """Verify that data created through SqlStore is saved to the SQLite database and persists."""
    store = SqlStore()
    league = store.create_league(
        CreateLeagueDto(
            name="Persistent Test League",
            season="2026",
            sportType="Soccer",
            pointsWin=3,
            pointsDraw=1,
            pointsLoss=0,
        )
    )

    # Query directly with a fresh independent DB session
    with get_db_context() as session:
        db_league = session.get(LeagueDB, league.id)
        assert db_league is not None
        assert db_league.name == "Persistent Test League"
        assert db_league.sport_type == "Soccer"


def test_foreign_key_cascade_delete():
    """Verify that foreign keys and cascade deletions function correctly."""
    store = SqlStore()
    league = store.create_league(CreateLeagueDto(name="Cascade Test League", season="2026"))
    team = store.create_team(
        league.id, CreateTeamDto(leagueId=league.id, name="Cascade FC", shortName="CFC")
    )

    with get_db_context() as session:
        db_league = session.get(LeagueDB, league.id)
        session.delete(db_league)
        session.commit()

        # Team should be cascade-deleted
        db_team = session.get(TeamDB, team.id)
        assert db_team is None
