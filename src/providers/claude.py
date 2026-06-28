"""Claude web Provider (`src/providers/claude.py`) — B5 (P0).

Contract 1 via `_browser.run_web`. Selectors / response URL are best-effort and
must be verified against the live site (§6.4).
"""

from __future__ import annotations

from src.providers._browser import run_web
from src.providers._extract import extract_text


def _parse(body: str) -> str:
    # claude.ai streams completion events under /chat_conversations/.../completion.
    return extract_text(body)


SITE = {
    "url": "https://claude.ai/new",
    "response_match": ["/completion", "/chat_conversations"],
    "input_selector": 'div[contenteditable="true"]',
    "send_selector": 'button[aria-label="Send message"]',
    "done_selector": 'button[aria-label="Send message"]',
    "done_state": "visible",
    "login_url_match": "login",
    "login_selectors": ['button:has-text("Continue with Google")', 'input[type="email"]'],
    "assistant_selector": 'div[data-testid="assistant-message"], div.font-claude-message',
    "parse": _parse,
    "type_delay_ms": 10,
}


def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str:
    return run_web(SITE, profile, prompt, timeout_ms)


__all__ = ["run", "SITE"]
