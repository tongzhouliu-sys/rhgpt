"""Fixture provider: records max observed concurrency, used for lock tests.

If the Profile lock works, two steps sharing a profile must NEVER overlap, so
max_concurrency() must equal 1.
"""
import threading
import time

_lock = threading.Lock()
_current = 0
_max = 0
calls = []


def reset():
    global _current, _max
    with _lock:
        _current = 0
        _max = 0
    calls.clear()


def max_concurrency():
    with _lock:
        return _max


def run(profile, prompt, *, timeout_ms=120000, **options):
    global _current, _max
    with _lock:
        _current += 1
        _max = max(_max, _current)
        calls.append(profile)
    try:
        time.sleep(0.05)
        return f"# slow-ok[{profile}]\n\ndone\n"
    finally:
        with _lock:
            _current -= 1
