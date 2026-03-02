"""Application configuration."""

import os
from pathlib import Path

basedir = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{basedir / 'courttracker.db'}"
    )

    # API keys
    API_TENNIS_KEY = os.environ.get("API_TENNIS_KEY", "")
    SPORTRADAR_KEY = os.environ.get("SPORTRADAR_KEY", "")

    # Scraping
    SCRAPE_RATE_LIMIT_SECONDS = float(
        os.environ.get("SCRAPE_RATE_LIMIT_SECONDS", "2.0")
    )
    SCRAPE_MAX_RETRIES = int(os.environ.get("SCRAPE_MAX_RETRIES", "3"))
    SCRAPE_USER_AGENT = "CourtTracker/1.0 (tennis-research; contact@courttracker.com)"

    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
