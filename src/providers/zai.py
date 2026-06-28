"""z.ai (chat.z.ai) web Provider (`src/providers/zai.py`) — B6 (backfill).

Contract 1 via `_browser.run_web`. Selectors / response URL best-effort; verify
against the live site (§6.4).
"""

from __future__ import annotations

from src.providers._browser import run_web
from src.providers._extract import extract_text


def _parse(body: str) -> str:
    return extract_text(body)


SITE = {
    "url": "https://chat.z.ai/",
    "response_match": ["/api/chat/completions", "/v1/chat/completions"],
    "input_selector": "textarea",
    "send_selector": 'button[type="submit"]',
    "done_selector": 'button[type="submit"]:not([disabled])',
    "done_state": "visible",
    "login_url_match": "/auth",
    "login_selectors": ['button:has-text("Sign in")', 'input[type="password"]'],
    "assistant_selector": 'div[class*="markdown"], div[class*="prose"]',
    "parse": _parse,
    "type_delay_ms": 8,
}


def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str:
    return run_web(SITE, profile, prompt, timeout_ms)


__all__ = ["run", "SITE"]
