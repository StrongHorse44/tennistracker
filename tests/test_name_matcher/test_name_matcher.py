"""Tests for PlayerNameMatcher."""

import pytest

from backend.scrapers.utils.name_matcher import PlayerNameMatcher

PLAYERS = [
    {"id": 1, "full_name": "Novak Djokovic", "first_name": "Novak", "last_name": "Djokovic", "nationality": "SRB"},
    {"id": 2, "full_name": "Carlos Alcaraz", "first_name": "Carlos", "last_name": "Alcaraz", "nationality": "ESP"},
    {"id": 3, "full_name": "Jannik Sinner", "first_name": "Jannik", "last_name": "Sinner", "nationality": "ITA"},
    {"id": 4, "full_name": "Stefanos Tsitsipas", "first_name": "Stefanos", "last_name": "Tsitsipas", "nationality": "GRE"},
    {"id": 5, "full_name": "Holger Rune", "first_name": "Holger", "last_name": "Rune", "nationality": "DEN"},
    {"id": 6, "full_name": "Alex de Minaur", "first_name": "Alex", "last_name": "de Minaur", "nationality": "AUS"},
]


@pytest.fixture
def matcher():
    return PlayerNameMatcher(PLAYERS)


class TestExactMatch:
    def test_exact_match(self, matcher):
        player, confidence = matcher.match("Novak Djokovic")
        assert player is not None
        assert player["id"] == 1
        assert confidence == 1.0

    def test_exact_match_case_insensitive(self, matcher):
        player, confidence = matcher.match("novak djokovic")
        assert player is not None
        assert player["id"] == 1
        assert confidence == 1.0


class TestLastFirstFormat:
    def test_last_comma_first(self, matcher):
        player, confidence = matcher.match("DJOKOVIC, Novak")
        assert player is not None
        assert player["id"] == 1
        assert confidence == 1.0


class TestFuzzyMatch:
    def test_abbreviated_first_name(self, matcher):
        # "N. Djokovic" gets 0.80 similarity — below default 0.85 threshold
        player, confidence = matcher.match("N. Djokovic", threshold=0.75)
        assert player is not None
        assert player["id"] == 1
        assert confidence >= 0.75

    def test_partial_name(self, matcher):
        # "Carlos Alcaraz Garfia" vs "Carlos Alcaraz" gets 0.80 similarity
        player, confidence = matcher.match("Carlos Alcaraz Garfia", threshold=0.75)
        assert player is not None
        assert player["id"] == 2
        assert confidence >= 0.75

    def test_close_match_at_default_threshold(self, matcher):
        # Exact last name + close first name should match
        player, confidence = matcher.match("Novk Djokovic")
        assert player is not None
        assert player["id"] == 1
        assert confidence >= 0.85


class TestParenthetical:
    def test_with_entry_type(self, matcher):
        player, confidence = matcher.match("Jannik Sinner (WC)")
        assert player is not None
        assert player["id"] == 3

    def test_with_seed(self, matcher):
        player, confidence = matcher.match("Novak Djokovic [3]")
        assert player is not None
        assert player["id"] == 1


class TestNationalityFilter:
    def test_nationality_helps_disambiguation(self, matcher):
        player, confidence = matcher.match("Novak Djokovic", nationality="SRB")
        assert player is not None
        assert player["id"] == 1


class TestNoMatch:
    def test_no_match(self, matcher):
        player, confidence = matcher.match("Completely Unknown Player")
        assert player is None
        assert confidence == 0.0

    def test_empty_string(self, matcher):
        player, confidence = matcher.match("")
        assert player is None
