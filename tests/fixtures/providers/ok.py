"""Fixture provider: always succeeds with deterministic non-empty Markdown."""
import hashlib

calls = []


def reset():
    calls.clear()


def run(profile, prompt, *, timeout_ms=120000, **options):
    calls.append((profile, prompt))
    fp = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
    return f"# ok[{profile or 'api'}] {fp}\n\nanswer for: {len(prompt)} chars\n"
