"""Tests for search API endpoint."""

import pytest


class TestSearch:
    def test_search_requires_query(self, client):
        response = client.get("/api/v1/search")
        assert response.status_code == 400

    def test_search_requires_min_length(self, client):
        response = client.get("/api/v1/search?q=a")
        assert response.status_code == 400

    def test_search_players(self, client, sample_player):
        response = client.get("/api/v1/search?q=Djokovic")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["players"]) == 1
        assert data["players"][0]["full_name"] == "Novak Djokovic"

    def test_search_tournaments(self, client, sample_tournament):
        response = client.get("/api/v1/search?q=Australian")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["tournaments"]) == 1

    def test_search_by_type(self, client, sample_player, sample_tournament):
        response = client.get("/api/v1/search?q=open&type=tournament")
        data = response.get_json()
        assert "tournaments" in data
        assert "players" not in data

    def test_search_no_results(self, client):
        response = client.get("/api/v1/search?q=zzzzzzz")
        data = response.get_json()
        assert data["players"] == []
        assert data["tournaments"] == []
