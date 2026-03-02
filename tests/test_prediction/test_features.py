"""Tests for prediction features."""

from backend.prediction.features import PredictionFeatures, FEATURE_COLUMNS


class TestPredictionFeatures:
    def test_to_list_length(self):
        features = PredictionFeatures()
        result = features.to_list()
        assert len(result) == len(FEATURE_COLUMNS)

    def test_to_dict_keys(self):
        features = PredictionFeatures()
        result = features.to_dict()
        assert set(result.keys()) == set(FEATURE_COLUMNS)

    def test_custom_values(self):
        features = PredictionFeatures(
            played_last_year=True,
            current_ranking=5,
            is_grand_slam=True,
        )
        d = features.to_dict()
        assert d["played_last_year"] == 1
        assert d["current_ranking"] == 5
        assert d["is_grand_slam"] == 1

    def test_defaults(self):
        features = PredictionFeatures()
        d = features.to_dict()
        assert d["played_last_year"] == 0
        assert d["current_ranking"] == 999
        assert d["age"] == 25.0
