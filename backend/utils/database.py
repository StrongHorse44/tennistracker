"""Database utilities and helpers."""

from backend.extensions import db
from backend.models import Player, Tournament, TournamentEdition


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
