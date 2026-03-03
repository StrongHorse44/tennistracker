"""Seed the database with initial tournament, player, calendar, entry list,
match, prediction, and historical result data."""

import json
import sys
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.app import create_app
from backend.extensions import db
from backend.models import (
    Player,
    Tournament,
    TournamentEdition,
    EntryListRecord,
    Match,
    Prediction,
    HistoricalParticipation,
)

SEED_DIR = project_root / "data" / "seed"


def load_json(filename: str) -> list[dict]:
    """Load a JSON file from the seed directory."""
    path = SEED_DIR / filename
    with open(path) as f:
        return json.load(f)


# ── Lookup helpers ──────────────────────────────────────────────


def get_player_map() -> dict[str, Player]:
    """Return slug -> Player mapping for all players in DB."""
    return {p.slug: p for p in Player.query.all()}


def get_edition_map() -> dict[tuple[str, int], TournamentEdition]:
    """Return (tournament_slug, year) -> TournamentEdition mapping."""
    editions = (
        db.session.query(TournamentEdition, Tournament)
        .join(Tournament, TournamentEdition.tournament_id == Tournament.id)
        .all()
    )
    return {(t.slug, e.year): e for e, t in editions}


# ── Core seeders ────────────────────────────────────────────────


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
            # Update status if it changed in seed data
            new_status = item.get("status", "upcoming")
            if existing.status != new_status:
                print(f"  Updating {tournament.name} {year}: {existing.status} -> {new_status}")
                existing.status = new_status
            else:
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


# ── New enrichment seeders ──────────────────────────────────────


def seed_entry_lists() -> int:
    """Seed entry list records from entry_lists.json."""
    data = load_json("entry_lists.json")
    player_map = get_player_map()
    edition_map = get_edition_map()
    count = 0

    for tournament_block in data:
        slug = tournament_block["tournament_slug"]
        year = tournament_block["year"]
        edition = edition_map.get((slug, year))
        if not edition:
            print(f"  Warning: No edition for {slug} {year}, skipping")
            continue

        for entry in tournament_block["entries"]:
            player = player_map.get(entry["player_slug"])
            if not player:
                print(f"  Warning: No player for {entry['player_slug']}, skipping")
                continue

            existing = EntryListRecord.query.filter_by(
                player_id=player.id, tournament_edition_id=edition.id
            ).first()
            if existing:
                # Update status if it changed (e.g., competing -> champion)
                if existing.status != entry.get("status", "entered"):
                    existing.status = entry.get("status", "entered")
                continue

            record = EntryListRecord(
                player_id=player.id,
                tournament_edition_id=edition.id,
                entry_type=entry["entry_type"],
                entry_rank=entry.get("entry_rank"),
                seed=entry.get("seed"),
                status=entry.get("status", "entered"),
                source=entry.get("source", "seed"),
            )
            db.session.add(record)
            count += 1

    db.session.flush()
    return count


def seed_matches() -> int:
    """Seed match records from matches.json."""
    data = load_json("matches.json")
    player_map = get_player_map()
    edition_map = get_edition_map()
    count = 0

    for tournament_block in data:
        slug = tournament_block["tournament_slug"]
        year = tournament_block["year"]
        edition = edition_map.get((slug, year))
        if not edition:
            print(f"  Warning: No edition for {slug} {year}, skipping")
            continue

        for m in tournament_block["matches"]:
            p1 = player_map.get(m["player1_slug"])
            p2 = player_map.get(m["player2_slug"])
            if not p1 or not p2:
                print(f"  Warning: Missing player for match, skipping")
                continue

            winner = player_map.get(m["winner_slug"]) if m.get("winner_slug") else None

            # Check for existing match to prevent duplicates
            existing = Match.query.filter_by(
                tournament_edition_id=edition.id,
                player1_id=p1.id,
                player2_id=p2.id,
                round=m["round"],
            ).first()
            if existing:
                # Update existing match with latest data
                existing.winner_id = winner.id if winner else None
                existing.score = m.get("score")
                existing.status = m.get("status", "scheduled")
                existing.duration_minutes = m.get("duration_minutes")
                continue

            match = Match(
                tournament_edition_id=edition.id,
                player1_id=p1.id,
                player2_id=p2.id,
                winner_id=winner.id if winner else None,
                round=m["round"],
                score=m.get("score"),
                status=m.get("status", "scheduled"),
                scheduled_date=date.fromisoformat(m["scheduled_date"]) if m.get("scheduled_date") else None,
                duration_minutes=m.get("duration_minutes"),
            )
            db.session.add(match)
            count += 1

    db.session.flush()
    return count


