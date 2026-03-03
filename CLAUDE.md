# CLAUDE.md — CourtTracker

## What is this project?

CourtTracker is a tennis player tracking and prediction platform — the "flight tracker for professional tennis." It tracks where top ATP and WTA players are competing, where they're going next, and predicts future tournament participation using ML models trained on historical patterns, entry list data, and ranking obligations.

## Quick reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Seed database (creates SQLite DB at courttracker.db)
python scripts/seed_database.py

# Run Flask dev server
flask --app backend.app run
```

## Tech stack

- **Python 3.11+** with type hints throughout
- **Flask 3.1** with Blueprints for API organization
- **SQLAlchemy 2.0** ORM with Flask-SQLAlchemy / Flask-Migrate / Alembic
- **SQLite** for development, **PostgreSQL** for production
- **BeautifulSoup4** + **requests** for scraping
- **scikit-learn** GradientBoostingClassifier for predictions
- **pytest** for testing with pytest-flask

## Project structure

```
backend/
├── app.py                  # Flask app factory (create_app)
├── config.py               # Config classes (Development/Testing/Production)
├── extensions.py           # Flask extension instances (db, migrate, cors)
├── models.py               # All SQLAlchemy models (11 tables)
├── api/                    # REST API blueprints
│   ├── players.py          # /api/v1/players/*
│   ├── tournaments.py      # /api/v1/tournaments/*
│   ├── predictions.py      # /api/v1/predictions/*
│   ├── map_data.py         # /api/v1/map/*
│   ├── search.py           # /api/v1/search
│   └── health.py           # /api/v1/health, /api/v1/scrape/status
├── scrapers/
│   ├── base.py             # BaseScraper ABC (retry, rate-limit, logging)
│   ├── config.py           # URLs, rate limits, API keys
│   ├── api/                # API integrations (api_tennis.py)
│   ├── entry_lists/        # HTML scrapers (tennis_infinity.py)
│   ├── utils/
│   │   ├── name_matcher.py # PlayerNameMatcher (fuzzy cross-source matching)
│   │   ├── geo.py          # haversine_distance, same_continent
│   │   └── rate_limiter.py # Thread-safe per-domain rate limiter
│   ├── official/           # ATP/WTA official site scrapers (planned)
│   ├── historical/         # Wikipedia season scrapers (planned)
│   └── pipeline/           # Orchestrator, scheduler (planned)
├── prediction/
│   ├── features.py         # PredictionFeatures dataclass, FEATURE_COLUMNS
│   └── model.py            # TournamentEntryPredictor (sklearn wrapper)
├── services/               # Business logic layer (planned)
└── utils/
    └── database.py         # get_or_create helpers, refresh_edition_statuses

