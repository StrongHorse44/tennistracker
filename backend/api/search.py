"""Search API endpoint."""

from flask import Blueprint, jsonify, request

from backend.models import Player, Tournament

search_bp = Blueprint("search", __name__)


@search_bp.route("")
def search():
    """Search players and tournaments.

    Query params:
        q: search query string (required)
        type: "player", "tournament", or omit for both
        limit: max results per type (default 10)
    """
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"error": "Query must be at least 2 characters."}), 400

    search_type = request.args.get("type")
    limit = min(request.args.get("limit", 10, type=int), 50)
    pattern = f"%{q}%"

    results: dict = {}

    if search_type in (None, "player"):
        players = (
            Player.query.filter(
                Player.is_active.is_(True),
                Player.full_name.ilike(pattern),
            )
            .order_by(Player.current_singles_rank.asc().nullslast())
            .limit(limit)
            .all()
        )
        results["players"] = [p.to_dict(brief=True) for p in players]

    if search_type in (None, "tournament"):
        tournaments = (
            Tournament.query.filter(
                Tournament.name.ilike(pattern)
                | Tournament.city.ilike(pattern)
            )
            .order_by(Tournament.name)
            .limit(limit)
            .all()
        )
        results["tournaments"] = [t.to_dict(brief=True) for t in tournaments]

    return jsonify(results)
