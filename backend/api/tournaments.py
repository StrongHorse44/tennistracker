"""Tournament API endpoints."""

from datetime import date

from flask import Blueprint, jsonify, request

from backend.extensions import db
from backend.models import (
    Tournament,
    TournamentEdition,
    EntryListRecord,
    Player,
    Prediction,
)

tournaments_bp = Blueprint("tournaments", __name__)


@tournaments_bp.route("")
def list_tournaments():
    """List tournaments with optional filtering.

    Query params:
        tour: ATP, WTA, GRAND_SLAM, MIXED
        surface: Hard, Clay, Grass
        category: e.g. "ATP 1000", "Grand Slam"
        page, per_page
    """
    query = Tournament.query

    tour = request.args.get("tour")
    if tour:
        query = query.filter(Tournament.tour == tour.upper())

    surface = request.args.get("surface")
    if surface:
        query = query.filter(Tournament.surface == surface.capitalize())

    category = request.args.get("category")
    if category:
        query = query.filter(Tournament.category == category)

    query = query.order_by(Tournament.name)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "tournaments": [t.to_dict(brief=True) for t in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }
    )


@tournaments_bp.route("/<slug>")
def get_tournament(slug: str):
    """Get a tournament by slug, including its editions."""
    tournament = Tournament.query.filter_by(slug=slug).first_or_404()

    editions = (
        TournamentEdition.query.filter_by(tournament_id=tournament.id)
        .order_by(TournamentEdition.year.desc())
        .all()
    )

    data = tournament.to_dict()
    data["editions"] = [e.to_dict() for e in editions]
    return jsonify(data)


@tournaments_bp.route("/<slug>/editions/<int:year>")
def get_tournament_edition(slug: str, year: int):
    """Get a specific year's edition of a tournament."""
    tournament = Tournament.query.filter_by(slug=slug).first_or_404()
    edition = TournamentEdition.query.filter_by(
        tournament_id=tournament.id, year=year
    ).first_or_404()

    data = edition.to_dict()
    data["tournament"] = tournament.to_dict()
    return jsonify(data)


@tournaments_bp.route("/<slug>/editions/<int:year>/field")
def get_tournament_field(slug: str, year: int):
    """Get the entry list + predictions for who will enter.

    Returns confirmed entries and predicted entries sorted by ranking.
    """
    tournament = Tournament.query.filter_by(slug=slug).first_or_404()
    edition = TournamentEdition.query.filter_by(
        tournament_id=tournament.id, year=year
    ).first_or_404()

    # Confirmed entries
    entries = (
        db.session.query(EntryListRecord, Player)
        .join(Player, EntryListRecord.player_id == Player.id)
        .filter(EntryListRecord.tournament_edition_id == edition.id)
        .order_by(Player.current_singles_rank.asc().nullslast())
        .all()
    )

    # Predictions for players not yet on the entry list
    entered_player_ids = {e.player_id for e, _ in entries}
    predictions = (
        db.session.query(Prediction, Player)
        .join(Player, Prediction.player_id == Player.id)
        .filter(
            Prediction.tournament_edition_id == edition.id,
            Prediction.will_enter_probability >= 0.3,
            ~Prediction.player_id.in_(entered_player_ids) if entered_player_ids else True,
        )
        .order_by(Prediction.will_enter_probability.desc())
        .all()
    )

    return jsonify(
        {
            "tournament": tournament.to_dict(brief=True),
            "edition": edition.to_dict(),
            "confirmed_entries": [
                {
                    "player": player.to_dict(brief=True),
                    "entry": entry.to_dict(),
                }
                for entry, player in entries
            ],
            "predicted_entries": [
                {
                    "player": player.to_dict(brief=True),
                    "prediction": pred.to_dict(),
                }
                for pred, player in predictions
            ],
            "field_size": len(entries),
        }
    )
