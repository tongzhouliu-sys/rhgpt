"""DeepSeek web Provider (`src/providers/deepseek.py`) — B6 (backfill).

Contract 1 via `_browser.run_web`. Selectors / response URL best-effort; verify
against the live site (§6.4).
"""

from __future__ import annotations

from src.providers._browser import run_web
from src.providers._extract import extract_text


def _parse(body: str) -> str:
    return extract_text(body)


SITE = {
    "url": "https://chat.deepseek.com/",
    "response_match": ["/api/v0/chat/completion", "/chat/completion"],
    "input_selector": "textarea#chat-input, textarea",
    "send_selector": None,  # Enter submits
    "done_selector": 'div[class*="ds-icon"] svg, button[aria-label="regenerate"]',
    "done_state": "visible",
    "login_url_match": "/sign_in",
    "login_selectors": ['button:has-text("Log in")', 'input[type="password"]'],
    "assistant_selector": 'div[class*="markdown"]',
    "parse": _parse,
    "type_delay_ms": 8,
}


def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str:
    return run_web(SITE, profile, prompt, timeout_ms)


__all__ = ["run", "SITE"]
