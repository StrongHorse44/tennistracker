"""Player API endpoints."""

from datetime import date

from flask import Blueprint, jsonify, request, abort

from backend.extensions import db
from backend.models import (
    Player,
    EntryListRecord,
    TournamentEdition,
    Tournament,
    HistoricalParticipation,
    Prediction,
)

players_bp = Blueprint("players", __name__)


@players_bp.route("")
def list_players():
    """List players with optional filtering.

    Query params:
        tour: ATP or WTA
        rank_min: minimum ranking
        rank_max: maximum ranking
        active: true/false
        page: page number (default 1)
        per_page: results per page (default 50)
    """
    query = Player.query

    # Filters
    tour = request.args.get("tour")
    if tour:
        query = query.filter(Player.tour == tour.upper())

    rank_min = request.args.get("rank_min", type=int)
    if rank_min is not None:
        query = query.filter(Player.current_singles_rank >= rank_min)

    rank_max = request.args.get("rank_max", type=int)
    if rank_max is not None:
        query = query.filter(Player.current_singles_rank <= rank_max)

    active = request.args.get("active")
    if active is not None:
        query = query.filter(Player.is_active == (active.lower() == "true"))

    # Sorting
    query = query.order_by(Player.current_singles_rank.asc().nullslast())

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "players": [p.to_dict(brief=True) for p in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }
    )


@players_bp.route("/<slug>")
def get_player(slug: str):
    """Get a player by slug."""
    player = Player.query.filter_by(slug=slug).first_or_404()
    return jsonify(player.to_dict())


@players_bp.route("/<slug>/timeline")
def get_player_timeline(slug: str):
    """Get a player's full year timeline — entries + predictions.

    Query params:
        year: year to show (default: current year)
    """
    player = Player.query.filter_by(slug=slug).first_or_404()
    year = request.args.get("year", date.today().year, type=int)

    # Get all entries for the year
    entries = (
        db.session.query(EntryListRecord, TournamentEdition, Tournament)
        .join(TournamentEdition, EntryListRecord.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            EntryListRecord.player_id == player.id,
            TournamentEdition.year == year,
        )
        .order_by(TournamentEdition.start_date)
        .all()
    )

    # Get historical results for the year
    history = (
        db.session.query(HistoricalParticipation, TournamentEdition, Tournament)
        .join(TournamentEdition, HistoricalParticipation.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            HistoricalParticipation.player_id == player.id,
            TournamentEdition.year == year,
        )
        .order_by(TournamentEdition.start_date)
        .all()
    )

    # Get predictions for the year
    predictions = (
        db.session.query(Prediction, TournamentEdition, Tournament)
        .join(TournamentEdition, Prediction.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            Prediction.player_id == player.id,
            TournamentEdition.year == year,
        )
        .order_by(TournamentEdition.start_date)
        .all()
    )

    # Build unified timeline
    timeline_map: dict[int, dict] = {}

    for entry, edition, tournament in entries:
        key = edition.id
        if key not in timeline_map:
            timeline_map[key] = _make_timeline_event(tournament, edition)
        timeline_map[key]["entry"] = entry.to_dict()
        timeline_map[key]["tracking_status"] = "confirmed"

    for hp, edition, tournament in history:
        key = edition.id
        if key not in timeline_map:
            timeline_map[key] = _make_timeline_event(tournament, edition)
        timeline_map[key]["historical_result"] = hp.to_dict()
        if timeline_map[key]["tracking_status"] == "unknown":
            timeline_map[key]["tracking_status"] = "historical_only"

    for pred, edition, tournament in predictions:
        key = edition.id
        if key not in timeline_map:
            timeline_map[key] = _make_timeline_event(tournament, edition)
        timeline_map[key]["prediction"] = pred.to_dict()
        prob = float(pred.will_enter_probability)
        if timeline_map[key]["tracking_status"] == "unknown":
            if prob >= 0.7:
                timeline_map[key]["tracking_status"] = "predicted_likely"
            elif prob >= 0.4:
                timeline_map[key]["tracking_status"] = "predicted_possible"
            else:
                timeline_map[key]["tracking_status"] = "predicted_unlikely"

    # Sort by start_date
    timeline = sorted(timeline_map.values(), key=lambda x: x["start_date"] or "")

    return jsonify(
        {
            "player": player.to_dict(brief=True),
            "year": year,
            "timeline": timeline,
        }
    )


