#!/usr/bin/env python3
"""M1 smoke test (A2) — run the kernel end-to-end with the stub Provider.

No model, no browser, no network. Proves the DoD item: "仅用桩 Provider 即可
跑通最短 Pipeline 并完整落盘". It builds a throwaway 2-step prompt chain + a
pipeline that points at `stub_1` (from config/providers.yaml), executes
run_pipeline() with a file-backed emit (standing in for C), then prints every
persisted artifact so the operator can eyeball the M1 output set.

Run from the repo root:

    python scripts/smoke_stub.py
"""

from __future__ import annotations

import os
import sys
import tempfile

# Allow running as `python scripts/smoke_stub.py` from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.builder import PromptBuilder  # noqa: E402
from src.manager import ProviderManager  # noqa: E402
from src.runtime import run_pipeline  # noqa: E402
from src.stubs import make_file_emit  # noqa: E402

PROMPT_1 = "User question:\n\n{{user_question}}\n\nAnswer concisely.\n"
PROMPT_2 = "Refine the previous answer:\n\n{{s1}}\n\n(original: {{user_question}})\n"
PIPELINE = """\
name: "M1 stub smoke (2-step)"
steps:
  - key: s1
    provider: stub_1
    prompt: smoke_p1
  - key: s2
    provider: stub_1
    prompt: smoke_p2
"""


def main() -> int:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    providers_yaml = os.path.join(repo_root, "config", "providers.yaml")

    with tempfile.TemporaryDirectory() as work:
        prompts_dir = os.path.join(work, "prompts")
        os.makedirs(prompts_dir)
        with open(os.path.join(prompts_dir, "smoke_p1.md"), "w", encoding="utf-8") as f:
            f.write(PROMPT_1)
        with open(os.path.join(prompts_dir, "smoke_p2.md"), "w", encoding="utf-8") as f:
            f.write(PROMPT_2)

        pipeline_path = os.path.join(work, "smoke.yaml")
        with open(pipeline_path, "w", encoding="utf-8") as f:
            f.write(PIPELINE)

        session_dir = os.path.join(work, "session")
        builder = PromptBuilder(prompts_dir)
        manager = ProviderManager(config_path=providers_yaml)  # real src.providers
        emit, events = make_file_emit(session_dir)

        print("== running stub pipeline ==")
        context = run_pipeline(
            pipeline_path,
            "What is the capital of France?",
            session_dir,
            emit,
            builder=builder,
            manager=manager,
            job_id="smoke-0001",
        )

        print(f"\noutputs produced: {list(context['outputs'])}")
        print(f"events emitted  : {[(e['seq'], e['type']) for e in events]}")

        print("\n== persisted files ==")
        for fn in sorted(os.listdir(session_dir)):
            path = os.path.join(session_dir, fn)
            size = os.path.getsize(path)
            print(f"\n----- {fn} ({size} bytes) -----")
            with open(path, encoding="utf-8") as f:
                print(f.read().rstrip())

    print("\nOK: stub pipeline ran end-to-end and persisted prompt/response/"
          "context (+ events.jsonl via the stub emit).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
