"""Structured logging + minimal in-process metrics (`src/logging_conf.py`) — A9.

§10.1 Logging: one JSON object per line with exactly these fields when present:
    ts, level, logger, event, job_id, step_key, provider, site,
    attempt, duration_ms, error_type
Prompt/Response BODIES are never logged (privacy + volume, §9.5/§10.1); bodies
live only in the persisted *_prompt.md / *_response.md files.

§10.2 Metrics (minimal set, derivable from logs but also exposed in-process so
C's /health or a future /metrics can read them without a full monitoring stack):
    jobs_total, jobs_failed_total, step_duration_seconds{provider,site},
    step_retries_total, session_expired_total{provider}, active_jobs
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from datetime import datetime, timezone

# Allowlisted structured fields (anything else on the record is ignored, so we
# never leak internal LogRecord attributes or message bodies).
_STRUCT_FIELDS = (
    "event",
    "job_id",
    "step_key",
    "provider",
    "site",
    "attempt",
    "duration_ms",
    "error_type",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
        }
        # record.getMessage() is the human message; "event" (structured) takes
        # precedence as the machine-readable event name when provided.
        msg = record.getMessage()
        if msg:
            payload["msg"] = msg
        for field in _STRUCT_FIELDS:
            val = record.__dict__.get(field)
            if val is not None:
                payload[field] = val
        return json.dumps(payload, ensure_ascii=False)


_configured = False
_configure_guard = threading.Lock()


def configure_logging(level: int | str = "INFO", stream=None) -> None:
    """Idempotently install the JSON handler on the root logger."""
    global _configured
    with _configure_guard:
        if _configured:
            return
        handler = logging.StreamHandler(stream or sys.stdout)
        handler.setFormatter(JsonFormatter())
        root = logging.getLogger()
        root.handlers[:] = [handler]
        root.setLevel(level)
        _configured = True


def get_logger(name: str = "rhcloud") -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    job_id: str | None = None,
    step_key: str | None = None,
    provider: str | None = None,
    site: str | None = None,
    attempt: int | None = None,
    duration_ms: int | None = None,
    error_type: str | None = None,
) -> None:
    """Emit a structured event line. Never pass prompt/response bodies here."""
    logger.log(
        level,
        event,
        extra={
            "event": event,
            "job_id": job_id,
            "step_key": step_key,
            "provider": provider,
            "site": site,
            "attempt": attempt,
            "duration_ms": duration_ms,
            "error_type": error_type,
        },
    )


def _label_key(name: str, labels: dict) -> str:
    if not labels:
        return name
    parts = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    return f"{name}{{{parts}}}"


class Metrics:
    """Tiny thread-safe in-process metric registry (counters/gauges/histograms).

    Not Prometheus — deliberately dependency-free for V1. snapshot() returns a
    plain dict suitable for JSON exposure or test assertions.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._hist: dict[str, list[float]] = {}

    def inc(self, name: str, value: float = 1.0, **labels) -> None:
        key = _label_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value

    def set_gauge(self, name: str, value: float, **labels) -> None:
        key = _label_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, value: float, **labels) -> None:
        key = _label_key(name, labels)
        with self._lock:
            self._hist.setdefault(key, []).append(value)

    def snapshot(self) -> dict:
        with self._lock:
            hist = {}
            for k, vals in self._hist.items():
                n = len(vals)
                hist[k] = {
                    "count": n,
                    "sum": sum(vals),
                    "avg": (sum(vals) / n) if n else 0.0,
                    "max": max(vals) if n else 0.0,
                }
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": hist,
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._hist.clear()


# Canonical metric names (§10.2)
M_JOBS_TOTAL = "jobs_total"
M_JOBS_FAILED_TOTAL = "jobs_failed_total"
M_STEP_DURATION_SECONDS = "step_duration_seconds"
M_STEP_RETRIES_TOTAL = "step_retries_total"
M_SESSION_EXPIRED_TOTAL = "session_expired_total"
M_ACTIVE_JOBS = "active_jobs"

# Process-wide singleton.
metrics = Metrics()


__all__ = [
    "JsonFormatter",
    "configure_logging",
    "get_logger",
    "log_event",
    "Metrics",
    "metrics",
    "M_JOBS_TOTAL",
    "M_JOBS_FAILED_TOTAL",
    "M_STEP_DURATION_SECONDS",
    "M_STEP_RETRIES_TOTAL",
    "M_SESSION_EXPIRED_TOTAL",
    "M_ACTIVE_JOBS",
]
