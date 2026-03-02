"""SQLAlchemy models for CourtTracker."""

from datetime import datetime, date
from enum import Enum as PyEnum

from backend.extensions import db


class Tour(PyEnum):
    ATP = "ATP"
    WTA = "WTA"
    GRAND_SLAM = "GRAND_SLAM"
    MIXED = "MIXED"


class TournamentCategory(PyEnum):
    GRAND_SLAM = "Grand Slam"
    ATP_1000 = "ATP 1000"
    ATP_500 = "ATP 500"
    ATP_250 = "ATP 250"
    WTA_1000 = "WTA 1000"
    WTA_500 = "WTA 500"
    WTA_250 = "WTA 250"
    CHALLENGER = "Challenger"
    ITF = "ITF"
    EXHIBITION = "Exhibition"


class Surface(PyEnum):
    HARD = "Hard"
    CLAY = "Clay"
    GRASS = "Grass"
    CARPET = "Carpet"


class EditionStatus(PyEnum):
    UPCOMING = "upcoming"
    ENTRY_LIST = "entry_list"
    DRAW_RELEASED = "draw_released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EntryType(PyEnum):
    DIRECT_ACCEPTANCE = "Direct Acceptance"
    WILD_CARD = "Wild Card"
    QUALIFIER = "Qualifier"
    SPECIAL_EXEMPT = "Special Exempt"
    PROTECTED_RANKING = "Protected Ranking"
    ALTERNATE = "Alternate"
    UNKNOWN = "Unknown"


class EntryStatus(PyEnum):
    ENTERED = "entered"
    CONFIRMED = "confirmed"
    WITHDRAWN = "withdrawn"
    REPLACED = "replaced"
    COMPETING = "competing"
    ELIMINATED = "eliminated"
    CHAMPION = "champion"


class MatchStatus(PyEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    WALKOVER = "walkover"
    RETIRED = "retired"
    DEFAULTED = "defaulted"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class AlertType(PyEnum):
    PLAYER_ENTRY = "player_entry"
    PLAYER_WITHDRAWAL = "player_withdrawal"
    TOURNAMENT_FIELD = "tournament_field"
    PREDICTION_CHANGE = "prediction_change"
    MATCH_SCHEDULED = "match_scheduled"
    RESULT = "result"


class ScrapeStatus(PyEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class Player(db.Model):
    """Professional tennis player."""

    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)

    # Identity
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)

    # Tour affiliation
    tour = db.Column(db.String(10), nullable=False)
    nationality = db.Column(db.String(3), nullable=False)
    nationality_name = db.Column(db.String(100))

    # Bio
    date_of_birth = db.Column(db.Date)
    height_cm = db.Column(db.Integer)
    weight_kg = db.Column(db.Integer)
    plays = db.Column(db.String(20))
    backhand = db.Column(db.String(20))
    turned_pro_year = db.Column(db.Integer)

    # Current ranking snapshot
    current_singles_rank = db.Column(db.Integer)
    current_doubles_rank = db.Column(db.Integer)
    current_singles_points = db.Column(db.Integer)
    current_doubles_points = db.Column(db.Integer)
    ranking_updated_at = db.Column(db.DateTime)

    # External IDs
    api_tennis_id = db.Column(db.String(50))
    sportradar_id = db.Column(db.String(50))
    atp_id = db.Column(db.String(50))
    wta_id = db.Column(db.String(50))
    wikipedia_slug = db.Column(db.String(200))

    # Profile image
    photo_url = db.Column(db.Text)

    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entry_records = db.relationship(
        "EntryListRecord", back_populates="player", lazy="dynamic",
        foreign_keys="EntryListRecord.player_id",
    )
    historical_participations = db.relationship(
        "HistoricalParticipation", back_populates="player", lazy="dynamic"
    )
    predictions = db.relationship("Prediction", back_populates="player", lazy="dynamic")
    surface_stats = db.relationship("PlayerSurfaceStats", back_populates="player", lazy="dynamic")
    ranking_history = db.relationship("RankingHistory", back_populates="player", lazy="dynamic")

    __table_args__ = (
        db.Index("idx_players_tour", "tour"),
        db.Index("idx_players_rank", "current_singles_rank"),
        db.Index("idx_players_active_rank", "is_active", "current_singles_rank"),
    )

    def to_dict(self, brief: bool = False) -> dict:
        """Serialize player to dictionary."""
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "slug": self.slug,
            "tour": self.tour,
            "nationality": self.nationality,
            "current_singles_rank": self.current_singles_rank,
            "photo_url": self.photo_url,
        }
        if not brief:
            data.update(
                {
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "nationality_name": self.nationality_name,
                    "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
                    "height_cm": self.height_cm,
                    "weight_kg": self.weight_kg,
                    "plays": self.plays,
                    "backhand": self.backhand,
                    "turned_pro_year": self.turned_pro_year,
                    "current_doubles_rank": self.current_doubles_rank,
                    "current_singles_points": self.current_singles_points,
                    "current_doubles_points": self.current_doubles_points,
                    "is_active": self.is_active,
                }
            )
        return data

    def __repr__(self) -> str:
        return f"<Player {self.full_name} ({self.tour} #{self.current_singles_rank})>"


