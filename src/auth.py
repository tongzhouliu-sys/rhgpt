"""HMAC request authentication (`src/auth.py`) — C2, §9.1 / 契约 3 (17.1 决策).

Scheme (frozen in docs/contracts.md, contract 3):

    X-Api-Key:    <identity>
    X-Timestamp:  <unix seconds>
    X-Signature:  hex( HMAC-SHA256(secret, canonical) )
    canonical = METHOD + "\\n" + PATH + "\\n" + X-Timestamp + "\\n" + sha256_hex(body)

Server verifies: identity known -> signature matches (constant-time) AND
|now - timestamp| <= max_skew (default 300s, replay window).

This module is deliberately framework-free (stdlib only) so it can be unit
tested without FastAPI and reused by any transport. main.py adapts FastAPI
Request/Headers onto verify_request().
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time


class AuthError(Exception):
    """Authentication failure. `status` maps to the HTTP code main.py returns."""

    def __init__(self, message: str, status: int = 401):
        super().__init__(message)
        self.status = status
        self.message = message


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body or b"").hexdigest()


def canonical_string(method: str, path: str, timestamp: str, body: bytes) -> str:
    """Build the canonical string to sign. PATH is the URL path WITHOUT query."""
    return "\n".join([method.upper(), path, str(timestamp), sha256_hex(body)])


def sign(secret: str, method: str, path: str, timestamp: str, body: bytes) -> str:
    canonical = canonical_string(method, path, timestamp, body)
    return hmac.new(
        secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def load_keystore_from_env() -> dict[str, str]:
    """Load api_key -> secret pairs from the environment.

    Two accepted forms (RHCLOUD_API_KEYS wins if both present):
      RHCLOUD_API_KEYS="key1:secret1,key2:secret2"
      RHCLOUD_API_KEY="key1" + RHCLOUD_API_SECRET="secret1"

    Secrets never live in code/config/Git (§9.3) — only the environment.
    """
    raw = os.environ.get("RHCLOUD_API_KEYS")
    if raw:
        store: dict[str, str] = {}
        for pair in raw.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if ":" not in pair:
                raise ValueError(f"RHCLOUD_API_KEYS entry missing ':' -> {pair!r}")
            k, s = pair.split(":", 1)
            store[k.strip()] = s.strip()
        if not store:
            raise ValueError("RHCLOUD_API_KEYS produced no key/secret pairs")
        return store

    key = os.environ.get("RHCLOUD_API_KEY")
    secret = os.environ.get("RHCLOUD_API_SECRET")
    if key and secret:
        return {key: secret}

    raise ValueError(
        "No API credentials configured: set RHCLOUD_API_KEYS or "
        "RHCLOUD_API_KEY + RHCLOUD_API_SECRET"
    )


def verify_request(
    keystore: dict[str, str],
    method: str,
    path: str,
    *,
    api_key: str | None,
    timestamp: str | None,
    signature: str | None,
    body: bytes,
    now: float | None = None,
    max_skew: int = 300,
) -> str:
    """Verify a signed request. Returns the authenticated api_key on success,
    raises AuthError(401) otherwise. Fail-closed: any missing/invalid input is
    rejected with a generic message (no oracle about which part failed)."""
    if not api_key or not timestamp or not signature:
        raise AuthError("missing authentication headers")

    secret = keystore.get(api_key)
    if not secret:
        raise AuthError("unknown api key")

    # Timestamp must be an int and within the replay window.
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        raise AuthError("invalid timestamp")
    current = time.time() if now is None else now
    if abs(current - ts) > max_skew:
        raise AuthError("timestamp outside allowed window")

    expected = sign(secret, method, path, timestamp, body)
    # Constant-time comparison to avoid timing side channels.
    if not hmac.compare_digest(expected, signature):
        raise AuthError("signature mismatch")

    return api_key


__all__ = [
    "AuthError",
    "sha256_hex",
    "canonical_string",
    "sign",
    "load_keystore_from_env",
    "verify_request",
]