def seed_predictions() -> int:
    """Seed prediction records from predictions.json."""
    data = load_json("predictions.json")
    player_map = get_player_map()
    edition_map = get_edition_map()
    count = 0

    for tournament_block in data:
        slug = tournament_block["tournament_slug"]
        year = tournament_block["year"]
        edition = edition_map.get((slug, year))
        if not edition:
            print(f"  Warning: No edition for {slug} {year}, skipping")
            continue

        for pred in tournament_block["predictions"]:
            player = player_map.get(pred["player_slug"])
            if not player:
                print(f"  Warning: No player for {pred['player_slug']}, skipping")
                continue

            existing = Prediction.query.filter_by(
                player_id=player.id,
                tournament_edition_id=edition.id,
                model_version="seed-v1",
            ).first()
            if existing:
                continue

            prediction = Prediction(
                player_id=player.id,
                tournament_edition_id=edition.id,
                will_enter_probability=pred["probability"],
                confidence_level=pred.get("confidence", "medium"),
                prediction_label=pred.get("label", "possible"),
                features_json=pred.get("features"),
                model_version="seed-v1",
                predicted_at=datetime.utcnow(),
            )
            db.session.add(prediction)
            count += 1

    db.session.flush()
    return count


def seed_historical_results() -> int:
    """Seed historical participation records from historical_results.json."""
    data = load_json("historical_results.json")
    player_map = get_player_map()
    edition_map = get_edition_map()
    count = 0

    for tournament_block in data:
        slug = tournament_block["tournament_slug"]
        year = tournament_block["year"]
        edition = edition_map.get((slug, year))
        if not edition:
            print(f"  Warning: No edition for {slug} {year}, skipping")
            continue

        for result in tournament_block["results"]:
            player = player_map.get(result["player_slug"])
            if not player:
                print(f"  Warning: No player for {result['player_slug']}, skipping")
                continue

            existing = HistoricalParticipation.query.filter_by(
                player_id=player.id, tournament_edition_id=edition.id
            ).first()
            if existing:
                continue

            hp = HistoricalParticipation(
                player_id=player.id,
                tournament_edition_id=edition.id,
                result=result["result"],
                rounds_won=result.get("rounds_won", 0),
                ranking_points_earned=result.get("ranking_points_earned"),
                prize_money_earned_usd=result.get("prize_money_earned_usd"),
                ranking_at_time=result.get("ranking_at_time"),
                seed_at_time=result.get("seed_at_time"),
                points_to_defend=result.get("points_to_defend", 0),
                matches_played=result.get("matches_played", 0),
                matches_won=result.get("matches_won", 0),
                data_source="seed",
            )
            db.session.add(hp)
            count += 1

    db.session.flush()
    return count


# ── Main ────────────────────────────────────────────────────────


def cleanup_duplicate_matches() -> int:
    """Remove duplicate match records, keeping the most recent one."""
    from sqlalchemy import func

    # Find duplicates by (tournament_edition_id, player1_id, player2_id, round)
    dupes = (
        db.session.query(
            Match.tournament_edition_id,
            Match.player1_id,
            Match.player2_id,
            Match.round,
            func.count(Match.id).label("cnt"),
            func.max(Match.id).label("keep_id"),
        )
        .group_by(Match.tournament_edition_id, Match.player1_id, Match.player2_id, Match.round)
        .having(func.count(Match.id) > 1)
        .all()
    )

    removed = 0
    for dupe in dupes:
        # Delete all but the one with the highest id
        to_delete = Match.query.filter(
            Match.tournament_edition_id == dupe.tournament_edition_id,
            Match.player1_id == dupe.player1_id,
            Match.player2_id == dupe.player2_id,
            Match.round == dupe.round,
            Match.id != dupe.keep_id,
        ).all()
        for m in to_delete:
            db.session.delete(m)
            removed += 1

    if removed:
        db.session.flush()

    return removed


def main() -> None:
    """Run the full seed process."""
    app = create_app("development")

    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        # Clean up any duplicate matches from previous seeds
        print("\nCleaning up duplicate matches...")
        removed = cleanup_duplicate_matches()
        if removed:
            print(f"  Removed {removed} duplicate matches")
        else:
            print("  No duplicates found")

        print("\nSeeding tournaments...")
        tournament_map = seed_tournaments()

        print("\nSeeding ATP players...")
        seed_players("players_atp_top100.json", "ATP")

        print("\nSeeding WTA players...")
        seed_players("players_wta_top100.json", "WTA")

        print("\nSeeding 2026 calendar...")
        seed_calendar(tournament_map)

        db.session.commit()

        print("\nSeeding entry lists...")
        entry_count = seed_entry_lists()
        print(f"  Added {entry_count} entry list records")

        print("\nSeeding matches...")
        match_count = seed_matches()
        print(f"  Added {match_count} matches")

        print("\nSeeding predictions...")
        pred_count = seed_predictions()
        print(f"  Added {pred_count} predictions")

        print("\nSeeding historical results...")
        hist_count = seed_historical_results()
        print(f"  Added {hist_count} historical results")

        print("\nCommitting to database...")
        db.session.commit()

        # Print summary
        print(f"\nSeed complete!")
        print(f"  Players: {Player.query.count()}")
        print(f"  Tournaments: {Tournament.query.count()}")
        print(f"  Tournament Editions: {TournamentEdition.query.count()}")
        print(f"  Entry List Records: {EntryListRecord.query.count()}")
        print(f"  Matches: {Match.query.count()}")
        print(f"  Predictions: {Prediction.query.count()}")
        print(f"  Historical Results: {HistoricalParticipation.query.count()}")


if __name__ == "__main__":
    main()
