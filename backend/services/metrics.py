from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock

from backend.config import get_settings


@dataclass
class MetricsStore:
    started_at: float = field(default_factory=time.time)
    upload_count: int = 0
    screen_count: int = 0
    screen_success_count: int = 0
    screen_total_ms: float = 0.0
    last_screen_ms: float | None = None
    last_screen_at: float | None = None
    screen_errors: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_upload(self) -> None:
        with self._lock:
            self.upload_count += 1

    def record_screen(self, duration_ms: float, *, error: bool = False) -> None:
        with self._lock:
            self.screen_count += 1
            if error:
                self.screen_errors += 1
            else:
                self.screen_success_count += 1
                self.screen_total_ms += duration_ms
                self.last_screen_ms = duration_ms
                self.last_screen_at = time.time()

    def snapshot(self) -> dict:
        settings = get_settings()
        with self._lock:
            avg = (
                self.screen_total_ms / self.screen_success_count
                if self.screen_success_count > 0
                else None
            )
            sla_ms = settings.screen_sla_seconds * 1000
            last = self.last_screen_ms
            return {
                "uptime_seconds": round(time.time() - self.started_at, 2),
                "upload_count": self.upload_count,
                "screen_count": self.screen_count,
                "screen_errors": self.screen_errors,
                "last_screen_ms": round(last, 2) if last is not None else None,
                "avg_screen_ms": round(avg, 2) if avg is not None else None,
                "screen_sla_seconds": settings.screen_sla_seconds,
                "sla_met_last": last is not None and last <= sla_ms,
            }


_store = MetricsStore()


def get_metrics_store() -> MetricsStore:
    return _store
