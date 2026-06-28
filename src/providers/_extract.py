"""Tolerant extraction of assistant text from a captured response body.

Each web backend streams a different shape (SSE `data:` lines, a single JSON
doc, NDJSON). Real field paths must be verified against each site's live API;
this helper covers the common shapes so a Provider's `parse` is a thin wrapper.
Returns "" when nothing text-like is found (caller then tries DOM fallback).
"""

from __future__ import annotations

import json
from typing import Any

# Keys that commonly carry assistant text or streamed deltas, in priority order.
_TEXT_KEYS = (
    "content",
    "text",
    "completion",
    "delta",
    "parts",
    "answer",
    "response",
    "message",
)


def _collect_strings(obj: Any, out: list[str]) -> None:
    """Walk a JSON value, appending strings found under known text keys."""
    if isinstance(obj, dict):
        # OpenAI-style: choices[].message.content / choices[].delta.content;
        # ChatGPT web: message.content.parts (list of strings).
        for k in _TEXT_KEYS:
            v = obj.get(k)
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        out.append(item)
                    elif isinstance(item, (dict, list)):
                        _collect_strings(item, out)
            elif isinstance(v, dict):
                _collect_strings(v, out)
        for k, v in obj.items():
            if k in _TEXT_KEYS:
                continue
            if isinstance(v, (dict, list)):
                _collect_strings(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_strings(item, out)


def _from_json_obj(obj: Any) -> str:
    parts: list[str] = []
    _collect_strings(obj, parts)
    # De-dupe consecutive identical fragments (streamed cumulative snapshots).
    cleaned: list[str] = []
    for p in parts:
        if p and (not cleaned or cleaned[-1] != p):
            cleaned.append(p)
    return "".join(cleaned).strip()


def extract_text(body: str) -> str:
    body = (body or "").strip()
    if not body:
        return ""

    # 1) Whole body is a single JSON document.
    try:
        return _from_json_obj(json.loads(body))
    except (json.JSONDecodeError, ValueError):
        pass

    # 2) SSE / NDJSON: accumulate text across data frames.
    chunks: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        if line in ("[DONE]", "data: [DONE]"):
            continue
        try:
            frag = _from_json_obj(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
        if frag:
            chunks.append(frag)

    # Streamed deltas concatenate; cumulative snapshots -> take the longest.
    if not chunks:
        return ""
    joined = "".join(chunks).strip()
    longest = max(chunks, key=len)
    return longest if len(longest) >= len(joined) else joined


__all__ = ["extract_text"]
