"""Per-domain rate limiting for scrapers."""

import time
import threading


class RateLimiter:
    """Thread-safe per-domain rate limiter."""

    def __init__(self) -> None:
        self._last_request: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, domain: str, min_interval: float) -> None:
        """Block until enough time has passed since the last request to this domain."""
        with self._lock:
            now = time.time()
            last = self._last_request.get(domain, 0)
            elapsed = now - last
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            self._last_request[domain] = time.time()


# Global rate limiter instance
rate_limiter = RateLimiter()
