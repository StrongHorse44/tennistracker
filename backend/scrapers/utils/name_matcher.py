"""Fuzzy player name matching across data sources.

Handles variations like:
- "Novak Djokovic" vs "N. Djokovic" vs "DJOKOVIC, Novak"
- "Carlos Alcaraz Garfia" vs "Carlos Alcaraz"
- Accented characters: "Holger Rune" vs "Holger Vitus Nodskov Rune"
"""

import re
import unicodedata
from difflib import SequenceMatcher


class PlayerNameMatcher:
    """Match player names across different data sources."""

    def __init__(self, known_players: list[dict]):
        """Initialize with list of known player dicts from DB.

        Each dict should have: id, full_name, first_name, last_name, nationality
        """
        self.players = known_players
        self._build_index()

    def _normalize(self, name: str) -> str:
        """Normalize a player name for matching."""
        name = name.strip()

        # Handle "LAST, First" format
        if "," in name:
            parts = name.split(",", 1)
            name = f"{parts[1].strip()} {parts[0].strip()}"

        # Remove parenthetical info like "(WC)" or "[1]"
        name = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", name)

        # Normalize unicode (remove accents)
        name = unicodedata.normalize("NFKD", name)
        name = "".join(c for c in name if not unicodedata.combining(c))

        return name.lower().strip()

    def _build_index(self) -> None:
        """Build lookup indexes for fast matching."""
        self.by_last_name: dict[str, list[dict]] = {}
        self.by_full_normalized: dict[str, dict] = {}

        for p in self.players:
            ln = self._normalize(p["last_name"])
            self.by_last_name.setdefault(ln, []).append(p)
            self.by_full_normalized[self._normalize(p["full_name"])] = p

    def match(
        self,
        raw_name: str,
        nationality: str | None = None,
        threshold: float = 0.85,
    ) -> tuple[dict | None, float]:
        """Find the best matching player for a raw name string.

        Returns (player_dict, confidence) or (None, 0.0).
        """
        normalized = self._normalize(raw_name)

        # Exact match
        if normalized in self.by_full_normalized:
            return self.by_full_normalized[normalized], 1.0

        # Last name match with fuzzy first name
        words = normalized.split()
        if not words:
            return None, 0.0

        last = words[-1]
        candidates = self.by_last_name.get(last, [])

        # If nationality provided, prefer candidates from same country
        if nationality and candidates:
            nat_filtered = [
                c
                for c in candidates
                if c.get("nationality", "").lower() == nationality.lower()
            ]
            if nat_filtered:
                candidates = nat_filtered

        best_match = None
        best_score = 0.0
        for c in candidates:
            score = SequenceMatcher(
                None, normalized, self._normalize(c["full_name"])
            ).ratio()
            if score > best_score:
                best_score = score
                best_match = c

        if best_match and best_score >= threshold:
            return best_match, best_score

        # Fallback: try all players if no last name match
        if not candidates:
            best_match = None
            best_score = 0.0
            for p in self.players:
                score = SequenceMatcher(
                    None, normalized, self._normalize(p["full_name"])
                ).ratio()
                if score > best_score:
                    best_score = score
                    best_match = p

            if best_match and best_score >= threshold:
                return best_match, best_score

        return None, 0.0
