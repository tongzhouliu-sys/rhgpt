"""Consecutive-failure alerting (`src/alerts.py`) — C9, §10.3.

Watches the event stream and raises a prominent log line when the SAME failure
class (`session_expired` / `transient` / ...) occurs N times in a row across
steps/jobs (default N=3, env ALERT_CONSECUTIVE_THRESHOLD). Any successful step
resets the streak — a working pipeline should not keep alerting.

Counting logic is pure and thread-safe so it can be unit tested without the web
layer; the default sink emits via A's structured logger (error_type + attempt
are allowlisted fields, so no message bodies leak).
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Callable, Optional

from src.logging_conf import get_logger, log_event

_log = get_logger("rhcloud.alerts")

DEFAULT_THRESHOLD = 3
# Event types that indicate forward progress and therefore clear the streak.
_PROGRESS_TYPES = {"step_succeeded", "pipeline_finished"}
_FAILURE_TYPES = {"step_failed", "fatal"}


def _default_sink(error_type: str, count: int) -> None:
    log_event(
        _log,
        "alert_consecutive_failures",
        level=logging.ERROR,
        error_type=error_type,
        attempt=count,
    )


def threshold_from_env() -> int:
    raw = os.environ.get("ALERT_CONSECUTIVE_THRESHOLD")
    if raw:
        try:
            n = int(raw)
            if n > 0:
                return n
        except ValueError:
            pass
    return DEFAULT_THRESHOLD


class AlertTracker:
    """Tracks consecutive same-type failures and fires a sink at the threshold.

    `observe(event)` returns the error_type string if an alert fired on THIS
    event, else None. The sink fires once when the streak first reaches the
    threshold and again on every further consecutive failure of that type
    (so a sustained outage keeps signalling), until a success resets it.
    """

    def __init__(
        self,
        threshold: int = DEFAULT_THRESHOLD,
        on_alert: Optional[Callable[[str, int], None]] = None,
    ):
        self.threshold = max(1, threshold)
        self._on_alert = on_alert or _default_sink
        self._lock = threading.Lock()
        self._counts: dict[str, int] = {}

    def observe(self, event: dict) -> Optional[str]:
        etype_event = event.get("type")
        if etype_event in _PROGRESS_TYPES:
            with self._lock:
                self._counts.clear()
            return None
        if etype_event not in _FAILURE_TYPES:
            return None

        error_type = (event.get("error") or {}).get("type") or "unknown"
        with self._lock:
            # A new failure class resets the others — "consecutive" is per class.
            for k in list(self._counts):
                if k != error_type:
                    self._counts[k] = 0
            count = self._counts.get(error_type, 0) + 1
            self._counts[error_type] = count
            fire = count >= self.threshold
        if fire:
            self._on_alert(error_type, count)
            return error_type
        return None

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counts)

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()


__all__ = ["AlertTracker", "DEFAULT_THRESHOLD", "threshold_from_env"]