class Tournament(db.Model):
    """A recurring tennis tournament (not a specific year's edition)."""

    __tablename__ = "tournaments"

    id = db.Column(db.Integer, primary_key=True)

    # Identity
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)

    # Classification
    tour = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    surface = db.Column(db.String(20), nullable=False)
    indoor_outdoor = db.Column(db.String(20))
    draw_size = db.Column(db.Integer)

    # Location
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(3), nullable=False)
    country_name = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    timezone = db.Column(db.String(50))
    venue_name = db.Column(db.String(200))

    # Prize money
    prize_money_usd = db.Column(db.Integer)
    prize_money_currency = db.Column(db.String(3))

    # Ranking points
    winner_points = db.Column(db.Integer)
    finalist_points = db.Column(db.Integer)
    semifinalist_points = db.Column(db.Integer)
    quarterfinalist_points = db.Column(db.Integer)

    # External IDs
    api_tennis_id = db.Column(db.String(50))
    sportradar_id = db.Column(db.String(50))
    atp_wta_url = db.Column(db.Text)

    # Metadata
    is_mandatory = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    editions = db.relationship("TournamentEdition", back_populates="tournament", lazy="dynamic")

    __table_args__ = (
        db.Index("idx_tournaments_tour", "tour"),
        db.Index("idx_tournaments_category", "category"),
        db.Index("idx_tournaments_surface", "surface"),
        db.Index("idx_tournaments_location", "latitude", "longitude"),
    )

    def to_dict(self, brief: bool = False) -> dict:
        """Serialize tournament to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "tour": self.tour,
            "category": self.category,
            "surface": self.surface,
            "city": self.city,
            "country": self.country,
            "country_name": self.country_name,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
        }
        if not brief:
            data.update(
                {
                    "indoor_outdoor": self.indoor_outdoor,
                    "draw_size": self.draw_size,
                    "venue_name": self.venue_name,
                    "prize_money_usd": self.prize_money_usd,
                    "winner_points": self.winner_points,
                    "finalist_points": self.finalist_points,
                    "semifinalist_points": self.semifinalist_points,
                    "quarterfinalist_points": self.quarterfinalist_points,
                    "is_mandatory": self.is_mandatory,
                }
            )
        return data

    def __repr__(self) -> str:
        return f"<Tournament {self.name} ({self.category})>"


class TournamentEdition(db.Model):
    """A specific year's instance of a tournament."""

    __tablename__ = "tournament_editions"

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey("tournaments.id"), nullable=False)

    # Dates
    year = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    entry_deadline = db.Column(db.Date)
    withdrawal_deadline = db.Column(db.Date)
    qualifying_start_date = db.Column(db.Date)

    # Draw specifics
    draw_size = db.Column(db.Integer)
    qualifying_draw_size = db.Column(db.Integer)

    # Prize money
    prize_money_usd = db.Column(db.Integer)

    # Status
    status = db.Column(db.String(20), default="upcoming")

    # External references
    entry_list_url = db.Column(db.Text)
    draw_url = db.Column(db.Text)
    official_site_url = db.Column(db.Text)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tournament = db.relationship("Tournament", back_populates="editions")
    entry_records = db.relationship("EntryListRecord", back_populates="tournament_edition", lazy="dynamic")
    historical_participations = db.relationship(
        "HistoricalParticipation", back_populates="tournament_edition", lazy="dynamic"
    )
    predictions = db.relationship("Prediction", back_populates="tournament_edition", lazy="dynamic")
    matches = db.relationship("Match", back_populates="tournament_edition", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint("tournament_id", "year"),
        db.Index("idx_editions_dates", "start_date", "end_date"),
        db.Index("idx_editions_year", "year"),
        db.Index("idx_editions_status", "status"),
        db.Index("idx_editions_tournament", "tournament_id"),
    )

    def to_dict(self) -> dict:
        """Serialize edition to dictionary."""
        tournament_data = self.tournament.to_dict(brief=True) if self.tournament else {}
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "year": self.year,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "draw_size": self.draw_size,
            "prize_money_usd": self.prize_money_usd,
            "tournament": tournament_data,
        }

    def __repr__(self) -> str:
        name = self.tournament.name if self.tournament else "?"
        return f"<TournamentEdition {name} {self.year}>"


