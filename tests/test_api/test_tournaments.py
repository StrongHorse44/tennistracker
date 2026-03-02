"""Tests for tournament API endpoints."""

import pytest
from datetime import date

from backend.models import Tournament, TournamentEdition
from backend.extensions import db as _db


class TestListTournaments:
    def test_list_tournaments_empty(self, client):
        response = client.get("/api/v1/tournaments")
        assert response.status_code == 200
        data = response.get_json()
        assert data["tournaments"] == []

    def test_list_tournaments(self, client, sample_tournament):
        response = client.get("/api/v1/tournaments")
        data = response.get_json()
        assert data["total"] == 1
        assert data["tournaments"][0]["name"] == "Australian Open"

    def test_filter_by_surface(self, client, sample_tournament, db):
        clay_tournament = Tournament(
            name="Roland Garros", slug="roland-garros", tour="GRAND_SLAM",
            category="Grand Slam", surface="Clay", city="Paris",
            country="FRA", is_mandatory=True,
        )
        db.session.add(clay_tournament)
        db.session.commit()

        response = client.get("/api/v1/tournaments?surface=Clay")
        data = response.get_json()
        assert data["total"] == 1
        assert data["tournaments"][0]["name"] == "Roland Garros"


class TestGetTournament:
    def test_get_tournament(self, client, sample_tournament):
        response = client.get("/api/v1/tournaments/australian-open")
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Australian Open"
        assert data["category"] == "Grand Slam"

    def test_get_tournament_not_found(self, client):
        response = client.get("/api/v1/tournaments/nonexistent")
        assert response.status_code == 404


class TestGetEdition:
    def test_get_edition(self, client, sample_edition, sample_tournament):
        response = client.get("/api/v1/tournaments/australian-open/editions/2026")
        assert response.status_code == 200
        data = response.get_json()
        assert data["year"] == 2026
        assert data["tournament"]["name"] == "Australian Open"

    def test_get_edition_not_found(self, client, sample_tournament):
        response = client.get("/api/v1/tournaments/australian-open/editions/9999")
        assert response.status_code == 404


class TestGetField:
    def test_get_field_empty(self, client, sample_edition, sample_tournament):
        response = client.get("/api/v1/tournaments/australian-open/editions/2026/field")
        assert response.status_code == 200
        data = response.get_json()
        assert data["confirmed_entries"] == []
        assert data["field_size"] == 0

    def test_get_field_with_entry(self, client, sample_entry, sample_edition, sample_tournament):
        response = client.get("/api/v1/tournaments/australian-open/editions/2026/field")
        data = response.get_json()
        assert data["field_size"] == 1
        assert data["confirmed_entries"][0]["player"]["full_name"] == "Novak Djokovic"