data/seed/                  # Seed JSON files (tournaments, players, calendar)
scripts/seed_database.py    # Database seeder
tests/                      # Test suite
```

## Database models

All models are in `backend/models.py`. The 11 tables:

| Model | Table | Purpose |
|---|---|---|
| `Player` | `players` | ATP/WTA player profiles, rankings, bio |
| `Tournament` | `tournaments` | Recurring tournament metadata, location, points |
| `TournamentEdition` | `tournament_editions` | Specific year instance (dates, status, draw) |
| `EntryListRecord` | `entry_list_records` | Player entries (the core tracking data) |
| `HistoricalParticipation` | `historical_participation` | Past results (ML training data) |
| `Prediction` | `predictions` | ML-predicted entry probabilities |
| `Match` | `matches` | Individual match results and live scores |
| `PlayerSurfaceStats` | `player_surface_stats` | Aggregated surface win rates by year |
| `RankingHistory` | `ranking_history` | Weekly ranking snapshots |
| `ScrapeLog` | `scrape_log` | Scraper run audit trail |
| `Alert` | `alerts` | User notification subscriptions |

Key relationships:
- `Tournament` 1→N `TournamentEdition` (one per year)
- `TournamentEdition` 1→N `EntryListRecord` (the entry list)
- `Player` 1→N `EntryListRecord` (entries across tournaments)
- `EntryListRecord` has two FKs to `Player` (`player_id` and `replaced_by_player_id`) — the `entry_records` relationship uses `foreign_keys=[EntryListRecord.player_id]`

### Status enums

These string values are used in status columns (not enforced via Python Enum in SQLAlchemy, but defined as PyEnum classes for reference):

- **EditionStatus**: `upcoming`, `entry_list`, `draw_released`, `in_progress`, `completed`, `cancelled`
- **EntryStatus**: `entered`, `confirmed`, `withdrawn`, `replaced`, `competing`, `eliminated`, `champion`
- **EntryType**: `Direct Acceptance`, `Wild Card`, `Qualifier`, `Special Exempt`, `Protected Ranking`, `Alternate`, `Unknown`
- **MatchStatus**: `scheduled`, `live`, `completed`, `walkover`, `retired`, `defaulted`, `suspended`, `cancelled`

### Auto-status refresh

Tournament edition statuses are automatically corrected based on the current date via `refresh_edition_statuses()` in `backend/utils/database.py`. This runs once per day on the first request (via a `before_request` hook in `backend/app.py`):

- Editions past their `end_date` → `completed` (unless already `completed` or `cancelled`)
- Editions within `start_date..end_date` → `in_progress` (unless already `in_progress`, `completed`, or `cancelled`)

This prevents stale statuses when scrapers haven't run. The seed data provides initial statuses, but the auto-refresh ensures they stay accurate over time.

### Serialization

Every model has a `to_dict()` method. `Player.to_dict(brief=True)` and `Tournament.to_dict(brief=True)` return minimal fields for list views; `brief=False` (default) returns full detail.

## API design

All endpoints are under `/api/v1/`. Blueprints are registered in `backend/app.py`.

| Blueprint | Prefix | File |
|---|---|---|
| `players_bp` | `/api/v1/players` | `backend/api/players.py` |
| `tournaments_bp` | `/api/v1/tournaments` | `backend/api/tournaments.py` |
| `predictions_bp` | `/api/v1/predictions` | `backend/api/predictions.py` |
| `map_bp` | `/api/v1/map` | `backend/api/map_data.py` |
| `search_bp` | `/api/v1/search` | `backend/api/search.py` |
| `health_bp` | `/api/v1` | `backend/api/health.py` |

Common patterns:
- List endpoints support `page` and `per_page` query params (max 200) via `query.paginate()`
- Detail endpoints use slug-based lookups with `.first_or_404()`
- Filtering is via query parameters (e.g., `?tour=ATP&surface=Clay`)
- All responses are JSON

### Key endpoint shapes

**Player location** (`GET /api/v1/players/:slug/location`): Returns `current` (tournament where player is competing), `upcoming_confirmed` (entry list entries), and `upcoming_predicted` (ML predictions for tournaments without confirmed entry).

**Tournament field** (`GET /api/v1/tournaments/:slug/editions/:year/field`): Returns `confirmed_entries` and `predicted_entries` — players not yet on the entry list but predicted to enter.

**Player timeline** (`GET /api/v1/players/:slug/timeline?year=2026`): Returns unified timeline merging entries, historical results, and predictions. Each event has a `tracking_status`: `confirmed`, `predicted_likely`, `predicted_possible`, `predicted_unlikely`, or `historical_only`.

## Scrapers

All scrapers extend `BaseScraper` (`backend/scrapers/base.py`):
- Automatic rate limiting via `_throttle()` (minimum `rate_limit_seconds` between requests)
- Retry with exponential backoff (`2^attempt` seconds)
- Every run creates a `ScrapeLog` entry via `_start_log` / `_complete_log` / `_fail_log`
- `User-Agent: CourtTracker/1.0 (tennis-research; contact@courttracker.com)`
- Rate limits per domain are in `backend/scrapers/config.py` (2-3 seconds for scrape sites, 1 second for APIs)

**Player name matching** (`backend/scrapers/utils/name_matcher.py`): Player name matching MUST go through `PlayerNameMatcher` — never assume a raw name from a scraper is correct. It handles `LAST, First` format, parenthetical removal `(WC)` / `[1]`, accent normalization, and fuzzy matching via `SequenceMatcher`. Default threshold is 0.85. Pass `nationality` when available for disambiguation.

## Prediction engine

- Features are defined in `backend/prediction/features.py` as a `PredictionFeatures` dataclass (25 features)
- `FEATURE_COLUMNS` list defines the canonical ordering
- Model is `TournamentEntryPredictor` in `backend/prediction/model.py` wrapping `GradientBoostingClassifier`
- Training uses `TimeSeriesSplit` (5 folds) — never random split, since data is temporal
- Predictions are probabilities 0→1; labels are derived: `likely` (>=0.7), `possible` (0.4-0.7), `unlikely` (<0.4)
- Trained models saved as `.joblib` in `data/models/`

## Testing

```bash
pytest tests/ -v          # Run all tests
pytest tests/test_api/ -v # Run API tests only
```

- Framework: **pytest** with **pytest-flask**
- Test config: `TestingConfig` uses `sqlite:///:memory:`
- Fixtures in `tests/conftest.py`: `app`, `db` (per-function fresh DB), `client`, `sample_player`, `sample_tournament`, `sample_edition`, `sample_entry`
- The `db` fixture creates all tables, yields, then rolls back and drops — each test gets a clean database
- Scraper tests use saved HTML fixtures (don't hit live sites). Test files go in `tests/fixtures/`
- Name matcher tests use hardcoded player lists, not DB

Test layout mirrors source:
```
tests/test_api/          # API endpoint tests
tests/test_name_matcher/ # PlayerNameMatcher tests
tests/test_prediction/   # Feature + model tests
tests/test_scrapers/     # Geo utils, scraper logic tests
```

## Coding conventions

- **Type hints** on all function signatures
- **Docstrings** on all public functions/classes
- Use `@dataclass` for data transfer objects
- Use Python `Enum` for status field definitions (reference only — DB stores strings)
- All dates stored and processed in **UTC**; timezone conversion only in frontend
- Player slugs are URL-friendly: `novak-djokovic`, `australian-open`
- Logging: `INFO` for normal operations, `WARNING` for recoverable errors, `ERROR` for failures
- Never commit API keys — use `.env` file (see `.env.example`)
- Configuration via environment variables, loaded through `backend/config.py`

## Commit convention

- `feat:` new features
- `fix:` bug fixes
- `data:` seed data or data pipeline changes
- `scrape:` scraper changes
- `pred:` prediction engine changes
- `api:` API endpoint changes
- `ui:` frontend changes
- `test:` test-only changes
- `refactor:` code restructuring without behavior change

## Adding a new API endpoint

1. Add route function in the appropriate `backend/api/*.py` blueprint file
2. If a new blueprint, register it in `backend/app.py` `create_app()`
3. Use `db.session.query()` for joins across multiple tables, `Model.query` for simple single-table queries
4. Return JSON via `jsonify()`; use `to_dict(brief=True)` for list items
5. Support pagination for list endpoints: `query.paginate(page=page, per_page=per_page, error_out=False)`
6. Add tests in `tests/test_api/`

## Adding a new scraper

1. Create a new class extending `BaseScraper` in the appropriate subdirectory
2. Set `source_name` and `rate_limit_seconds` in `__init__`
3. Implement `scrape(**kwargs) -> list[dict]` returning normalized records
4. Add rate limit config to `backend/scrapers/config.py` `RATE_LIMITS`
5. Use `PlayerNameMatcher.match()` for all player name resolution — never insert raw names
6. All runs must log to `scrape_log` (handled automatically by `BaseScraper.run()`)
7. Test with saved HTML fixtures, never live HTTP in tests

## Adding a new model

1. Add the SQLAlchemy model class to `backend/models.py`
2. Add a `to_dict()` method for serialization
3. Add relationships with explicit `foreign_keys` if there are multiple FK paths to the same table
4. Add appropriate indexes via `__table_args__`
5. Run `flask db migrate -m "description"` and `flask db upgrade` for Alembic migrations
6. Add fixtures to `tests/conftest.py` if needed for testing

## Seed data

Seed files in `data/seed/`:
- `tournaments.json` — 20 tournaments (4 Grand Slams, 9 Masters, etc.) with geocoded locations
- `players_atp_top100.json` — ATP top 20 players
- `players_wta_top100.json` — WTA top 15 players
- `calendar_2026.json` — 21 tournament edition records for the 2026 season
- `entry_lists.json` — Entry lists for 4 tournaments (Australian Open, Qatar Open, Dubai, Indian Wells)
- `matches.json` — Match results for 3 completed tournaments (Australian Open, Qatar Open, Dubai)
- `predictions.json` — ML predictions for 4 upcoming tournaments (Miami, Monte Carlo, Roland Garros, Wimbledon)
- `historical_results.json` — Historical participation records for 2 tournaments

Run `python scripts/seed_database.py` to load. The script is idempotent:
- Skips existing records by slug/unique key
- Updates existing edition statuses, entry statuses, and match results if seed data has changed
- Cleans up duplicate matches on startup (from previous seeds that lacked dedup)
- Match seeding checks for existing `(edition, player1, player2, round)` before inserting

## Environment setup

Copy `.env.example` to `.env` and fill in API keys:
```
API_TENNIS_KEY=...     # From https://api-tennis.com/
SPORTRADAR_KEY=...     # From https://developer.sportradar.com/
```

The app runs without API keys (scraping features will fail, but API + seed data work).
