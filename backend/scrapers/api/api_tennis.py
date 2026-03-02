"""API-Tennis integration for rankings, live scores, and results."""

from backend.scrapers.base import BaseScraper
from backend.scrapers.config import URLS, RATE_LIMITS, API_TENNIS_KEY


class APITennisClient(BaseScraper):
    """Client for the API-Tennis REST API."""

    BASE_URL = URLS["api_tennis"]

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            "api-tennis",
            rate_limit_seconds=RATE_LIMITS.get("api-tennis", 1.0),
        )
        self.api_key = api_key or API_TENNIS_KEY

    def _api_get(self, method: str, **params) -> dict:
        """Make an API-Tennis request."""
        params["method"] = method
        params["APIkey"] = self.api_key
        response = self.fetch(self.BASE_URL, params=params)
        return response.json()

    def get_standings(self, tour: str = "ATP") -> list[dict]:
        """Get current rankings/standings for a tour.

        Returns list of dicts with: player, place, points, etc.
        """
        data = self._api_get("get_standings", event_type=tour)
        results = data.get("result", [])

        standings = []
        for entry in results:
            standings.append(
                {
                    "player": entry.get("player", ""),
                    "place": int(entry.get("place", 0)),
                    "points": int(entry.get("points", 0)),
                    "team_id": entry.get("team_id", ""),
                }
            )

        return standings

    def get_live_events(self) -> list[dict]:
        """Get currently live tennis matches."""
        data = self._api_get("get_events", status="live")
        return data.get("result", [])

    def get_events_by_date(self, date_str: str) -> list[dict]:
        """Get events for a specific date (YYYY-MM-DD)."""
        data = self._api_get(
            "get_events", date_start=date_str, date_stop=date_str
        )
        return data.get("result", [])

    def scrape(self, **kwargs) -> list[dict]:
        """Generic scrape method — dispatches based on scrape_type."""
        scrape_type = kwargs.get("scrape_type", "standings")

        if scrape_type == "standings":
            tour = kwargs.get("tour", "ATP")
            return self.get_standings(tour)
        elif scrape_type == "live":
            return self.get_live_events()
        elif scrape_type == "events":
            date_str = kwargs.get("date", "")
            return self.get_events_by_date(date_str)

        return []