class EntryListRecord(db.Model):
    """A player's entry into a specific tournament edition."""

    __tablename__ = "entry_list_records"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    tournament_edition_id = db.Column(
        db.Integer, db.ForeignKey("tournament_editions.id"), nullable=False
    )

    # Entry details
    entry_type = db.Column(db.String(30), nullable=False)
    entry_rank = db.Column(db.Integer)
    seed = db.Column(db.Integer)

    # Status tracking
    status = db.Column(db.String(20), default="entered")
    withdrawal_reason = db.Column(db.String(200))
    withdrawal_date = db.Column(db.Date)
    replaced_by_player_id = db.Column(db.Integer, db.ForeignKey("players.id"))

    # Tracking
    first_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = db.Column(db.String(100))

    # Relationships
    player = db.relationship("Player", back_populates="entry_records", foreign_keys=[player_id])
    tournament_edition = db.relationship("TournamentEdition", back_populates="entry_records")
    replaced_by = db.relationship("Player", foreign_keys=[replaced_by_player_id])

    __table_args__ = (
        db.UniqueConstraint("player_id", "tournament_edition_id"),
        db.Index("idx_entries_player", "player_id"),
        db.Index("idx_entries_edition", "tournament_edition_id"),
        db.Index("idx_entries_status", "status"),
        db.Index("idx_entries_player_status", "player_id", "status"),
    )

    def to_dict(self) -> dict:
        """Serialize entry record to dictionary."""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "tournament_edition_id": self.tournament_edition_id,
            "entry_type": self.entry_type,
            "entry_rank": self.entry_rank,
            "seed": self.seed,
            "status": self.status,
            "withdrawal_reason": self.withdrawal_reason,
            "source": self.source,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
        }

    def __repr__(self) -> str:
        return f"<EntryListRecord player={self.player_id} edition={self.tournament_edition_id} status={self.status}>"


