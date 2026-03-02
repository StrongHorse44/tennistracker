# CourtTracker

Tennis player location and schedule intelligence platform — the "flight tracker for professional tennis."

Tracks where top ATP and WTA players are, where they're going next, and predicts future tournament participation using historical patterns, entry list data, and ranking obligations.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database with tournaments, players, and 2026 calendar
python scripts/seed_database.py

# Run the Flask development server
flask --app backend.app run

# Run tests
pytest tests/ -v
```

## Project Structure

- `backend/` — Flask API, SQLAlchemy models, scrapers, prediction engine
- `backend/api/` — REST API endpoints (players, tournaments, predictions, map, search)
- `backend/scrapers/` — Data ingestion from entry list sites and APIs
- `backend/prediction/` — ML-based tournament entry prediction (GradientBoosting)
- `data/seed/` — Seed data (tournaments, players, calendar)
- `scripts/` — Database seeding and management scripts
- `tests/` — pytest test suite

## API Endpoints

```
GET /api/v1/players                              # List players
GET /api/v1/players/:slug                        # Player detail
GET /api/v1/players/:slug/timeline               # Year timeline
GET /api/v1/players/:slug/location               # Current location
GET /api/v1/players/:slug/predictions            # Predictions
GET /api/v1/players/:slug/history                # Historical results
GET /api/v1/tournaments                          # List tournaments
GET /api/v1/tournaments/:slug                    # Tournament detail
GET /api/v1/tournaments/:slug/editions/:year     # Specific edition
GET /api/v1/tournaments/:slug/editions/:year/field  # Entry list + predictions
GET /api/v1/map/current                          # Global map data
GET /api/v1/map/week/:date                       # Week view
GET /api/v1/predictions/upcoming                 # Upcoming predictions
GET /api/v1/predictions/changes                  # Recent changes
GET /api/v1/search?q=                            # Search players/tournaments
GET /api/v1/health                               # Health check
```

## Tech Stack

- **Backend**: Python 3.13 + Flask + SQLAlchemy
- **Database**: PostgreSQL (production) / SQLite (development)
- **Scraping**: BeautifulSoup4 + requests
- **Prediction**: scikit-learn GradientBoostingClassifier
- **Frontend**: React + Leaflet.js + Tailwind CSS (planned)
