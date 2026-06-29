"""Session + profile-cache cleanup (`src/cleanup.py`) — A8; NFR-09; 17.1: 14 days.

Two sweeps that keep the (small) Railway Volume from filling up — a full disk is
what makes `os.makedirs(session_dir)` raise OSError(ENOSPC) and every POST /jobs
500:

  1. cleanup_sessions(...)        — delete data/sessions/{job_id}/ older than the
     retention window so per-run artifacts do not linger.
  2. cleanup_profile_caches(...)  — prune the Chromium *cache* subdirs that
     accumulate inside the persistent web-provider login profiles. This is the
     real disk hog (caches grow unbounded inside ACTIVE profiles). It is SAFE:
     it only removes pure performance caches (Cache / Code Cache / GPUCache …)
     and never touches Cookies / Local Storage / IndexedDB, so logins survive.
     Deleting whole orphan profiles (not referenced in providers.yaml) is opt-in
     via --delete-orphans, because deleting an active account dir logs it out and
     requires re-seeding (scripts/seed_session.py).

CLI (one command can do both, suitable for a single Railway Cron Service):

    python -m src.cleanup --root data/sessions --days 14 \
        --profiles-root data/profiles --providers config/providers.yaml [--dry-run]

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

# Pure Chromium performance caches: safe to delete anywhere inside a profile —
# the browser rebuilds them on next launch (only cost: a slightly slower first
# load). Matched by directory *name* at any depth under the profile. This set is
# the conservative default and NEVER includes login state (Cookies / Local
# Storage / IndexedDB).
PROFILE_CACHE_DIR_NAMES = frozenset({
    "Cache",
    "Code Cache",
    "GPUCache",
    "ShaderCache",
    "GrShaderCache",
    "DawnCache",
    "DawnGraphiteCache",
    "DawnWebGPUCache",
})

# Slightly more aggressive: the Service Worker CacheStorage/ScriptCache is bulky
# but re-registered on demand. Opt-in only (--include-service-worker), since a
# few sites lean on it for session continuity.
PROFILE_SW_DIR_NAMES = frozenset({"Service Worker"})

# Hard guard: never delete a directory whose name holds auth / persistent state,
# regardless of any future change to the cache set above.
PROFILE_PROTECTED_DIR_NAMES = frozenset({
    "Cookies",
    "Local Storage",
    "IndexedDB",
    "Session Storage",
    "Local State",
    "Login Data",
    "Web Data",
    "Sessions",
})


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


def _active_profile_names(providers_path: str) -> set[str]:
    """Basenames of the non-empty `profile:` paths referenced in providers.yaml.

    These are live web-provider logins; their directories must never be deleted
    wholesale (only their caches are pruned). Best-effort: a missing/unreadable
    providers file yields an empty set, which makes orphan deletion a no-op for
    safety (we only delete orphans we are sure are not referenced).
    """
    try:
        import yaml

        with open(providers_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except (OSError, ValueError):
        return set()
    providers = cfg.get("providers", cfg) if isinstance(cfg, dict) else {}
    names: set[str] = set()
    if isinstance(providers, dict):
        for conf in providers.values():
            profile = (conf or {}).get("profile") if isinstance(conf, dict) else None
            if isinstance(profile, str) and profile.strip():
                names.add(os.path.basename(profile.rstrip("/")))
    return names


def _prune_cache_dirs(profile_dir: str, cache_names: frozenset[str], dry_run: bool) -> int:
    """Delete cache subdirs (by name) anywhere under `profile_dir`. Returns count."""
    removed = 0
    # topdown=True so we can skip descending into a dir we just removed.
    for dirpath, dirnames, _ in os.walk(profile_dir, topdown=True):
        for name in list(dirnames):
            if name in PROFILE_PROTECTED_DIR_NAMES:
                dirnames.remove(name)  # never touch / descend into login state
                continue
            if name in cache_names:
                target = os.path.join(dirpath, name)
                dirnames.remove(name)  # do not descend into what we delete
                if dry_run:
                    removed += 1
                    continue
                try:
                    shutil.rmtree(target)
                    removed += 1
                except OSError as e:
                    _log.error(
                        "profile_cache_delete_failed: %s (%s)", target, type(e).__name__
                    )
    return removed


def cleanup_profile_caches(
    profiles_root: str = "data/profiles",
    providers_path: str = "config/providers.yaml",
    *,
    include_service_worker: bool = False,
    delete_orphans: bool = False,
    dry_run: bool = False,
) -> dict[str, int]:
    """Prune Chromium caches inside web-provider profiles to reclaim disk.

    SAFE by default: only pure-performance cache dirs are removed; login state
    (Cookies / Local Storage / IndexedDB) is preserved, so providers stay logged
    in. `delete_orphans=True` additionally removes whole profile dirs that are
    NOT referenced in providers.yaml (e.g. `_default`, stale test accounts).

    Returns counts: {"caches_removed", "orphans_removed"}.
    """
    cache_names = PROFILE_CACHE_DIR_NAMES | (PROFILE_SW_DIR_NAMES if include_service_worker else frozenset())
    result = {"caches_removed": 0, "orphans_removed": 0}
    if not os.path.isdir(profiles_root):
        return result

    active = _active_profile_names(providers_path)
    for name in sorted(os.listdir(profiles_root)):
        profile_dir = os.path.join(profiles_root, name)
        if not os.path.isdir(profile_dir):
            continue

        is_orphan = name not in active
        if delete_orphans and is_orphan:
            if dry_run:
                _log.info("profile_orphan_candidate: %s", name)
                result["orphans_removed"] += 1
                continue
            try:
                shutil.rmtree(profile_dir)
                result["orphans_removed"] += 1
                _log.info("profile_orphan_deleted: %s", name)
            except OSError as e:
                _log.error("profile_orphan_delete_failed: %s (%s)", name, type(e).__name__)
            continue

        result["caches_removed"] += _prune_cache_dirs(profile_dir, cache_names, dry_run)

    _log.info(
        "profile_cleanup_done: %d cache dir(s), %d orphan(s)",
        result["caches_removed"],
        result["orphans_removed"],
    )
    return result


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RHCLOUD session + profile-cache cleanup"
    )
    parser.add_argument("--root", default="data/sessions", help="sessions root")
    parser.add_argument("--days", type=int, default=None, help="session retention days")
    parser.add_argument(
        "--profiles-root",
        default=os.environ.get("PROFILES_ROOT", "data/profiles"),
        help="web-provider profiles root (empty string to skip profile cleanup)",
    )
    parser.add_argument(
        "--providers",
        default=os.environ.get("PROVIDERS_PATH", "config/providers.yaml"),
        help="providers.yaml used to tell active profiles from orphans",
    )
    parser.add_argument("--include-service-worker", action="store_true")
    parser.add_argument(
        "--delete-orphans",
        action="store_true",
        help="also delete whole profile dirs not referenced in providers.yaml",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    verb = "would delete" if args.dry_run else "deleted"

    deleted = cleanup_sessions(args.root, args.days, dry_run=args.dry_run)
    print(f"{verb} {len(deleted)} session(s)")
    for p in deleted:
        print(f"  {p}")

    if args.profiles_root:
        pr = cleanup_profile_caches(
            args.profiles_root,
            args.providers,
            include_service_worker=args.include_service_worker,
            delete_orphans=args.delete_orphans,
            dry_run=args.dry_run,
        )
        print(
            f"{verb} {pr['caches_removed']} profile cache dir(s)"
            f" and {pr['orphans_removed']} orphan profile(s)"
        )
    return 0


if __name__ == "__main__":
    from src.logging_conf import configure_logging

    configure_logging()
    raise SystemExit(_main())


__all__ = [
    "cleanup_sessions",
    "cleanup_profile_caches",
    "DEFAULT_RETENTION_DAYS",
]