@players_bp.route("/<slug>/location")
def get_player_location(slug: str):
    """Get a player's current location + next confirmed entry."""
    player = Player.query.filter_by(slug=slug).first_or_404()
    today = date.today()

    # Current tournament (in-progress)
    current = (
        db.session.query(EntryListRecord, TournamentEdition, Tournament)
        .join(TournamentEdition, EntryListRecord.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            EntryListRecord.player_id == player.id,
            EntryListRecord.status.in_(["competing", "entered", "confirmed"]),
            TournamentEdition.status.in_(["in_progress", "draw_released"]),
        )
        .first()
    )

    # Upcoming confirmed entries
    upcoming_confirmed = (
        db.session.query(EntryListRecord, TournamentEdition, Tournament)
        .join(TournamentEdition, EntryListRecord.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            EntryListRecord.player_id == player.id,
            EntryListRecord.status.in_(["entered", "confirmed"]),
            TournamentEdition.start_date > today,
        )
        .order_by(TournamentEdition.start_date)
        .all()
    )

    # Upcoming predicted entries
    upcoming_predicted = (
        db.session.query(Prediction, TournamentEdition, Tournament)
        .join(TournamentEdition, Prediction.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            Prediction.player_id == player.id,
            Prediction.will_enter_probability >= 0.4,
            TournamentEdition.start_date > today,
        )
        .order_by(TournamentEdition.start_date)
        .all()
    )

    # Exclude tournaments that already have confirmed entries
    confirmed_edition_ids = {e.tournament_edition_id for e, _, _ in upcoming_confirmed}
    upcoming_predicted = [
        (pred, ed, t)
        for pred, ed, t in upcoming_predicted
        if ed.id not in confirmed_edition_ids
    ]

    result = {
        "player": player.to_dict(),
        "current": None,
        "upcoming_confirmed": [],
        "upcoming_predicted": [],
    }

    if current:
        entry, edition, tournament = current
        result["current"] = {
            "tournament": tournament.name,
            "city": tournament.city,
            "country": tournament.country_name,
            "latitude": float(tournament.latitude) if tournament.latitude else None,
            "longitude": float(tournament.longitude) if tournament.longitude else None,
            "surface": tournament.surface,
            "category": tournament.category,
            "start_date": edition.start_date.isoformat(),
            "end_date": edition.end_date.isoformat(),
            "status": entry.status,
            "seed": entry.seed,
        }

    for entry, edition, tournament in upcoming_confirmed:
        result["upcoming_confirmed"].append(
            {
                "tournament": tournament.name,
                "city": tournament.city,
                "country": tournament.country_name,
                "latitude": float(tournament.latitude) if tournament.latitude else None,
                "longitude": float(tournament.longitude) if tournament.longitude else None,
                "surface": tournament.surface,
                "category": tournament.category,
                "start_date": edition.start_date.isoformat(),
                "end_date": edition.end_date.isoformat(),
                "entry_type": entry.entry_type,
                "tracking_status": "confirmed",
            }
        )

    for pred, edition, tournament in upcoming_predicted:
        result["upcoming_predicted"].append(
            {
                "tournament": tournament.name,
                "city": tournament.city,
                "country": tournament.country_name,
                "latitude": float(tournament.latitude) if tournament.latitude else None,
                "longitude": float(tournament.longitude) if tournament.longitude else None,
                "surface": tournament.surface,
                "category": tournament.category,
                "start_date": edition.start_date.isoformat(),
                "end_date": edition.end_date.isoformat(),
                "probability": float(pred.will_enter_probability),
                "prediction_label": pred.prediction_label,
            }
        )

    return jsonify(result)


@players_bp.route("/<slug>/predictions")
def get_player_predictions(slug: str):
    """Get all predictions for a player."""
    player = Player.query.filter_by(slug=slug).first_or_404()

    predictions = (
        db.session.query(Prediction, TournamentEdition, Tournament)
        .join(TournamentEdition, Prediction.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(Prediction.player_id == player.id)
        .order_by(TournamentEdition.start_date)
        .all()
    )

    return jsonify(
        {
            "player": player.to_dict(brief=True),
            "predictions": [
                {
                    **pred.to_dict(),
                    "tournament": tournament.to_dict(brief=True),
                    "edition": {
                        "start_date": edition.start_date.isoformat(),
                        "end_date": edition.end_date.isoformat(),
                        "year": edition.year,
                    },
                }
                for pred, edition, tournament in predictions
            ],
        }
    )


@players_bp.route("/<slug>/history")
def get_player_history(slug: str):
    """Get a player's historical participation records.

    Query params:
        limit: max results (default 50)
    """
    player = Player.query.filter_by(slug=slug).first_or_404()
    limit = min(request.args.get("limit", 50, type=int), 200)

    history = (
        db.session.query(HistoricalParticipation, TournamentEdition, Tournament)
        .join(TournamentEdition, HistoricalParticipation.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(HistoricalParticipation.player_id == player.id)
        .order_by(TournamentEdition.start_date.desc())
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "player": player.to_dict(brief=True),
            "history": [
                {
                    **hp.to_dict(),
                    "tournament": tournament.to_dict(brief=True),
                    "edition": {
                        "start_date": edition.start_date.isoformat(),
                        "end_date": edition.end_date.isoformat(),
                        "year": edition.year,
                    },
                }
                for hp, edition, tournament in history
            ],
        }
    )


def _make_timeline_event(tournament: Tournament, edition: TournamentEdition) -> dict:
    """Build a timeline event dict for a tournament edition."""
    return {
        "tournament": tournament.to_dict(brief=True),
        "start_date": edition.start_date.isoformat() if edition.start_date else None,
        "end_date": edition.end_date.isoformat() if edition.end_date else None,
        "edition_status": edition.status,
        "entry": None,
        "historical_result": None,
        "prediction": None,
        "tracking_status": "unknown",
    }