class HistoricalParticipation(db.Model):
    """Past tournament results — training data for predictions."""

    __tablename__ = "historical_participation"

    id = db.Column(db.Integer, primary_key=True)

    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    tournament_edition_id = db.Column(
        db.Integer, db.ForeignKey("tournament_editions.id"), nullable=False
    )

    # Result
    result = db.Column(db.String(30))
    rounds_won = db.Column(db.Integer, default=0)

    # Points and prize
    ranking_points_earned = db.Column(db.Integer)
    prize_money_earned_usd = db.Column(db.Integer)

    # Context at time of tournament
    ranking_at_time = db.Column(db.Integer)
    seed_at_time = db.Column(db.Integer)

    # Points defense
    points_to_defend = db.Column(db.Integer, default=0)

    # Match details summary
    matches_played = db.Column(db.Integer, default=0)
    matches_won = db.Column(db.Integer, default=0)
    sets_played = db.Column(db.Integer, default=0)
    sets_won = db.Column(db.Integer, default=0)

    # Metadata
    data_source = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    player = db.relationship("Player", back_populates="historical_participations")
    tournament_edition = db.relationship("TournamentEdition", back_populates="historical_participations")

    __table_args__ = (
        db.UniqueConstraint("player_id", "tournament_edition_id"),
        db.Index("idx_historical_player", "player_id"),
        db.Index("idx_historical_edition", "tournament_edition_id"),
        db.Index("idx_historical_result", "result"),
        db.Index("idx_historical_player_result", "player_id", "result"),
    )

    def to_dict(self) -> dict:
        """Serialize historical participation to dictionary."""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "tournament_edition_id": self.tournament_edition_id,
            "result": self.result,
            "rounds_won": self.rounds_won,
            "ranking_points_earned": self.ranking_points_earned,
            "ranking_at_time": self.ranking_at_time,
            "seed_at_time": self.seed_at_time,
            "points_to_defend": self.points_to_defend,
            "matches_played": self.matches_played,
            "matches_won": self.matches_won,
        }


class Prediction(db.Model):
    """Predicted probability of a player entering a tournament."""

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)

    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    tournament_edition_id = db.Column(
        db.Integer, db.ForeignKey("tournament_editions.id"), nullable=False
    )

    # Prediction output
    will_enter_probability = db.Column(db.Numeric(5, 4), nullable=False)
    confidence_level = db.Column(db.String(20))
    prediction_label = db.Column(db.String(20))

    # Feature values (for explainability)
    features_json = db.Column(db.JSON)

    # Tracking
    model_version = db.Column(db.String(50))
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Evaluation
    actual_entered = db.Column(db.Boolean)
    evaluated_at = db.Column(db.DateTime)

    # Relationships
    player = db.relationship("Player", back_populates="predictions")
    tournament_edition = db.relationship("TournamentEdition", back_populates="predictions")

    __table_args__ = (
        db.UniqueConstraint("player_id", "tournament_edition_id", "model_version"),
        db.Index("idx_predictions_player", "player_id"),
        db.Index("idx_predictions_edition", "tournament_edition_id"),
        db.Index("idx_predictions_probability", will_enter_probability.desc()),
    )

    def to_dict(self) -> dict:
        """Serialize prediction to dictionary."""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "tournament_edition_id": self.tournament_edition_id,
            "will_enter_probability": float(self.will_enter_probability),
            "confidence_level": self.confidence_level,
            "prediction_label": self.prediction_label,
            "features": self.features_json,
            "model_version": self.model_version,
            "predicted_at": self.predicted_at.isoformat() if self.predicted_at else None,
            "actual_entered": self.actual_entered,
        }


