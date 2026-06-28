# E2E Smoke (manual, pre-release) — C10

The API/SSE behaviour is covered automatically by `tests/api/` with a stub
runtime. This document is the **manual** end-to-end smoke that drives at least
**one web-automation Provider + one API Provider** through the shortest real
pipeline. It needs live accounts/credentials and a browser, so it is **not** run
in CI — execute it in a dedicated environment before a release.

## Preconditions

- Developer B's Providers are implemented and at least two are configured in
  `config/providers.yaml`: one API-backed (e.g. `gemini_api`) and one
  web-automation (e.g. `chatgpt_web_1`), with a seeded profile under
  `data/profiles/` for the web one (see B8 / §12.6 Session Seeding).
- A shortest pipeline exists, e.g. `pipelines/smoke.yaml` with two steps:
  `generate` (API provider) → `review` (web provider), and the matching
  `prompts/*.md`.
- Backend env set: `RHCLOUD_API_KEYS` (or `RHCLOUD_API_KEY` + `_SECRET`),
  `FRONTEND_ORIGIN`, provider API keys.

## Procedure

1. **Start the backend**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```
   Confirm `GET /health` returns `{"status":"ok"}`.

2. **Submit a job** (signed request — reuse `src/auth.py::sign` to build headers,
   or drive it from the frontend with `NEXT_PUBLIC_USE_MOCK=0`):
   ```
   POST /jobs   { "user_question": "用三句话解释 CAP 定理", "pipeline": "pipelines/smoke.yaml" }
   ```
   Expect `200 { "job_id": "…" }`.

3. **Watch the stream**: open `GET /jobs/{job_id}/events`. Expect, in order:
   `step_started/step_succeeded` for `generate`, then for `review`, then
   `pipeline_finished`, then `event: done`. Each `id:` (seq) is strictly
   increasing.

4. **Reconnect check**: kill the SSE connection mid-run and reopen it with
   `Last-Event-ID: <last seq seen>`. Only events with `seq >` that value replay —
   no loss, no duplicates.

5. **Polling fallback**: with no SSE open, `GET /jobs/{job_id}` returns the same
   accumulated events and a terminal `status` once finished.

6. **Inspect the session on disk** (`data/sessions/{job_id}/`): one
   `NN_{key}_prompt.md` + `NN_{key}_response.md` per step, `context.json`,
   `events.jsonl`. A failed step also has `NN_{key}_error.json`.

7. **Exports**: `GET /jobs/{job_id}/export?mode=merged|steps|json` each download
   successfully and contain every step's output.

8. **再来一轮**: from the frontend, click 再来一轮 → a new job runs with
   `pipeline=pipelines/continue.yaml`, seeded by the prior round.

## Pass criteria

- [ ] Two providers (1 web + 1 API) each produced a real response.
- [ ] Event sequence correct and monotonic; `event: done` received.
- [ ] `Last-Event-ID` reconnect replays only newer events (no loss/dup).
- [ ] Polling fallback reaches a terminal state.
- [ ] Session fully persisted; all three exports valid.
- [ ] A forced failure (e.g. expired profile) surfaces as `step_failed`/`fatal`
      with `error.json`, not an HTTP 5xx.

> A provider-free smoke of the kernel (stub provider, no accounts) is available
> via `scripts/smoke_stub.py` for a quick liveness check before this full E2E.
