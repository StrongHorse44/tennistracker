"""Map data API endpoints."""

from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from backend.extensions import db
from backend.models import (
    Player,
    Tournament,
    TournamentEdition,
    EntryListRecord,
)

map_bp = Blueprint("map", __name__)


@map_bp.route("/current")
def map_current():
    """Get all players currently competing — for the global map.

    Query params:
        tour: ATP or WTA
    """
    query = (
        db.session.query(Player, EntryListRecord, TournamentEdition, Tournament)
        .join(EntryListRecord, Player.id == EntryListRecord.player_id)
        .join(TournamentEdition, EntryListRecord.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            TournamentEdition.status.in_(["in_progress", "draw_released"]),
            EntryListRecord.status.in_(["competing", "entered", "confirmed"]),
            Player.is_active.is_(True),
        )
    )

    tour = request.args.get("tour")
    if tour:
        query = query.filter(Player.tour == tour.upper())

    results = query.order_by(Player.current_singles_rank.asc().nullslast()).all()

    # Group by tournament location
    locations: dict[int, dict] = {}
    for player, entry, edition, tournament in results:
        tid = tournament.id
        if tid not in locations:
            locations[tid] = {
                "tournament": tournament.to_dict(brief=True),
                "edition_status": edition.status,
                "start_date": edition.start_date.isoformat(),
                "end_date": edition.end_date.isoformat(),
                "players": [],
            }
        locations[tid]["players"].append(
            {
                "player": player.to_dict(brief=True),
                "entry_status": entry.status,
                "seed": entry.seed,
            }
        )

    return jsonify({"locations": list(locations.values())})


@map_bp.route("/week/<date_str>")
def map_week(date_str: str):
    """Where everyone is/will be for a given week.

    Args:
        date_str: ISO date string (YYYY-MM-DD) — the Monday of the week.
    """
    try:
        week_start = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    week_end = week_start + timedelta(days=6)

    # Find editions overlapping with this week
    editions = (
        db.session.query(TournamentEdition, Tournament)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .filter(
            TournamentEdition.start_date <= week_end,
            TournamentEdition.end_date >= week_start,
        )
        .all()
    )

    locations = []
    for edition, tournament in editions:
        # Get entries for this edition
        entries = (
            db.session.query(EntryListRecord, Player)
            .join(Player, EntryListRecord.player_id == Player.id)
            .filter(
                EntryListRecord.tournament_edition_id == edition.id,
                EntryListRecord.status.in_(["entered", "confirmed", "competing"]),
            )
            .order_by(Player.current_singles_rank.asc().nullslast())
            .all()
        )

        locations.append(
            {
                "tournament": tournament.to_dict(brief=True),
                "edition_status": edition.status,
                "start_date": edition.start_date.isoformat(),
                "end_date": edition.end_date.isoformat(),
                "players": [
                    {
                        "player": player.to_dict(brief=True),
                        "entry_status": entry.status,
                        "seed": entry.seed,
                    }
                    for entry, player in entries
                ],
                "player_count": len(entries),
            }
        )

    return jsonify(
        {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "locations": locations,
        }
    )
