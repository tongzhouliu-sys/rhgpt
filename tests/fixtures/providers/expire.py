"""Fixture provider: always raises SessionExpiredError (fatal class)."""
from src.providers._errors import SessionExpiredError

calls = []


def reset():
    calls.clear()


def run(profile, prompt, *, timeout_ms=120000, **options):
    calls.append((profile, prompt))
    raise SessionExpiredError(profile)
