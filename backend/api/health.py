"""Health check and system endpoints."""

from datetime import datetime

from flask import Blueprint, jsonify

from backend.extensions import db
from backend.models import ScrapeLog

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    """Health check endpoint."""
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return jsonify(
        {
            "status": "ok" if db_status == "ok" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
        }
    )


@health_bp.route("/scrape/status")
def scrape_status():
    """Return latest scrape run statuses."""
    latest_runs = (
        db.session.query(ScrapeLog)
        .order_by(ScrapeLog.started_at.desc())
        .limit(20)
        .all()
    )

    return jsonify(
        {
            "runs": [
                {
                    "id": run.id,
                    "source": run.source,
                    "scrape_type": run.scrape_type,
                    "status": run.status,
                    "records_found": run.records_found,
                    "records_created": run.records_created,
                    "records_updated": run.records_updated,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    "duration_seconds": run.duration_seconds,
                }
                for run in latest_runs
            ]
        }
    )
