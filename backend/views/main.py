"""Frontend view routes for CourtTracker."""

import json
from datetime import date

from flask import Blueprint, render_template, request, abort

from backend.extensions import db
from backend.models import (
    Player,
    Tournament,
    TournamentEdition,
    EntryListRecord,
    HistoricalParticipation,
    Prediction,
    Match,
)

views_bp = Blueprint(
    "views", __name__,
    template_folder="../templates",
    static_folder="../static",
)


@views_bp.route("/")
def dashboard() -> str:
    """Dashboard with world map, stats, and upcoming tournaments."""
    today = date.today()

    # Stats
    total_players = Player.query.filter_by(is_active=True).count()
    total_tournaments = Tournament.query.count()
    upcoming_editions = (
        TournamentEdition.query
        .filter(TournamentEdition.start_date >= today)
        .count()
    )
    total_predictions = Prediction.query.count()

    # Upcoming tournaments (next 8)
    upcoming = (
        db.session.query(TournamentEdition, Tournament)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(TournamentEdition.start_date >= today)
        .order_by(TournamentEdition.start_date)
        .limit(8)
        .all()
    )

    # In-progress tournaments
    in_progress = (
        db.session.query(TournamentEdition, Tournament)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(TournamentEdition.status == "in_progress")
        .order_by(TournamentEdition.start_date)
        .all()
    )

    # Map data: all current/upcoming entries grouped by tournament
    map_entries = (
        db.session.query(Player, EntryListRecord, TournamentEdition, Tournament)
        .join(EntryListRecord, Player.id == EntryListRecord.player_id)
        .join(TournamentEdition, EntryListRecord.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            TournamentEdition.status.in_(["in_progress", "draw_released", "entry_list"]),
            EntryListRecord.status.in_(["competing", "entered", "confirmed"]),
            Player.is_active.is_(True),
        )
        .order_by(Player.current_singles_rank.asc().nullslast())
        .all()
    )

    locations: dict[int, dict] = {}
    for player, entry, edition, tournament in map_entries:
        tid = tournament.id
        if tid not in locations:
            locations[tid] = {
                "tournament": tournament.to_dict(brief=True),
                "edition_status": edition.status,
                "start_date": edition.start_date.isoformat(),
                "end_date": edition.end_date.isoformat(),
                "players": [],
            }
        locations[tid]["players"].append({
            "player": player.to_dict(brief=True),
            "entry_status": entry.status,
            "seed": entry.seed,
        })

    # If no entries yet, show all upcoming tournament locations on the map
    if not locations:
        for edition, tournament in upcoming:
            if tournament.latitude and tournament.longitude:
                locations[tournament.id] = {
                    "tournament": tournament.to_dict(brief=True),
                    "edition_status": edition.status,
                    "start_date": edition.start_date.isoformat(),
                    "end_date": edition.end_date.isoformat(),
                    "players": [],
                    "player_count": 0,
                }

    # Recent predictions
    recent_predictions = (
        db.session.query(Prediction, Player, TournamentEdition, Tournament)
        .join(Player, Prediction.player_id == Player.id)
        .join(TournamentEdition, Prediction.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            TournamentEdition.start_date >= today,
            Prediction.will_enter_probability >= 0.5,
        )
        .order_by(Prediction.will_enter_probability.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "index.html",
        stats={
            "players": total_players,
            "tournaments": total_tournaments,
            "upcoming": upcoming_editions,
            "predictions": total_predictions,
        },
        upcoming=upcoming,
        in_progress=in_progress,
        map_locations=json.dumps(list(locations.values())),
        recent_predictions=recent_predictions,
    )


@views_bp.route("/players")
def players_list() -> str:
    """Players list with filtering."""
    tour = request.args.get("tour", "")
    page = request.args.get("page", 1, type=int)

    query = Player.query.filter_by(is_active=True)

    if tour:
        query = query.filter(Player.tour == tour.upper())

    query = query.order_by(Player.current_singles_rank.asc().nullslast())
    pagination = query.paginate(page=page, per_page=50, error_out=False)

    return render_template(
        "players/list.html",
        players=pagination.items,
        pagination=pagination,
        tour=tour,
    )


@views_bp.route("/players/<slug>")
def player_detail(slug: str) -> str:
    """Player profile page."""
    player = Player.query.filter_by(slug=slug).first_or_404()
    today = date.today()
    year = request.args.get("year", today.year, type=int)

    # Current tournament
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

    # Build timeline
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

    # Merge into timeline
    timeline_map: dict[int, dict] = {}

    for entry, edition, tournament in entries:
        key = edition.id
        if key not in timeline_map:
            timeline_map[key] = _make_timeline_event(tournament, edition)
        timeline_map[key]["entry"] = entry
        timeline_map[key]["tracking_status"] = "confirmed"

    for hp, edition, tournament in history:
        key = edition.id
        if key not in timeline_map:
            timeline_map[key] = _make_timeline_event(tournament, edition)
        timeline_map[key]["historical"] = hp
        if timeline_map[key]["tracking_status"] == "unknown":
            timeline_map[key]["tracking_status"] = "historical_only"

    for pred, edition, tournament in predictions:
        key = edition.id
        if key not in timeline_map:
            timeline_map[key] = _make_timeline_event(tournament, edition)
        timeline_map[key]["prediction"] = pred
        prob = float(pred.will_enter_probability)
        if timeline_map[key]["tracking_status"] == "unknown":
            if prob >= 0.7:
                timeline_map[key]["tracking_status"] = "predicted_likely"
            elif prob >= 0.4:
                timeline_map[key]["tracking_status"] = "predicted_possible"
            else:
                timeline_map[key]["tracking_status"] = "predicted_unlikely"

    timeline = sorted(timeline_map.values(), key=lambda x: x["start_date"] or "")

    # Recent matches
    recent_matches = (
        db.session.query(Match, TournamentEdition, Tournament)
        .join(TournamentEdition, Match.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            db.or_(Match.player1_id == player.id, Match.player2_id == player.id),
            Match.status == "completed",
        )
        .order_by(Match.scheduled_date.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "players/detail.html",
        player=player,
        current=current,
        timeline=timeline,
        recent_matches=recent_matches,
        year=year,
    )


@views_bp.route("/tournaments")
def tournaments_list() -> str:
    """Tournaments list with filtering."""
    tour = request.args.get("tour", "")
    surface = request.args.get("surface", "")
    page = request.args.get("page", 1, type=int)

    query = Tournament.query

    if tour:
        query = query.filter(Tournament.tour == tour.upper())
    if surface:
        query = query.filter(Tournament.surface == surface)

    query = query.order_by(Tournament.name)
    pagination = query.paginate(page=page, per_page=50, error_out=False)

    # Get upcoming editions for each tournament
    today = date.today()
    tournament_ids = [t.id for t in pagination.items]
    upcoming_editions = {}
    if tournament_ids:
        editions = (
            TournamentEdition.query
            .filter(
                TournamentEdition.tournament_id.in_(tournament_ids),
                TournamentEdition.start_date >= today,
            )
            .order_by(TournamentEdition.start_date)
            .all()
        )
        for e in editions:
            if e.tournament_id not in upcoming_editions:
                upcoming_editions[e.tournament_id] = e

    return render_template(
        "tournaments/list.html",
        tournaments=pagination.items,
        pagination=pagination,
        tour=tour,
        surface=surface,
        upcoming_editions=upcoming_editions,
    )


@views_bp.route("/tournaments/<slug>")
def tournament_detail(slug: str) -> str:
    """Tournament detail page with editions."""
    tournament = Tournament.query.filter_by(slug=slug).first_or_404()

    editions = (
        TournamentEdition.query
        .filter_by(tournament_id=tournament.id)
        .order_by(TournamentEdition.year.desc())
        .all()
    )

    return render_template(
        "tournaments/detail.html",
        tournament=tournament,
        editions=editions,
    )


@views_bp.route("/tournaments/<slug>/<int:year>")
def tournament_edition(slug: str, year: int) -> str:
    """Tournament edition page with field and predictions."""
    tournament = Tournament.query.filter_by(slug=slug).first_or_404()
    edition = TournamentEdition.query.filter_by(
        tournament_id=tournament.id, year=year,
    ).first_or_404()

    # Confirmed entries
    entries = (
        db.session.query(EntryListRecord, Player)
        .join(Player, EntryListRecord.player_id == Player.id)
        .filter(EntryListRecord.tournament_edition_id == edition.id)
        .order_by(Player.current_singles_rank.asc().nullslast())
        .all()
    )

    # Predictions
    entered_player_ids = {e.player_id for e, _ in entries}
    predicted = (
        db.session.query(Prediction, Player)
        .join(Player, Prediction.player_id == Player.id)
        .filter(
            Prediction.tournament_edition_id == edition.id,
            Prediction.will_enter_probability >= 0.3,
            ~Prediction.player_id.in_(entered_player_ids) if entered_player_ids else db.true(),
        )
        .order_by(Prediction.will_enter_probability.desc())
        .all()
    )

    # Matches
    matches = (
        db.session.query(Match)
        .filter(Match.tournament_edition_id == edition.id)
        .order_by(Match.scheduled_date.desc(), Match.round)
        .all()
    )

    return render_template(
        "tournaments/edition.html",
        tournament=tournament,
        edition=edition,
        entries=entries,
        predicted=predicted,
        matches=matches,
    )


@views_bp.route("/search")
def search() -> str:
    """Search results page."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return render_template("search.html", q=q, players=[], tournaments=[], error="Enter at least 2 characters.")

    pattern = f"%{q}%"

    players = (
        Player.query
        .filter(db.or_(
            Player.full_name.ilike(pattern),
            Player.slug.ilike(pattern),
        ))
        .order_by(Player.current_singles_rank.asc().nullslast())
        .limit(20)
        .all()
    )

    tournaments = (
        Tournament.query
        .filter(db.or_(
            Tournament.name.ilike(pattern),
            Tournament.city.ilike(pattern),
        ))
        .order_by(Tournament.name)
        .limit(20)
        .all()
    )

    return render_template("search.html", q=q, players=players, tournaments=tournaments, error=None)


def _make_timeline_event(tournament: Tournament, edition: TournamentEdition) -> dict:
    """Build a timeline event dict for a tournament edition."""
    return {
        "tournament": tournament,
        "edition": edition,
        "start_date": edition.start_date.isoformat() if edition.start_date else None,
        "end_date": edition.end_date.isoformat() if edition.end_date else None,
        "edition_status": edition.status,
        "entry": None,
        "historical": None,
        "prediction": None,
        "tracking_status": "unknown",
    }