class Match(db.Model):
    """A match within a tournament edition."""

    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)

    tournament_edition_id = db.Column(
        db.Integer, db.ForeignKey("tournament_editions.id"), nullable=False
    )

    # Players
    player1_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey("players.id"))

    # Match details
    round = db.Column(db.String(20), nullable=False)
    match_number = db.Column(db.Integer)
    court = db.Column(db.String(100))

    # Schedule
    scheduled_date = db.Column(db.Date)
    scheduled_time = db.Column(db.Time)
    actual_start_time = db.Column(db.DateTime)
    actual_end_time = db.Column(db.DateTime)

    # Score
    score = db.Column(db.String(100))
    sets_json = db.Column(db.JSON)

    # Status
    status = db.Column(db.String(20), default="scheduled")

    # Stats
    duration_minutes = db.Column(db.Integer)
    stats_json = db.Column(db.JSON)

    # External IDs
    api_tennis_match_id = db.Column(db.String(50))
    sportradar_match_id = db.Column(db.String(50))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tournament_edition = db.relationship("TournamentEdition", back_populates="matches")
    player1 = db.relationship("Player", foreign_keys=[player1_id])
    player2 = db.relationship("Player", foreign_keys=[player2_id])
    winner = db.relationship("Player", foreign_keys=[winner_id])

    __table_args__ = (
        db.Index("idx_matches_edition", "tournament_edition_id"),
        db.Index("idx_matches_players", "player1_id", "player2_id"),
        db.Index("idx_matches_winner", "winner_id"),
        db.Index("idx_matches_date", "scheduled_date"),
        db.Index("idx_matches_status", "status"),
    )

    def to_dict(self) -> dict:
        """Serialize match to dictionary."""
        return {
            "id": self.id,
            "tournament_edition_id": self.tournament_edition_id,
            "player1": self.player1.to_dict(brief=True) if self.player1 else None,
            "player2": self.player2.to_dict(brief=True) if self.player2 else None,
            "winner_id": self.winner_id,
            "round": self.round,
            "score": self.score,
            "status": self.status,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "duration_minutes": self.duration_minutes,
        }


class PlayerSurfaceStats(db.Model):
    """Aggregated player statistics by surface and year."""

    __tablename__ = "player_surface_stats"

    id = db.Column(db.Integer, primary_key=True)

    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    surface = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    # Win/loss
    matches_played = db.Column(db.Integer, default=0)
    matches_won = db.Column(db.Integer, default=0)
    win_percentage = db.Column(db.Numeric(5, 2))

    # Titles and deep runs
    titles = db.Column(db.Integer, default=0)
    finals = db.Column(db.Integer, default=0)
    semifinals = db.Column(db.Integer, default=0)

    # Metadata
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = db.relationship("Player", back_populates="surface_stats")

    __table_args__ = (
        db.UniqueConstraint("player_id", "surface", "year"),
        db.Index("idx_surface_stats_player", "player_id"),
    )


class RankingHistory(db.Model):
    """Weekly ranking snapshots."""

    __tablename__ = "ranking_history"

    id = db.Column(db.Integer, primary_key=True)

    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    tour = db.Column(db.String(10), nullable=False)
    ranking_date = db.Column(db.Date, nullable=False)
    singles_rank = db.Column(db.Integer)
    singles_points = db.Column(db.Integer)
    doubles_rank = db.Column(db.Integer)
    doubles_points = db.Column(db.Integer)

    # Relationships
    player = db.relationship("Player", back_populates="ranking_history")

    __table_args__ = (
        db.UniqueConstraint("player_id", "tour", "ranking_date"),
        db.Index("idx_ranking_history_player", "player_id"),
        db.Index("idx_ranking_history_date", "ranking_date"),
    )


class ScrapeLog(db.Model):
    """Track scraping runs for debugging and monitoring."""

    __tablename__ = "scrape_log"

    id = db.Column(db.Integer, primary_key=True)

    source = db.Column(db.String(100), nullable=False)
    scrape_type = db.Column(db.String(50), nullable=False)
    target_url = db.Column(db.Text)

    # Results
    status = db.Column(db.String(20), default="running")
    records_found = db.Column(db.Integer, default=0)
    records_created = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    errors_json = db.Column(db.JSON)

    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)

    __table_args__ = (
        db.Index("idx_scrape_log_source", "source"),
        db.Index("idx_scrape_log_status", "status"),
        db.Index("idx_scrape_log_date", "started_at"),
    )


class Alert(db.Model):
    """User-configured notifications."""

    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)

    # What to watch
    alert_type = db.Column(db.String(30), nullable=False)

    # Filters
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"))
    tournament_id = db.Column(db.Integer, db.ForeignKey("tournaments.id"))

    # Delivery
    delivery_method = db.Column(db.String(20), default="in_app")
    delivery_target = db.Column(db.String(200))

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_triggered_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    player = db.relationship("Player")
    tournament = db.relationship("Tournament")
