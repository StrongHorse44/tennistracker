"""Tests for player API endpoints."""

import pytest
from datetime import date

from backend.models import Player, Tournament, TournamentEdition, EntryListRecord, Prediction
from backend.extensions import db as _db


class TestListPlayers:
    def test_list_players_empty(self, client):
        response = client.get("/api/v1/players")
        assert response.status_code == 200
        data = response.get_json()
        assert data["players"] == []
        assert data["total"] == 0

    def test_list_players_returns_player(self, client, sample_player):
        response = client.get("/api/v1/players")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 1
        assert data["players"][0]["full_name"] == "Novak Djokovic"

    def test_list_players_filter_tour(self, client, sample_player, db):
        wta_player = Player(
            first_name="Iga", last_name="Swiatek", full_name="Iga Swiatek",
            slug="iga-swiatek", tour="WTA", nationality="POL",
            current_singles_rank=2, is_active=True,
        )
        db.session.add(wta_player)
        db.session.commit()

        response = client.get("/api/v1/players?tour=WTA")
        data = response.get_json()
        assert data["total"] == 1
        assert data["players"][0]["full_name"] == "Iga Swiatek"

    def test_list_players_filter_rank(self, client, sample_player, db):
        player2 = Player(
            first_name="Jannik", last_name="Sinner", full_name="Jannik Sinner",
            slug="jannik-sinner", tour="ATP", nationality="ITA",
            current_singles_rank=1, is_active=True,
        )
        db.session.add(player2)
        db.session.commit()

        response = client.get("/api/v1/players?rank_max=3")
        data = response.get_json()
        assert data["total"] == 1
        assert data["players"][0]["full_name"] == "Jannik Sinner"

    def test_list_players_pagination(self, client, sample_player):
        response = client.get("/api/v1/players?page=1&per_page=1")
        data = response.get_json()
        assert data["per_page"] == 1
        assert data["page"] == 1


class TestGetPlayer:
    def test_get_player_by_slug(self, client, sample_player):
        response = client.get("/api/v1/players/novak-djokovic")
        assert response.status_code == 200
        data = response.get_json()
        assert data["full_name"] == "Novak Djokovic"
        assert data["tour"] == "ATP"
        assert data["nationality"] == "SRB"
        assert data["current_singles_rank"] == 4

    def test_get_player_not_found(self, client):
        response = client.get("/api/v1/players/nonexistent")
        assert response.status_code == 404


class TestGetPlayerLocation:
    def test_player_location_no_current(self, client, sample_player):
        response = client.get("/api/v1/players/novak-djokovic/location")
        assert response.status_code == 200
        data = response.get_json()
        assert data["current"] is None
        assert data["upcoming_confirmed"] == []
        assert data["upcoming_predicted"] == []


class TestGetPlayerTimeline:
    def test_player_timeline_empty(self, client, sample_player):
        response = client.get("/api/v1/players/novak-djokovic/timeline?year=2026")
        assert response.status_code == 200
        data = response.get_json()
        assert data["year"] == 2026
        assert data["timeline"] == []

    def test_player_timeline_with_entry(self, client, sample_player, sample_entry, sample_edition):
        response = client.get("/api/v1/players/novak-djokovic/timeline?year=2026")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["timeline"]) == 1
        event = data["timeline"][0]
        assert event["tracking_status"] == "confirmed"
        assert event["entry"] is not None


class TestGetPlayerHistory:
    def test_player_history_empty(self, client, sample_player):
        response = client.get("/api/v1/players/novak-djokovic/history")
        assert response.status_code == 200
        data = response.get_json()
        assert data["history"] == []
