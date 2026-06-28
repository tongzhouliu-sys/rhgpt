"""Provider error-type contract (契约 1 错误类型 / §6.4 / §3.1).

FROZEN CONTRACT — Day 1 deliverable from A. Developer B implements the
*providers that raise* these and may ADD further exception types, but the
three names and their A-side handling semantics below are locked. Any change
requires three-party agreement and a sync to docs/contracts.md.

A-side handling (runtime, §5.4 [修正-4]):

    SessionExpiredError  -> FATAL: no retry, mark step failed, error.type
                            "session_expired", surface "需重新 Seeding" to user.
    GenerationTimeout    -> TRANSIENT: retry with exponential backoff up to
                            `retries`, then fail with error.type "transient".
    (any other Exception)-> TRANSIENT: same retry path as GenerationTimeout.

Only SessionExpiredError is special-cased in runtime; everything else
(including GenerationTimeout) flows through the generic transient branch.
"""

from __future__ import annotations


class ProviderError(Exception):
    """Base for all provider-raised errors. Carries the offending profile.

    B may subclass this for additional provider-specific errors; as long as
    new errors are NOT SessionExpiredError, runtime treats them as transient.
    """

    def __init__(self, profile: str, message: str | None = None):
        self.profile = profile
        super().__init__(message or f"{type(self).__name__}(profile={profile!r})")


class SessionExpiredError(ProviderError):
    """Login state is invalid (redirected to login / login control present).

    FATAL class — runtime does NOT retry; the session must be re-seeded.
    """


class GenerationTimeout(ProviderError):
    """The model's generation-complete signal did not arrive in time.

    TRANSIENT class — runtime retries with exponential backoff.
    """


__all__ = ["ProviderError", "SessionExpiredError", "GenerationTimeout"]
