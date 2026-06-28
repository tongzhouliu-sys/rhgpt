"""M1 stub provider (A2 deliverable).

A fixed-return Provider used to exercise the whole kernel end-to-end *without*
any real model, browser automation, or network. It is the "桩 provider" that
B and C reference during parallel development, and it lets A satisfy the DoD
"仅用桩 Provider 即可跑通最短 Pipeline 并完整落盘".

Contract: implements the frozen `run(profile, prompt, *, timeout_ms, **opts)`.
Output is deterministic (same prompt -> same text) and always non-empty.
"""

from __future__ import annotations

import hashlib


def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str:
    fingerprint = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
    label = profile or "api"
    # Deterministic, non-empty Markdown. We intentionally do NOT echo the full
    # prompt back (it can be large and may carry sensitive content); only a
    # length + fingerprint, so the stub is debuggable yet privacy-preserving.
    return (
        f"# [stub:{label}] deterministic response\n\n"
        f"This is a fixed stub answer produced without calling any model.\n\n"
        f"- prompt_chars: {len(prompt)}\n"
        f"- prompt_fingerprint: {fingerprint}\n"
        f"- timeout_ms: {timeout_ms}\n"
    )
