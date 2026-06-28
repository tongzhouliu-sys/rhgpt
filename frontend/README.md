# RHCLOUD V1 — Frontend (接力控制台)

Next.js (App Router) console for the multi-model relay pipeline. Submits a
question, streams each step live via SSE, renders per-step Markdown, and exports
the round. Implements C6 (UI + node-card state machine), C7 (fetch+ReadableStream
SSE client with `Last-Event-ID` reconnect + polling fallback, HMAC-signed), and
C8 (再来一轮 carrying the prior round into `pipelines/continue.yaml`).

## Run locally

```bash
cd frontend
cp .env.example .env.local      # fill in API base + HMAC key/secret
npm install
npm run dev                     # http://localhost:3000
```

To develop without a backend, set `NEXT_PUBLIC_USE_MOCK=1` in `.env.local`; the
UI runs against an in-browser mock that replays a scripted event stream.

## Build & deploy (Cloudflare Pages)

`next.config.mjs` uses `output: "export"`, so the app builds to a static bundle:

```bash
npm run build      # emits ./out
```

Cloudflare Pages settings:
- Build command: `npm run build`
- Output directory: `out`
- Environment variables: `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_API_KEY`,
  `NEXT_PUBLIC_API_SECRET` (and optionally `NEXT_PUBLIC_USE_MOCK`).

The backend must allow this origin in CORS (`FRONTEND_ORIGIN`, set on the API).

## How it talks to the API (contract 3)

Every request is signed (`lib/api.ts`): `X-Api-Key`, `X-Timestamp`, and
`X-Signature = HMAC-SHA256(secret, METHOD\nPATH\nTS\nsha256(body))`, computed in
the browser with Web Crypto. The canonical string matches `src/auth.py` exactly.
SSE is consumed with `fetch` + `ReadableStream` (native `EventSource` can't send
headers); on a dropped connection the client reconnects with `Last-Event-ID` set
to the last `seq`, and after repeated failures falls back to polling
`GET /jobs/{id}`.

## Security

`NEXT_PUBLIC_*` values are inlined into the client bundle, so a public SPA cannot
keep the HMAC secret confidential. Embed the secret only for a trusted/internal
(access-gated) deployment. For an untrusted audience, front the backend with a
thin signing proxy that holds the secret and authenticates the browser by
session — the backend contract is unchanged. See `.env.example`.

## Layout

```
frontend/
├── app/
│   ├── layout.tsx        # metadata + global styles
│   ├── page.tsx          # console: input → relay node cards → result/export
│   └── globals.css       # operator console theme + relay timeline
└── lib/
    ├── api.ts            # HMAC signing, createJob/getJob/streamEvents/downloadExport
    ├── sse.ts            # SSE frame parser over ReadableStream
    ├── markdown.ts       # minimal XSS-safe Markdown renderer
    └── mock.ts           # in-browser mock backend (NEXT_PUBLIC_USE_MOCK=1)
```

> `pipelines/round1.yaml` and `pipelines/continue.yaml` are referenced by name
> only; the actual pipeline/prompt files are Developer B's deliverables.
