"""Shared test fixtures."""

import pytest
from datetime import date

from backend.app import create_app
from backend.extensions import db as _db
from backend.models import Player, Tournament, TournamentEdition, EntryListRecord, Prediction


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app("testing")
    return app


@pytest.fixture(scope="function")
def db(app):
    """Create a fresh database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def sample_player(db):
    """Create a sample player."""
    player = Player(
        first_name="Novak",
        last_name="Djokovic",
        full_name="Novak Djokovic",
        slug="novak-djokovic",
        tour="ATP",
        nationality="SRB",
        nationality_name="Serbia",
        date_of_birth=date(1987, 5, 22),
        current_singles_rank=4,
        plays="Right-Handed",
        backhand="Two-Handed",
        turned_pro_year=2003,
        is_active=True,
    )
    db.session.add(player)
    db.session.commit()
    return player


@pytest.fixture
def sample_tournament(db):
    """Create a sample tournament."""
    tournament = Tournament(
        name="Australian Open",
        slug="australian-open",
        tour="GRAND_SLAM",
        category="Grand Slam",
        surface="Hard",
        city="Melbourne",
        country="AUS",
        country_name="Australia",
        latitude=-37.8217,
        longitude=144.9782,
        winner_points=2000,
        is_mandatory=True,
    )
    db.session.add(tournament)
    db.session.commit()
    return tournament


@pytest.fixture
def sample_edition(db, sample_tournament):
    """Create a sample tournament edition."""
    edition = TournamentEdition(
        tournament_id=sample_tournament.id,
        year=2026,
        start_date=date(2026, 1, 19),
        end_date=date(2026, 2, 1),
        status="completed",
        draw_size=128,
    )
    db.session.add(edition)
    db.session.commit()
    return edition


@pytest.fixture
def sample_entry(db, sample_player, sample_edition):
    """Create a sample entry list record."""
    entry = EntryListRecord(
        player_id=sample_player.id,
        tournament_edition_id=sample_edition.id,
        entry_type="Direct Acceptance",
        entry_rank=4,
        seed=3,
        status="competing",
        source="test",
    )
    db.session.add(entry)
    db.session.commit()
    return entry
