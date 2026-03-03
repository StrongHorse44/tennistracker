"""Flask application factory for CourtTracker."""

import logging
import os

from flask import Flask, jsonify

from backend.config import config_by_name
from backend.extensions import db, migrate, cors

logger = logging.getLogger(__name__)


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Register API blueprints
    from backend.api.players import players_bp
    from backend.api.tournaments import tournaments_bp
    from backend.api.predictions import predictions_bp
    from backend.api.map_data import map_bp
    from backend.api.search import search_bp
    from backend.api.health import health_bp

    app.register_blueprint(players_bp, url_prefix="/api/v1/players")
    app.register_blueprint(tournaments_bp, url_prefix="/api/v1/tournaments")
    app.register_blueprint(predictions_bp, url_prefix="/api/v1/predictions")
    app.register_blueprint(map_bp, url_prefix="/api/v1/map")
    app.register_blueprint(search_bp, url_prefix="/api/v1/search")
    app.register_blueprint(health_bp, url_prefix="/api/v1")

    # Register frontend views
    from backend.views.main import views_bp

    app.register_blueprint(views_bp)

    # Auto-refresh tournament edition statuses on first request each day
    _status_refreshed_date = [None]

    @app.before_request
    def _auto_refresh_statuses():
        from datetime import date as _date
        today = _date.today()
        if _status_refreshed_date[0] != today:
            from backend.utils.database import refresh_edition_statuses
            count = refresh_edition_statuses(today)
            _status_refreshed_date[0] = today
            if count:
                logger.info("Auto-refreshed %d tournament edition statuses", count)

    # API overview endpoint
    @app.route("/api/v1/")
    def api_index():
        """API overview with available endpoints."""
        return jsonify({
            "name": "CourtTracker API",
            "version": "1.0",
            "description": "Tennis player tracking and prediction platform",
            "endpoints": {
                "health": "/api/v1/health",
                "players": "/api/v1/players",
                "tournaments": "/api/v1/tournaments",
                "predictions": "/api/v1/predictions",
                "map": "/api/v1/map",
                "search": "/api/v1/search",
            },
        })

    return app
