"""Fixture provider: fails (transient) the first N calls, then succeeds.

N is taken from the profile string "flaky:N" (default 1). Call counts are kept
per profile in module state; reset() clears them between tests.
"""
_attempts = {}
calls = []


def reset():
    _attempts.clear()
    calls.clear()


def _fail_target(profile):
    if profile and profile.startswith("flaky:"):
        try:
            return int(profile.split(":", 1)[1])
        except ValueError:
            return 1
    return 1


def run(profile, prompt, *, timeout_ms=120000, **options):
    calls.append((profile, prompt))
    n = _attempts.get(profile, 0) + 1
    _attempts[profile] = n
    if n <= _fail_target(profile):
        raise RuntimeError(f"transient flake {n}")
    return f"# flaky-ok after {n} attempt(s)\n\ndone\n"
