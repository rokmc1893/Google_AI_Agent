from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class InMemoryRateLimiter:
    """Small demo-only limiter.

    This is intentionally process-local so the demo does not need Redis or an
    external gateway. Production deployments should replace this with a shared
    store-backed limiter.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._upload_events: dict[str, deque[float]] = defaultdict(deque)
        self._active_screenings = 0

    def allow_upload(
        self,
        client_id: str,
        limit_per_minute: int,
        now: float | None = None,
    ) -> RateLimitDecision:
        if limit_per_minute <= 0:
            return RateLimitDecision(allowed=True)

        current = now if now is not None else time.monotonic()
        window_start = current - 60

        with self._lock:
            events = self._upload_events[client_id]
            while events and events[0] <= window_start:
                events.popleft()

            if len(events) >= limit_per_minute:
                retry_after = max(1, int(60 - (current - events[0])))
                return RateLimitDecision(
                    allowed=False,
                    retry_after_seconds=retry_after,
                )

            events.append(current)
            return RateLimitDecision(allowed=True)

    def try_acquire_screening(self, max_concurrent: int) -> bool:
        if max_concurrent <= 0:
            return True

        with self._lock:
            if self._active_screenings >= max_concurrent:
                return False
            self._active_screenings += 1
            return True

    def release_screening(self) -> None:
        with self._lock:
            self._active_screenings = max(0, self._active_screenings - 1)

    @property
    def active_screenings(self) -> int:
        with self._lock:
            return self._active_screenings


_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    return _rate_limiter
