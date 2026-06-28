"""Session retention cleanup (`src/cleanup.py`) — A8; NFR-09; 17.1: 14 days.

Deletes data/sessions/{job_id}/ directories older than the retention window so
disk does not grow without bound and (potentially sensitive) persisted content
does not linger. Run as a periodic task or at startup; also a CLI:

    python -m src.cleanup --root data/sessions --days 14 [--dry-run]

Retention precedence: explicit arg > env SESSION_RETENTION_DAYS > DEFAULT (14).
Age is measured by directory mtime, which on a finished session reflects when
its last file was written (≈ end of run) — adequate for a coarse retention
sweep. A future tightening could read a created_at marker instead.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import time

from src.logging_conf import get_logger, log_event

_log = get_logger("rhcloud.cleanup")

DEFAULT_RETENTION_DAYS = 14


def _resolve_retention_days(retention_days: int | None) -> int:
    if retention_days is not None:
        return int(retention_days)
    env = os.environ.get("SESSION_RETENTION_DAYS")
    if env:
        try:
            return int(env)
        except ValueError:
            pass
    return DEFAULT_RETENTION_DAYS


def cleanup_sessions(
    sessions_root: str = "data/sessions",
    retention_days: int | None = None,
    now: float | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Delete session dirs older than the retention window. Returns deleted paths."""
    days = _resolve_retention_days(retention_days)
    now = time.time() if now is None else now
    cutoff = now - days * 86400

    if not os.path.isdir(sessions_root):
        return []

    deleted: list[str] = []
    for name in sorted(os.listdir(sessions_root)):
        path = os.path.join(sessions_root, name)
        if not os.path.isdir(path):
            continue
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if mtime >= cutoff:
            continue
        age_days = (now - mtime) / 86400
        if dry_run:
            log_event(_log, "session_cleanup_candidate", job_id=name)
            deleted.append(path)
            continue
        try:
            shutil.rmtree(path)
            deleted.append(path)
            log_event(_log, "session_deleted", job_id=name)
        except OSError as e:
            log_event(
                _log,
                "session_delete_failed",
                level=logging.ERROR,
                job_id=name,
                error_type=type(e).__name__,
            )
    log_event(_log, "session_cleanup_done")
    return deleted


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RHCLOUD session retention cleanup")
    parser.add_argument("--root", default="data/sessions")
    parser.add_argument("--days", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    deleted = cleanup_sessions(args.root, args.days, dry_run=args.dry_run)
    verb = "would delete" if args.dry_run else "deleted"
    print(f"{verb} {len(deleted)} session(s)")
    for p in deleted:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    from src.logging_conf import configure_logging

    configure_logging()
    raise SystemExit(_main())


__all__ = ["cleanup_sessions", "DEFAULT_RETENTION_DAYS"]
