"""Feature engineering for tournament entry prediction."""

from dataclasses import dataclass
from datetime import date

RESULT_ENCODING = {
    "W": 7,
    "F": 6,
    "SF": 5,
    "QF": 4,
    "R16": 3,
    "R32": 2,
    "R64": 1,
    "R128": 0,
}

CATEGORY_ENCODING = {
    "Grand Slam": 6,
    "ATP 1000": 5,
    "WTA 1000": 5,
    "ATP 500": 4,
    "WTA 500": 4,
    "ATP 250": 3,
    "WTA 250": 3,
    "Challenger": 2,
    "ITF": 1,
    "Exhibition": 0,
}

FEATURE_COLUMNS = [
    "played_last_year",
    "played_last_3_years",
    "played_last_5_years",
    "career_appearances",
    "best_result_code",
    "points_to_defend",
    "points_to_defend_pct",
    "defending_champion",
    "is_mandatory",
    "is_grand_slam",
    "category_code",
    "winner_points_available",
    "surface_win_pct_career",
    "surface_win_pct_last_12m",
    "surface_matches_last_12m",
    "current_ranking",
    "ranking_trend_3m",
    "matches_won_last_30d",
    "tournaments_played_last_30d",
    "geographic_distance_km",
    "days_until_start",
    "days_between_prev_tournament",
    "tournaments_entered_next_30d",
    "age",
    "years_on_tour",
]


@dataclass
class PredictionFeatures:
    """Feature vector for a (player, tournament_edition) pair."""

    # Historical participation
    played_last_year: bool = False
    played_last_3_years: int = 0
    played_last_5_years: int = 0
    career_appearances: int = 0
    best_result_code: int = 0

    # Points defense
    points_to_defend: int = 0
    points_to_defend_pct: float = 0.0
    defending_champion: bool = False

    # Tournament characteristics
    is_mandatory: bool = False
    is_grand_slam: bool = False
    category_code: int = 0
    winner_points_available: int = 0

    # Surface affinity
    surface_win_pct_career: float = 0.0
    surface_win_pct_last_12m: float = 0.0
    surface_matches_last_12m: int = 0

    # Current form
    current_ranking: int = 999
    ranking_trend_3m: float = 0.0
    matches_won_last_30d: int = 0
    tournaments_played_last_30d: int = 0

    # Schedule and travel
    geographic_distance_km: float = 0.0
    days_until_start: int = 0
    days_between_prev_tournament: int = 0
    tournaments_entered_next_30d: int = 0

    # Demographics
    age: float = 25.0
    years_on_tour: int = 5

    def to_list(self) -> list:
        """Convert to ordered list matching FEATURE_COLUMNS."""
        return [
            int(self.played_last_year),
            self.played_last_3_years,
            self.played_last_5_years,
            self.career_appearances,
            self.best_result_code,
            self.points_to_defend,
            self.points_to_defend_pct,
            int(self.defending_champion),
            int(self.is_mandatory),
            int(self.is_grand_slam),
            self.category_code,
            self.winner_points_available,
            self.surface_win_pct_career,
            self.surface_win_pct_last_12m,
            self.surface_matches_last_12m,
            self.current_ranking,
            self.ranking_trend_3m,
            self.matches_won_last_30d,
            self.tournaments_played_last_30d,
            self.geographic_distance_km,
            self.days_until_start,
            self.days_between_prev_tournament,
            self.tournaments_entered_next_30d,
            self.age,
            self.years_on_tour,
        ]

    def to_dict(self) -> dict:
        """Convert to dictionary for storage in features_json."""
        return {col: val for col, val in zip(FEATURE_COLUMNS, self.to_list())}
