"""Flask application factory for CourtTracker."""

import os

from flask import Flask, jsonify

from backend.config import config_by_name
from backend.extensions import db, migrate, cors


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

    # Register blueprints
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

    @app.route("/")
    def index():
        """Root endpoint with API overview."""
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
