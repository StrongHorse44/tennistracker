"""Database utilities and helpers."""

import logging
from datetime import date

from backend.extensions import db
from backend.models import Player, Tournament, TournamentEdition

logger = logging.getLogger(__name__)


def get_or_create_player(slug: str, defaults: dict) -> tuple[Player, bool]:
    """Get a player by slug, or create if not found.

    Returns (player, created) tuple.
    """
    player = Player.query.filter_by(slug=slug).first()
    if player:
        return player, False

    player = Player(slug=slug, **defaults)
    db.session.add(player)
    db.session.flush()
    return player, True


def get_or_create_tournament(slug: str, defaults: dict) -> tuple[Tournament, bool]:
    """Get a tournament by slug, or create if not found."""
    tournament = Tournament.query.filter_by(slug=slug).first()
    if tournament:
        return tournament, False

    tournament = Tournament(slug=slug, **defaults)
    db.session.add(tournament)
    db.session.flush()
    return tournament, True


def get_or_create_edition(
    tournament_id: int, year: int, defaults: dict
) -> tuple[TournamentEdition, bool]:
    """Get a tournament edition, or create if not found."""
    edition = TournamentEdition.query.filter_by(
        tournament_id=tournament_id, year=year
    ).first()
    if edition:
        return edition, False

    edition = TournamentEdition(
        tournament_id=tournament_id, year=year, **defaults
    )
    db.session.add(edition)
    db.session.flush()
    return edition, True


def refresh_edition_statuses(today: date | None = None) -> int:
    """Update tournament edition statuses based on current date.

    Corrects stale statuses that haven't been updated by scrapers:
    - Editions past their end_date become 'completed'
    - Editions within their date range become 'in_progress'
    - Editions starting within 14 days with entry data become 'entry_list'

    Returns the number of editions updated.
    """
    if today is None:
        today = date.today()

    updated = 0

    # Mark past tournaments as completed
    past_editions = TournamentEdition.query.filter(
        TournamentEdition.end_date < today,
        TournamentEdition.status.notin_(["completed", "cancelled"]),
    ).all()
    for edition in past_editions:
        logger.info("Auto-updating %s %s: %s -> completed", edition.tournament.name, edition.year, edition.status)
        edition.status = "completed"
        updated += 1

    # Mark currently running tournaments as in_progress
    current_editions = TournamentEdition.query.filter(
        TournamentEdition.start_date <= today,
        TournamentEdition.end_date >= today,
        TournamentEdition.status.notin_(["in_progress", "completed", "cancelled"]),
    ).all()
    for edition in current_editions:
        logger.info("Auto-updating %s %s: %s -> in_progress", edition.tournament.name, edition.year, edition.status)
        edition.status = "in_progress"
        updated += 1

    if updated:
        db.session.commit()

    return updated
