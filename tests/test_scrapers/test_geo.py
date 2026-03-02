"""Tests for geographic utilities."""

import pytest

from backend.scrapers.utils.geo import haversine_distance, same_continent


class TestHaversineDistance:
    def test_same_point(self):
        dist = haversine_distance(0, 0, 0, 0)
        assert dist == 0.0

    def test_known_distance(self):
        # New York to London is approximately 5,570 km
        dist = haversine_distance(40.7128, -74.0060, 51.5074, -0.1278)
        assert 5500 < dist < 5700

    def test_melbourne_to_paris(self):
        # Melbourne to Paris is approximately 16,800 km
        dist = haversine_distance(-37.8136, 144.9631, 48.8566, 2.3522)
        assert 16500 < dist < 17100


class TestSameContinent:
    def test_same_continent(self):
        assert same_continent("USA", "CAN") is True
        assert same_continent("FRA", "ESP") is True

    def test_different_continent(self):
        assert same_continent("USA", "FRA") is False
        assert same_continent("AUS", "GBR") is False

    def test_unknown_country(self):
        assert same_continent("XXX", "YYY") is False
