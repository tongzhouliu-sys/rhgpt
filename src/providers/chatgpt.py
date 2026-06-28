"""ChatGPT web Provider (`src/providers/chatgpt.py`) — B4 (P0).

Contract 1: `run(profile, prompt, *, timeout_ms, **options) -> str`. Delegates to
the shared engine in `_browser.run_web`. Selectors and the backend response URL
are best-effort and MUST be re-verified against the live site (§6.4 note).
"""

from __future__ import annotations

from src.providers._browser import run_web
from src.providers._extract import extract_text


def _parse(body: str) -> str:
    # ChatGPT streams SSE frames from backend-api/conversation; the assistant
    # text lives under message.content.parts[]. The generic extractor handles
    # the common shapes; verify against the live stream.
    return extract_text(body)


SITE = {
    "url": "https://chatgpt.com/",
    "response_match": ["backend-api/conversation", "backend-anon/conversation"],
    "input_selector": 'div[contenteditable="true"]',
    "send_selector": 'button[data-testid="send-button"]',
    "done_selector": 'button[data-testid="send-button"]',  # re-enabled when done
    "done_state": "visible",
    "login_url_match": "auth.openai.com",
    "login_selectors": ['button[data-testid="login-button"]', 'a[href*="/auth/login"]'],
    "assistant_selector": 'div[data-message-author-role="assistant"]',
    "parse": _parse,
    "type_delay_ms": 10,
}


def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str:
    return run_web(SITE, profile, prompt, timeout_ms)


__all__ = ["run", "SITE"]
