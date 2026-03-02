"""Scraper configuration — URLs, rate limits, user agents."""

import os

# API keys
API_TENNIS_KEY = os.environ.get("API_TENNIS_KEY", "")
SPORTRADAR_KEY = os.environ.get("SPORTRADAR_KEY", "")

# Rate limits (seconds between requests per domain)
RATE_LIMITS = {
    "tennis-infinity": 3.0,
    "livetennis": 3.0,
    "tennisuptodate": 3.0,
    "atptour": 2.0,
    "wtatennis": 2.0,
    "api-tennis": 1.0,
    "sportradar": 1.0,
    "wikipedia": 1.0,
}

# Base URLs
URLS = {
    "tennis_infinity_entry_lists": "https://tennis-infinity.com/entry-list",
    "livetennis_entry_lists": "https://www.livetennis.io/tournaments/entry-lists/",
    "tennisuptodate_entry_lists": "https://tennisuptodate.com/entry-lists",
    "atp_tour": "https://www.atptour.com",
    "wta_tennis": "https://www.wtatennis.com",
    "api_tennis": "https://api.api-tennis.com/tennis/",
    "sportradar": "https://api.sportradar.us/tennis/trial/v3/en",
    "wikipedia_api": "https://en.wikipedia.org/w/api.php",
}

# Max retries for HTTP requests
MAX_RETRIES = int(os.environ.get("SCRAPE_MAX_RETRIES", "3"))
