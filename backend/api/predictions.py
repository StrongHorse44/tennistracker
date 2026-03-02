"""Prediction API endpoints."""

from datetime import date

from flask import Blueprint, jsonify, request

from backend.extensions import db
from backend.models import (
    Prediction,
    TournamentEdition,
    Tournament,
    Player,
)

predictions_bp = Blueprint("predictions", __name__)


@predictions_bp.route("/upcoming")
def upcoming_predictions():
    """Get all predictions for upcoming tournaments.

    Query params:
        tour: ATP or WTA
        min_probability: minimum probability threshold (default 0.5)
        limit: max results (default 100)
    """
    today = date.today()
    min_prob = request.args.get("min_probability", 0.5, type=float)
    limit = min(request.args.get("limit", 100, type=int), 500)

    query = (
        db.session.query(Prediction, TournamentEdition, Tournament, Player)
        .join(TournamentEdition, Prediction.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .join(Player, Prediction.player_id == Player.id)
        .filter(
            TournamentEdition.start_date > today,
            Prediction.will_enter_probability >= min_prob,
        )
    )

    tour = request.args.get("tour")
    if tour:
        query = query.filter(Player.tour == tour.upper())

    results = (
        query.order_by(
            TournamentEdition.start_date,
            Prediction.will_enter_probability.desc(),
        )
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "predictions": [
                {
                    "player": player.to_dict(brief=True),
                    "tournament": tournament.to_dict(brief=True),
                    "edition": {
                        "start_date": edition.start_date.isoformat(),
                        "end_date": edition.end_date.isoformat(),
                        "year": edition.year,
                    },
                    "probability": float(pred.will_enter_probability),
                    "confidence_level": pred.confidence_level,
                    "prediction_label": pred.prediction_label,
                }
                for pred, edition, tournament, player in results
            ]
        }
    )


@predictions_bp.route("/changes")
def prediction_changes():
    """Get recent prediction changes (alerts feed).

    Query params:
        days: how far back to look (default 7)
        limit: max results (default 50)
    """
    from datetime import timedelta

    days = request.args.get("days", 7, type=int)
    limit = min(request.args.get("limit", 50, type=int), 200)
    cutoff = date.today() - timedelta(days=days)

    results = (
        db.session.query(Prediction, TournamentEdition, Tournament, Player)
        .join(TournamentEdition, Prediction.tournament_edition_id == TournamentEdition.id)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .join(Player, Prediction.player_id == Player.id)
        .filter(Prediction.predicted_at >= cutoff)
        .order_by(Prediction.predicted_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "changes": [
                {
                    "player": player.to_dict(brief=True),
                    "tournament": tournament.to_dict(brief=True),
                    "probability": float(pred.will_enter_probability),
                    "prediction_label": pred.prediction_label,
                    "predicted_at": pred.predicted_at.isoformat() if pred.predicted_at else None,
                }
                for pred, edition, tournament, player in results
            ]
        }
    )
