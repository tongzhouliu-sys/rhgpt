"""Provider site modules.

Each `src/providers/{site}.py` MUST expose exactly:

    def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str

returning the model's non-empty plain-text (Markdown) output. No abstract base
class, no inheritance — the function signature *is* the contract (契约 1, §3.1).

Kept import-light on purpose: importing this package must NOT pull in Playwright
or any heavy dependency, so A/C test paths and the stub provider stay cheap.
Provider modules are loaded lazily by ProviderManager via importlib.
"""
