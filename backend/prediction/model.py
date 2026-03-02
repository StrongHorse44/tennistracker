"""Tournament entry prediction model."""

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import precision_score, recall_score, roc_auc_score

from backend.prediction.features import FEATURE_COLUMNS


class TournamentEntryPredictor:
    """Predict whether a player will enter a tournament."""

    def __init__(self) -> None:
        self.model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            min_samples_leaf=20,
            random_state=42,
        )
        self.version: str | None = None

    def train(self, X, y, version_tag: str = "v1") -> list[dict]:
        """Train the model on historical (player, tournament) pairs.

        Args:
            X: DataFrame with FEATURE_COLUMNS
            y: Series of 0/1 (did not enter / entered)
            version_tag: Version identifier for this model

        Returns:
            List of score dicts from cross-validation splits.
        """
        tscv = TimeSeriesSplit(n_splits=5)

        scores = []
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            self.model.fit(X_train, y_train)
            y_pred_proba = self.model.predict_proba(X_val)[:, 1]

            scores.append(
                {
                    "auc": roc_auc_score(y_val, y_pred_proba),
                    "precision": precision_score(
                        y_val, (y_pred_proba > 0.5).astype(int), zero_division=0
                    ),
                    "recall": recall_score(
                        y_val, (y_pred_proba > 0.5).astype(int), zero_division=0
                    ),
                }
            )

        # Final fit on all data
        self.model.fit(X, y)
        self.version = version_tag

        return scores

    def predict(self, X) -> np.ndarray:
        """Predict entry probability for (player, tournament) pairs.

        Returns array of probabilities [0, 1].
        """
        return self.model.predict_proba(X)[:, 1]

    def get_feature_importance(self) -> dict[str, float]:
        """Return feature importances for explainability."""
        return dict(zip(FEATURE_COLUMNS, self.model.feature_importances_))

    def save(self, path: str | Path) -> None:
        """Save model to disk."""
        joblib.dump({"model": self.model, "version": self.version}, path)

    def load(self, path: str | Path) -> None:
        """Load model from disk."""
        data = joblib.load(path)
        self.model = data["model"]
        self.version = data["version"]
