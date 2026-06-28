"""Stub emit helpers (A2) for B/C parallel development & A's own tests.

Contract 2 has C inject `emit`, which (in production) appends each event to
events.jsonl and forwards it to SSE. During parallel work — and in A's
integration tests — these stand-ins let runtime be driven without C's main.py.

  make_recording_emit() -> (emit, events)
      In-memory only. `events` is a live list the caller can assert against.

  make_file_emit(session_dir) -> (emit, events)
      Simulates C's role: records in memory AND appends to
      {session_dir}/events.jsonl (so the on-disk event log can be verified).

  print_emit(ev)
      Append-to-stdout sink for ad-hoc manual runs.

Note: runtime assigns `seq` before calling emit; these stubs only persist what
they receive (they never renumber).
"""

from __future__ import annotations

import json
import os
from typing import Callable


def make_recording_emit() -> tuple[Callable[[dict], None], list[dict]]:
    events: list[dict] = []

    def emit(ev: dict) -> None:
        events.append(ev)

    return emit, events


def make_file_emit(session_dir: str) -> tuple[Callable[[dict], None], list[dict]]:
    os.makedirs(session_dir, exist_ok=True)
    path = os.path.join(session_dir, "events.jsonl")
    events: list[dict] = []

    def emit(ev: dict) -> None:
        events.append(ev)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    return emit, events


def print_emit(ev: dict) -> None:
    print(json.dumps(ev, ensure_ascii=False))


__all__ = ["make_recording_emit", "make_file_emit", "print_emit"]
