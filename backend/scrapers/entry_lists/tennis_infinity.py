"""Scrape entry lists from tennis-infinity.com."""

from datetime import datetime

from bs4 import BeautifulSoup

from backend.scrapers.base import BaseScraper
from backend.scrapers.config import URLS, RATE_LIMITS


class TennisInfinityScraper(BaseScraper):
    """Scrape entry lists from tennis-infinity.com."""

    BASE_URL = URLS["tennis_infinity_entry_lists"]

    def __init__(self) -> None:
        super().__init__(
            "tennis-infinity",
            rate_limit_seconds=RATE_LIMITS.get("tennis-infinity", 3.0),
        )

    def get_tournament_entry_list_urls(self) -> list[dict]:
        """Get all available entry list page URLs."""
        response = self.fetch(self.BASE_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        links = []
        for link in soup.select('a[href*="entry-list"]'):
            href = link.get("href", "")
            name = link.get_text(strip=True)
            if href and name:
                full_url = (
                    href
                    if href.startswith("http")
                    else f"https://tennis-infinity.com{href}"
                )
                links.append({"name": name, "url": full_url})

        return links

    def parse_entry_list_page(self, url: str) -> list[dict]:
        """Parse a single tournament entry list page."""
        response = self.fetch(url)
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []
        for row in soup.select("table tr, .entry-row"):
            entry = self._parse_entry_row(row)
            if entry:
                entries.append(entry)

        return entries

    def _parse_entry_row(self, row) -> dict | None:
        """Parse a single entry list row. Returns normalized dict."""
        cells = row.find_all(["td", "span", "div"])
        if len(cells) < 2:
            return None

        # Extract text — actual selectors depend on site structure
        texts = [c.get_text(strip=True) for c in cells]

        return {
            "player_name": texts[0] if texts else None,
            "ranking": self._parse_int(texts[1]) if len(texts) > 1 else None,
            "entry_type": self._normalize_entry_type(texts[2]) if len(texts) > 2 else None,
            "seed": self._parse_int(texts[3]) if len(texts) > 3 else None,
            "status": "entered",
            "withdrawal_reason": None,
            "source": "tennis-infinity",
            "scraped_at": datetime.utcnow().isoformat(),
        }

    def _parse_int(self, value: str) -> int | None:
        """Safely parse an integer from a string."""
        try:
            return int(value.strip().replace(",", ""))
        except (ValueError, AttributeError):
            return None

    def _normalize_entry_type(self, raw: str) -> str:
        """Normalize entry type abbreviations to standard values."""
        mapping = {
            "DA": "Direct Acceptance",
            "WC": "Wild Card",
            "Q": "Qualifier",
            "SE": "Special Exempt",
            "PR": "Protected Ranking",
            "Alt": "Alternate",
            "LL": "Alternate",
        }
        return mapping.get(raw.strip(), "Unknown")

    def scrape(self, **kwargs) -> list[dict]:
        """Main scrape method. If no URL provided, scrape all available."""
        tournament_url = kwargs.get("tournament_url")
        if tournament_url:
            return self.parse_entry_list_page(tournament_url)

        all_entries = []
        for tournament in self.get_tournament_entry_list_urls():
            entries = self.parse_entry_list_page(tournament["url"])
            for entry in entries:
                entry["tournament_name"] = tournament["name"]
            all_entries.extend(entries)

        return all_entries
