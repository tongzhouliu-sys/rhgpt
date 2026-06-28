# RHCLOUD V1 — HTTP API Reference (Contract 3)

The gateway (`src/main.py`) exposed by Developer C. Built on A's frozen
`run_pipeline(pipeline_path, user_question, session_dir, emit)` (contract 2).
Business-layer step failures are **not** HTTP errors — they arrive as
`step_failed` / `fatal` events.

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/jobs` | yes | Create + start a run; returns `job_id` |
| GET | `/jobs/{job_id}` | yes | Status + events so far (polling fallback) |
| GET | `/jobs/{job_id}/events` | yes | SSE event stream (`Last-Event-ID` reconnect) |
| GET | `/jobs/{job_id}/export?mode=` | yes | Download `merged` / `steps` / `json` |
| GET | `/health` | no | Liveness + active job count + metrics |

## Authentication (API Key + HMAC)

Every authed request carries three headers:

```
X-Api-Key:    <identity>
X-Timestamp:  <unix seconds>
X-Signature:  hex( HMAC-SHA256(secret, canonical) )

canonical = METHOD + "\n" + PATH + "\n" + X-Timestamp + "\n" + sha256_hex(body)
```

- `PATH` is the URL path **without** the query string (so `?mode=` is not signed).
- `body` is the raw request bytes (empty for GET → `sha256_hex("")`).
- The server accepts the request iff the api-key is known, the signature matches
  (constant-time), and `|now − X-Timestamp| ≤ 300s` (replay window).
- Credentials come from the environment: `RHCLOUD_API_KEYS="k1:s1,k2:s2"` or a
  single `RHCLOUD_API_KEY` + `RHCLOUD_API_SECRET`. If unset, the server starts
  with auth fail-closed (every authed route returns 401).

Reference implementations: `src/auth.py` (Python), `frontend/lib/api.ts`
(browser Web Crypto). The browser uses `fetch` + `ReadableStream` for SSE since
native `EventSource` cannot send these headers.

## `POST /jobs`

Request body:
```json
{ "user_question": "帮我设计一个高并发短链服务", "pipeline": "pipelines/round1.yaml" }
```
`pipeline` is optional (default `pipelines/round1.yaml`). The pipeline is
validated at submit (providers exist, prompt files exist, keys unique, no
forward `{{key}}` references); validation failure → `400`.

Response `200`:
```json
{ "job_id": "8f7e9d2a-1b3c-4d5e-9a0b-1c2d3e4f5a6b" }
```

## `GET /jobs/{job_id}`

```json
{
  "job_id": "8f7e9d2a-…",
  "status": "running",          // running | succeeded | failed
  "events": [
    { "seq": 1, "type": "step_started", "key": "generate", "provider": "chatgpt_web_1" },
    { "seq": 2, "type": "step_succeeded", "key": "generate", "provider": "chatgpt_web_1", "content": "…" }
  ]
}
```

## `GET /jobs/{job_id}/events` (SSE)

`Content-Type: text/event-stream`. Each event is delivered as:
```text
id: 2
data: {"seq":2,"type":"step_succeeded","key":"generate","provider":"chatgpt_web_1","content":"…"}

```
Every ~15s an idle stream sends a comment keepalive (`: keepalive`). When the job
finishes and all events are flushed, the stream sends a terminal frame and closes:
```text
event: done
data: {}
```

**Reconnect**: send `Last-Event-ID: N`; the server replays only events with
`seq > N` and continues live. The stream is driven by the persisted event log
with a per-connection cursor and strict `seq` de-duplication, so reconnects and
multiple concurrent readers never lose or duplicate an event.

### Event schema (`events.jsonl`, one JSON per line)

| Field | Type | Notes |
|-------|------|-------|
| `seq` | int | monotonic; the SSE `id:` / `Last-Event-ID` cursor |
| `type` | string | `step_started` / `step_succeeded` / `step_failed` / `pipeline_finished` / `fatal` |
| `key` | string | step key (omitted on lifecycle events) |
| `provider` | string | provider instance name |
| `content` | string | `step_succeeded` only — that step's output |
| `error` | object | `step_failed` / `fatal` only — `{type, message}` |

## `GET /jobs/{job_id}/export?mode=`

| `mode` | Content-Type | Body |
|--------|--------------|------|
| `merged` (default) | `text/markdown` | all steps concatenated in order (the user-facing result) |
| `steps` | `application/zip` | one `NN_{key}_response.md` per step (+ any `error.json`) |
| `json` | `application/json` | the `context.json` structure |

Unknown `mode` → `400`. Missing session / no outputs → `404`.

## `GET /health`

```json
{ "status": "ok", "active_jobs": 1, "metrics": { "jobs_total": 12, "jobs_failed_total": 1, "active_jobs": 1, "...": 0 } }
```

## Error codes

| HTTP | Meaning | Trigger |
|------|---------|---------|
| 400 | Bad request | missing/blank `user_question`; non-JSON body; pipeline/provider/prompt validation failed; bad export `mode` |
| 401 | Unauthorized | missing/invalid signature, unknown key, or stale timestamp |
| 404 | Not found | unknown `job_id`; nothing to export |
| 429 | Throttled | max concurrent jobs reached, or per-key rate limit exceeded |
| 500 | Server error | uncaught error in the request handler |

A failure **inside** the pipeline (a step) is reported via `step_failed` / `fatal`
events (and `NN_{key}_error.json`), never as an HTTP error.

## Environment variables (gateway)

| Var | Default | Meaning |
|-----|---------|---------|
| `RHCLOUD_API_KEYS` / `RHCLOUD_API_KEY`+`RHCLOUD_API_SECRET` | — | HMAC credentials |
| `FRONTEND_ORIGIN` | `https://your-frontend.pages.dev` | single allowed CORS origin (never `*`) |
| `MAX_CONCURRENT_JOBS` | `2` | concurrent-job cap (429 beyond) |
| `RATE_LIMIT_PER_MIN` | `30` | per-key job-creation rate (429 beyond) |
| `ALERT_CONSECUTIVE_THRESHOLD` | `3` | consecutive same-type failures before a prominent log |
| `PROVIDERS_PATH` | `config/providers.yaml` | provider config path |
| `PROMPTS_DIR` | `prompts` | prompt templates dir |
| `SESSIONS_ROOT` | `data/sessions` | session output root |
| `LOG_LEVEL` | `INFO` | structured log level |
