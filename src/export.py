"""Export (`src/export.py`) — C5, 17.1 决策 (单步 / 合并 / JSON).

Reads the session artifacts that A's runtime persisted (NN_{key}_response.md,
NN_{key}_error.json, context.json, events.jsonl) and produces the three export
shapes. Pure / framework-free so it is unit-testable without FastAPI; main.py
wraps these in HTTP responses with the right Content-Type / filename.

  steps  -> zip of each step's .md (independent per-model review)
  merged -> one concatenated .md (the user-facing final result)
  json   -> context.json structure (for systems / downstream)
"""

from __future__ import annotations

import io
import json
import os
import re
import zipfile

_RESP_RE = re.compile(r"^(\d+)_(?P<key>.+)_response\.md$")
_ERR_RE = re.compile(r"^(\d+)_(?P<key>.+)_error\.json$")


class ExportError(Exception):
    """Raised when a session cannot be exported (e.g. missing/empty)."""


def _require_dir(session_dir: str) -> None:
    if not os.path.isdir(session_dir):
        raise ExportError(f"session not found: {session_dir}")


def key_provider_map(session_dir: str) -> dict[str, str]:
    """Map step key -> provider name by reading events.jsonl (best effort)."""
    mapping: dict[str, str] = {}
    path = os.path.join(session_dir, "events.jsonl")
    if not os.path.isfile(path):
        return mapping
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            key, provider = ev.get("key"), ev.get("provider")
            if key and provider:
                mapping.setdefault(key, provider)
    return mapping


def list_step_responses(session_dir: str) -> list[tuple[int, str, str]]:
    """Return [(index, key, abspath)] for each *_response.md, ordered by index."""
    _require_dir(session_dir)
    items: list[tuple[int, str, str]] = []
    for fn in os.listdir(session_dir):
        m = _RESP_RE.match(fn)
        if m:
            items.append((int(m.group(1)), m.group("key"), os.path.join(session_dir, fn)))
    items.sort(key=lambda t: t[0])
    return items


def list_step_errors(session_dir: str) -> list[tuple[int, str, str]]:
    """Return [(index, key, abspath)] for each *_error.json, ordered by index."""
    _require_dir(session_dir)
    items: list[tuple[int, str, str]] = []
    for fn in os.listdir(session_dir):
        m = _ERR_RE.match(fn)
        if m:
            items.append((int(m.group(1)), m.group("key"), os.path.join(session_dir, fn)))
    items.sort(key=lambda t: t[0])
    return items


def build_merged_markdown(session_dir: str, title: str | None = None) -> str:
    """Concatenate all step responses (in order) into a single Markdown doc."""
    responses = list_step_responses(session_dir)
    providers = key_provider_map(session_dir)
    errors = {key: path for _, key, path in list_step_errors(session_dir)}

    parts: list[str] = []
    if title:
        parts.append(f"# {title}\n")

    # Include the original question if context.json is present.
    try:
        ctx = read_context(session_dir)
        q = ctx.get("user_question")
        if q:
            parts.append(f"> **问题**：{q}\n")
    except ExportError:
        pass

    for index, key, path in responses:
        provider = providers.get(key)
        heading = f"## {index:02d} · {key}"
        if provider:
            heading += f" ({provider})"
        with open(path, "r", encoding="utf-8") as f:
            body = f.read().rstrip()
        parts.append(f"{heading}\n\n{body}\n")

    # Surface any failed steps so the merged doc is complete, not silently short.
    for key, path in errors.items():
        with open(path, "r", encoding="utf-8") as f:
            try:
                err = json.load(f)
            except json.JSONDecodeError:
                err = {"type": "unknown", "message": "(unreadable error.json)"}
        parts.append(
            f"## ⚠️ {key} 失败\n\n- type: `{err.get('type')}`\n"
            f"- message: {err.get('message')}\n"
        )

    if not responses and not errors:
        raise ExportError(f"no step outputs to export in {session_dir}")

    return "\n".join(parts).rstrip() + "\n"


def build_steps_zip(session_dir: str) -> bytes:
    """Zip every per-step response (and any error.json) for independent review."""
    responses = list_step_responses(session_dir)
    errors = list_step_errors(session_dir)
    if not responses and not errors:
        raise ExportError(f"no step outputs to export in {session_dir}")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _, _, path in responses:
            zf.write(path, arcname=os.path.basename(path))
        for _, _, path in errors:
            zf.write(path, arcname=os.path.basename(path))
    return buf.getvalue()


def read_context(session_dir: str) -> dict:
    """Return the parsed context.json, or raise ExportError if missing/invalid."""
    _require_dir(session_dir)
    path = os.path.join(session_dir, "context.json")
    if not os.path.isfile(path):
        raise ExportError(f"context.json not found in {session_dir}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ExportError(f"context.json is not valid JSON: {e}") from e


# Modes recognized by the HTTP layer.
MODES = ("steps", "merged", "json")


__all__ = [
    "ExportError",
    "MODES",
    "key_provider_map",
    "list_step_responses",
    "list_step_errors",
    "build_merged_markdown",
    "build_steps_zip",
    "read_context",
]
