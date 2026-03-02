"""Base scraper class with retry logic, rate limiting, and structured logging."""

import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import requests

from backend.extensions import db
from backend.models import ScrapeLog


class BaseScraper(ABC):
    """Base class for all scrapers."""

    def __init__(self, source_name: str, rate_limit_seconds: float = 2.0):
        self.source_name = source_name
        self.rate_limit = rate_limit_seconds
        self.last_request_time: float = 0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "CourtTracker/1.0 (tennis-research; contact@courttracker.com)"
            }
        )
        self.logger = logging.getLogger(f"scraper.{source_name}")

    def _throttle(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def fetch(self, url: str, max_retries: int = 3, **kwargs) -> requests.Response:
        """Fetch URL with retry logic and rate limiting."""
        self._throttle()
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(
                    "Attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    max_retries,
                    url,
                    e,
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                else:
                    raise

        # Should not reach here, but satisfy type checker
        raise requests.RequestException(f"All {max_retries} retries failed for {url}")

    @abstractmethod
    def scrape(self, **kwargs) -> list[dict]:
        """Override in subclass. Returns list of normalized records."""

    def run(self, **kwargs) -> list[dict]:
        """Execute scrape with logging to scrape_log table."""
        log_entry = self._start_log(kwargs)
        try:
            records = self.scrape(**kwargs)
            self._complete_log(log_entry, records)
            return records
        except Exception as e:
            self._fail_log(log_entry, e)
            raise

    def _start_log(self, kwargs: dict) -> ScrapeLog:
        """Create a scrape log entry at the start of a run."""
        log_entry = ScrapeLog(
            source=self.source_name,
            scrape_type=kwargs.get("scrape_type", "general"),
            target_url=kwargs.get("url", ""),
            status="running",
            started_at=datetime.utcnow(),
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    def _complete_log(self, log_entry: ScrapeLog, records: list[dict]) -> None:
        """Update log entry on successful completion."""
        now = datetime.utcnow()
        log_entry.status = "success"
        log_entry.records_found = len(records)
        log_entry.completed_at = now
        if log_entry.started_at:
            log_entry.duration_seconds = int(
                (now - log_entry.started_at).total_seconds()
            )
        db.session.commit()

    def _fail_log(self, log_entry: ScrapeLog, error: Exception) -> None:
        """Update log entry on failure."""
        now = datetime.utcnow()
        log_entry.status = "failed"
        log_entry.errors_json = {"error": str(error)}
        log_entry.completed_at = now
        if log_entry.started_at:
            log_entry.duration_seconds = int(
                (now - log_entry.started_at).total_seconds()
            )
        db.session.commit()
