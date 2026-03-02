"""Seed the database with initial tournament, player, and calendar data."""

import json
import sys
from datetime import date
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.app import create_app
from backend.extensions import db
from backend.models import Player, Tournament, TournamentEdition

SEED_DIR = project_root / "data" / "seed"


def load_json(filename: str) -> list[dict]:
    """Load a JSON file from the seed directory."""
    path = SEED_DIR / filename
    with open(path) as f:
        return json.load(f)


def seed_tournaments() -> dict[str, Tournament]:
    """Seed tournaments table. Returns slug -> Tournament mapping."""
    data = load_json("tournaments.json")
    tournament_map = {}

    for item in data:
        slug = item["slug"]
        existing = Tournament.query.filter_by(slug=slug).first()
        if existing:
            print(f"  Tournament already exists: {slug}")
            tournament_map[slug] = existing
            continue

        tournament = Tournament(
            name=item["name"],
            slug=slug,
            tour=item["tour"],
            category=item["category"],
            surface=item["surface"],
            indoor_outdoor=item.get("indoor_outdoor"),
            draw_size=item.get("draw_size"),
            city=item["city"],
            country=item["country"],
            country_name=item.get("country_name"),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            timezone=item.get("timezone"),
            venue_name=item.get("venue_name"),
            winner_points=item.get("winner_points"),
            finalist_points=item.get("finalist_points"),
            semifinalist_points=item.get("semifinalist_points"),
            quarterfinalist_points=item.get("quarterfinalist_points"),
            is_mandatory=item.get("is_mandatory", False),
        )
        db.session.add(tournament)
        tournament_map[slug] = tournament
        print(f"  Added tournament: {item['name']}")

    db.session.flush()
    return tournament_map


def seed_players(filename: str, label: str) -> None:
    """Seed players from a JSON file."""
    data = load_json(filename)

    for item in data:
        slug = item["slug"]
        existing = Player.query.filter_by(slug=slug).first()
        if existing:
            print(f"  Player already exists: {slug}")
            continue

        dob = date.fromisoformat(item["date_of_birth"]) if item.get("date_of_birth") else None

        player = Player(
            first_name=item["first_name"],
            last_name=item["last_name"],
            full_name=item["full_name"],
            slug=slug,
            tour=item["tour"],
            nationality=item["nationality"],
            nationality_name=item.get("nationality_name"),
            date_of_birth=dob,
            plays=item.get("plays"),
            backhand=item.get("backhand"),
            turned_pro_year=item.get("turned_pro_year"),
            current_singles_rank=item.get("current_singles_rank"),
            is_active=True,
        )
        db.session.add(player)
        print(f"  Added {label} player: {item['full_name']} (#{item.get('current_singles_rank')})")

    db.session.flush()


def seed_calendar(tournament_map: dict[str, Tournament]) -> None:
    """Seed tournament editions from the calendar."""
    data = load_json("calendar_2026.json")

    for item in data:
        slug = item["tournament_slug"]
        tournament = tournament_map.get(slug)
        if not tournament:
            print(f"  Warning: No tournament found for slug '{slug}', skipping")
            continue

        year = item["year"]
        existing = TournamentEdition.query.filter_by(
            tournament_id=tournament.id, year=year
        ).first()
        if existing:
            print(f"  Edition already exists: {tournament.name} {year}")
            continue

        edition = TournamentEdition(
            tournament_id=tournament.id,
            year=year,
            start_date=date.fromisoformat(item["start_date"]),
            end_date=date.fromisoformat(item["end_date"]),
            status=item.get("status", "upcoming"),
            draw_size=tournament.draw_size,
            prize_money_usd=tournament.prize_money_usd,
        )
        db.session.add(edition)
        print(f"  Added edition: {tournament.name} {year}")

    db.session.flush()


def main() -> None:
    """Run the full seed process."""
    app = create_app("development")

    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        print("\nSeeding tournaments...")
        tournament_map = seed_tournaments()

        print("\nSeeding ATP players...")
        seed_players("players_atp_top100.json", "ATP")

        print("\nSeeding WTA players...")
        seed_players("players_wta_top100.json", "WTA")

        print("\nSeeding 2026 calendar...")
        seed_calendar(tournament_map)

        print("\nCommitting to database...")
        db.session.commit()

        # Print summary
        player_count = Player.query.count()
        tournament_count = Tournament.query.count()
        edition_count = TournamentEdition.query.count()

        print(f"\nSeed complete!")
        print(f"  Players: {player_count}")
        print(f"  Tournaments: {tournament_count}")
        print(f"  Tournament Editions: {edition_count}")


if __name__ == "__main__":
    main()
