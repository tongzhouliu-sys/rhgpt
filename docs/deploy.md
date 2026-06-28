# 部署指南（GitHub → Railway → Cloudflare Pages）

RHCLOUD V1 = FastAPI 后端（Railway，单实例）+ Next.js 前端（Cloudflare Pages 静态托管）。
前端是静态包，所有请求由浏览器直连后端。

> **架构约束**：后端的 Job 注册表与 SSE 事件表在内存里，**只能单实例，不能加副本**；重启会丢
> 在途 Job（落盘的 session 文件仍在，但 `GET /jobs/{id}` 会 404）。落盘走 Railway Volume。

---

## 0. 准备

- 把整个仓库推到 GitHub（`.gitignore` 已排除 `data/profiles`、`data/sessions`、`.env`）。
- 生成一个 HMAC secret：`openssl rand -hex 16`（前后端要用同一个）。

---

## 1. 后端（Railway）

1. Railway → New Project → **Deploy from GitHub repo**。仓库内已有 `railway.toml` 与
   `Dockerfile`，会自动用 Dockerfile 构建（含 Xvfb 有头 Chromium），健康检查路径 `/health`。
2. **挂 Volume**：mount path 填 `/app/data`（同时覆盖 `data/sessions` 落盘与
   `data/profiles` 登录态，二者相对 `/app`）。
3. **环境变量**（Variables，照抄 `.env.example`，至少）：

   | 变量 | 值 |
   |------|----|
   | `RHCLOUD_API_KEYS` | `client-a:<上面生成的secret>` |
   | `FRONTEND_ORIGIN` | 先填 `https://placeholder.pages.dev`，前端上线后回填真实域名 |
   | `GEMINI_API_KEY` | 你的 Gemini key（API 路线立即可用） |
   | `RHCLOUD_HEADLESS` | `0`（用网页 Provider 时） |
   | `MAX_CONCURRENT_JOBS` / `RATE_LIMIT_PER_MIN` / `LOG_LEVEL` | 可选，默认 2 / 30 / INFO |

4. 部署后验证：`curl https://<railway域名>/health` → `{"status":"ok",...}`。
   （`/health` 不鉴权，未配 key 也返回 200，但 `/jobs` 等会 401，直到 `RHCLOUD_API_KEYS` 配好。）

### 后端冒烟（API 路线，无需浏览器/seeding）

仓库已带 `pipelines/api_smoke.yaml`（单步 gemini）。签名调用（HMAC 必带）：

```bash
python - <<'PY'
import time, json, requests
from src.auth import sign
base = "https://<railway域名>"; key = "client-a"; secret = "<secret>"
path = "/jobs"
body = json.dumps({"user_question": "用三句话解释CAP定理",
                   "pipeline": "pipelines/api_smoke.yaml"}).encode()
ts = str(int(time.time()))
h = {"X-Api-Key": key, "X-Timestamp": ts,
     "X-Signature": sign(secret, "POST", path, ts, body),
     "Content-Type": "application/json"}
r = requests.post(base + path, data=body, headers=h); print(r.status_code, r.json())
PY
```

拿到 `job_id` 后看 `GET /jobs/{id}`（轮询）或 `/jobs/{id}/events`（SSE）、
`/jobs/{id}/export?mode=merged`。完整 API 见 `docs/api.md`。

---

## 2. 网页 Provider（可选，API 闭环跑通后再做）

上线前两件事：① 对照线上 DOM/接口**校准选择器与响应 URL**（`src/providers/{site}.py` 的
`SITE` 字典，源码已标注待实测）；② 注入登录态：

```bash
python scripts/seed_session.py --site chatgpt --profile data/profiles/chatgpt_acc1
tar -czf chatgpt_acc1.tgz -C data/profiles chatgpt_acc1
# 解压到 Railway Volume 的 /app/data/profiles/ 下，并 chmod -R 700
```

详见 `docs/session_seeding.md`。之后用 `pipelines/round1.yaml` 跑混合（网页+API）E2E，
流程见 `tests/e2e/README.md`。

---

## 3. 前端（Cloudflare Pages）

1. Cloudflare Pages → 连同一个 GitHub repo。
2. **构建设置**：
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `out`（`next.config.mjs` 已设 `output:"export"` 静态导出；
     `frontend/.nvmrc` 锁 Node 20）
3. **环境变量**：
   - `NEXT_PUBLIC_API_BASE` = `https://<railway域名>`
   - `NEXT_PUBLIC_API_KEY` = `client-a`
   - `NEXT_PUBLIC_API_SECRET` = `<与后端同一个 secret>`
4. 部署成功后，把 Pages 域名回填到后端 `FRONTEND_ORIGIN`，**redeploy 后端**（CORS 生效）。

> **安全**：`NEXT_PUBLIC_*` 会被打进前端包，公开 SPA 无法保密 secret——仅适用受信/内网
> （访问受控）场景；面向不可信用户须在后端前置签名代理持有 secret（契约不变）。

---

## 4. 运维

- **留存清理**：新建一个 Railway **Cron Service**（同一仓库/镜像），命令
  `python -m src.cleanup --root data/sessions`，按 `0 3 * * *` 之类定时（默认留 14 天，
  `SESSION_RETENTION_DAYS` 可覆盖）。
- **告警**：连续 N 次同类失败（`session_expired`/`transient`）打 ERROR 日志，接 Railway 日志
  告警；`session_expired` = profile 过期，重新 seeding。
- **CI**：`.github/workflows/ci.yml` 已含 lint + 单测/集成 + 契约(B) + api(C) + docker-build。

## 常见坑

1. **`$PORT`**：Dockerfile 已改为监听 `${PORT:-8000}`；Railway 路由到动态端口。
2. **Volume 路径**：必须挂 `/app/data`，否则落盘与登录态不持久。
3. **副本数**：保持 1（内存态 Job/SSE）。
4. **网页 Provider 选择器**：必须先对照线上实测校准，否则取不到文本。
5. **secret 不一致**：前端 `NEXT_PUBLIC_API_SECRET` 与后端 `RHCLOUD_API_KEYS` 里的 secret
   必须完全一致，否则全部 401。
