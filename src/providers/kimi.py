"""Kimi (kimi.com) web Provider (`src/providers/kimi.py`) — B6 (backfill).

Contract 1 via `_browser.run_web`. Selectors / response URL best-effort; verify
against the live site (§6.4).
"""

from __future__ import annotations

from src.providers._browser import run_web
from src.providers._extract import extract_text


def _parse(body: str) -> str:
    return extract_text(body)


SITE = {
    "url": "https://kimi.com/",
    "response_match": ["/api/chat/", "/completion/stream"],
    "input_selector": 'div[contenteditable="true"], textarea',
    "send_selector": 'div[class*="send"], button[class*="send"]',
    "done_selector": 'div[class*="send-button"]:not([class*="disabled"])',
    "done_state": "visible",
    "login_url_match": "/login",
    "login_selectors": ['button:has-text("登录")', 'input[type="tel"]'],
    "assistant_selector": 'div[class*="markdown"], div[class*="segment-assistant"]',
    "parse": _parse,
    "type_delay_ms": 8,
}


def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str:
    return run_web(SITE, profile, prompt, timeout_ms)


__all__ = ["run", "SITE"]
