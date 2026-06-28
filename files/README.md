# RHCLOUD V1 — 完整交付（Developer A + B + C）

配置驱动的多模型串行中继管线（multi-model relay pipeline）。前端（Next.js / Cloudflare
Pages）→ FastAPI 后端（Railway 单实例）按 Pipeline 顺序执行步骤（构建 prompt → 调用
Provider → 持久化 → 写 Context），事件经 SSE 推送。**文件即数据库，无 SQL。**

本仓库为 RHCLOUD V1 的完整三方交付：
- **A**（后端内核 + 基础设施）：runtime / builder / manager / validation / cleanup / 日志指标 / Dockerfile / CI。
- **B**（Provider 与浏览器自动化）：`src/providers/{chatgpt,claude,deepseek,zai,kimi,gemini_api,qwen_api}.py` + 共享浏览器引擎 `_browser.py` + `pipelines/*.yaml` + `prompts/*.md` + 会话注入 + 契约测试。
- **C**（接入网关与前端）：`src/main.py` + 鉴权/导出/告警 + `frontend/` + API/E2E 测试。

桩 Provider（A）与各模型 Provider（B）共存于 `config/providers.yaml`；新增账号仅改该文件，新增网站仅加 `src/providers/{site}.py`，runtime/builder/manager/网关零改动。

---

## 目录结构

```
src/
  builder.py        A3  Prompt 构建（白名单单遍正则替换，[修正-3]）
  manager.py        A4  Provider 动态加载 + 参数解析 + 模块缓存
  validation.py     A5  配置/管线四项校验（含前向引用检查）
  runtime.py        A6+A7 执行引擎（分类重试[修正-4] + Profile 锁[修正-8] + 落盘 + 事件）
  cleanup.py        A8  会话清理（默认保留 14 天，含 CLI）
  logging_conf.py   A9  结构化 JSON 日志 + 进程内指标
  main.py           C1+C3+C4  FastAPI 网关：Job 化 + 后台 Worker + 可重连 SSE + 导出 + /health
  auth.py           C2  HMAC 鉴权（API Key + 签名 + 时间戳防重放，框架无关）
  export.py         C5  导出三态（单步 zip / 合并 md / JSON），读 A 的落盘文件
  alerts.py         C9  连续失败告警（连续 N 次同类失败 → 显著日志）
  providers/
    _errors.py          错误类型契约（A 提供，B 复用）
    _browser.py       B1  共享浏览器引擎：持久上下文池 + 反检测 + 拦截优先 run_web
    _extract.py       B   响应正文文本提取（SSE/JSON 容错，被各网页 Provider 复用）
    chatgpt.py        B4  网页 Provider（P0）
    claude.py         B5  网页 Provider（P0）
    deepseek.py       B6  网页 Provider（backfill）
    zai.py            B6  网页 Provider（backfill）
    kimi.py           B6  网页 Provider（backfill）
    gemini_api.py     B3  官方 API Provider（P0 基线）
    qwen_api.py       B6  官方 API Provider（P1）
    stub.py             M1 桩 Provider（无模型/无网络）
  stubs.py              桩 emit（模拟 C，供并行与自测）
pipelines/            B7  round1.yaml（5 步）+ continue.yaml（跳过 generate）
prompts/              B7  generate/review/deep_analyze/improve/summary(+recap) 模板
config/
  providers.yaml    Provider 实例配置（A 拥有 schema 与校验）
docs/
  contracts.md      冻结契约（B/C 依此并行开发）— 必读
  api.md            C  HTTP API 参考（端点/鉴权 canonical/SSE 帧/导出/错误码/环境变量）
  session_seeding.md B8  会话注入流程（本地有头登录 → Volume 注入 → 冒烟）
frontend/           C6+C7+C8  Next.js 控制台（输入 → 实时节点卡片 → 导出 / 再来一轮）
  app/              页面 + 状态机 + 控制台样式
  lib/              HMAC 签名、SSE 客户端、Markdown 渲染、Mock 后端
scripts/
  smoke_stub.py     M1 烟雾测试：桩链路端到端跑通并打印落盘
  seed_session.py   B8  本地有头登录、持久化 Provider profile 供 Volume 注入
tests/
  unit/             builder / manager / validation + auth / export / alerts 单测
  integration/      runtime 集成测试（事件、落盘、重试、锁、指标）
  contract/         B  Provider 契约测试（假 page + 打桩 requests；含 round1 端到端回放）
  api/              C  网关 API/SSE 测试（httpx + 桩 Runtime，CI 运行）
  e2e/              C  真实 Provider 手动 E2E 流程（发布前，README）
  fixtures/         桩 Provider 包 + 测试用 prompts/pipelines/providers.yaml
Dockerfile          §12.2（playwright + xvfb）
requirements*.txt   运行/开发依赖
.github/workflows/ci.yml  CI：lint(建议) + unit/integration(必过) + contract(B) + api(C) + docker-build
```

---

## 运行测试

无需第三方依赖即可跑本地单测、集成与契约（标准库 `unittest`）：

```bash
python -m unittest discover -s tests/unit -p 'test_*.py' -v
python -m unittest discover -s tests/integration -p 'test_*.py' -v
python -m unittest discover -s tests/contract -p 'test_*.py' -v
```

CI 中亦用 `pytest`（`requirements-dev.txt`）；两者均可发现同一批用例。

- **本地可跑**（无需 FastAPI / 真实浏览器 / 网络）：A 的 builder/manager/validation + runtime 集成；
  C 的 `auth`/`export`/`alerts` 单测；**B 的 Provider 契约测试**（假 `page` 模拟网络拦截/登录/空输出 +
  打桩 `requests`，含用真实 `round1.yaml`/prompts 跑通 5 步接力的端到端回放）。共 50 单测 + 6 集成 +
  18 契约全绿。
- **CI 运行**（需 `fastapi`+`httpx`，`requirements-dev.txt` 已含）：`tests/api/` 用 FastAPI
  `TestClient` + 桩 Runtime 验证鉴权 401、校验 400、超并发/限流 429、SSE 帧 + `Last-Event-ID` 续传、
  轮询兜底、导出三态、Worker 致命 seq；无 FastAPI 环境自动 `skip`。
- **发布前手动**：`tests/e2e/README.md`（真实 1 网页 + 1 API Provider）+ `docs/session_seeding.md`
  （会话注入）。

---

## 桩 Provider / M1 就绪

不依赖 B 的站点实现、不联网即可跑通最短管线并完整落盘：

```bash
python scripts/smoke_stub.py
```

将创建临时两步管线（均指向 `config/providers.yaml` 中的 `stub_1`），执行后打印
`NN_{key}_prompt.md` / `NN_{key}_response.md` / `context.json` 与（由桩 emit 写出的）
`events.jsonl`，验证：seq 单调从 1、prompt 链式传递（s2 prompt 含 s1 输出）、出错即中断
等内核行为。

---

## 契约（B/C 必读）

`docs/contracts.md` 冻结了三方接口：

- **契约一** Provider：`run(profile, prompt, *, timeout_ms=120000, **options) -> str`（B 实现）。
- **契约二** 编排：`run_pipeline(pipeline_path, user_question, session_dir, emit) -> dict`（A 实现，C 调用）。
- **错误分类**：`SessionExpiredError` = 致命不重试；其他 `Exception` / 空内容 = 瞬时重试。
- **持久化归属**：A 写 `*_prompt.md` / `*_response.md` / `*_error.json` / `context.json`；
  `events.jsonl` 由 **C 的 emit** 写，Runtime 绝不写。
- **校验**：C 在 `POST /jobs` 调 `validate_pipeline_file`，失败→HTTP 400。

> 凡涉及契约签名 / 事件 schema / 持久化命名 / 错误分类的改动，须先改 `docs/contracts.md`
> 并经三方确认，否则视为破坏性回归。

---

## Provider 与流水线（Developer B）

各模型适配器封装为单文件 `src/providers/{site}.py`，对 A/C 透明——只暴露契约 1：

```python
def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str
```

Manager 经 `importlib` 按 `site` 动态加载；新增网站只加一个文件，零改动其它层。

- **网页自动化**（`chatgpt`/`claude`/`deepseek`/`zai`/`kimi`）：统一委托共享引擎
  `_browser.run_web`——按 `profile` 复用**持久上下文**（不每步冷启）、注入**反检测**
  （stealth init script + 真实 UA/语言/时区/视口；`playwright_stealth` 可选）、
  **网络拦截优先**（`page.on("response")` 取后端响应，`_extract` 容错解析 SSE/JSON），
  DOM 仅兜底；**生成完成判定无 `sleep`**（`wait_for_selector` 等完成信号）；重定向登录页或
  出现登录控件即抛 `SessionExpiredError`（致命 → 快速失败 + 提示重新 Seeding）。
  > 各站点的选择器与后端响应 URL 为最佳推断，**须对照线上 DOM/接口实测校准**（§6.4）。
- **官方 API**（`gemini_api` P0 基线、`qwen_api`）：API Key 取自环境变量（绝不入 YAML）；
  空响应按瞬时错误处理。
- **流水线**：`pipelines/round1.yaml`（generate→review→deep_analyze→improve→summary，
  混用网页 chatgpt/claude + API gemini，满足"≥3 模型含 ≥1 API"）；`pipelines/continue.yaml`
  （跳过 generate，首步 `review` 用 `recap` 重述上一轮结果，供 C8"再来一轮"）。两条均通过 A 的
  启动校验与提交校验（前向引用合法）。
- **Prompt**：`prompts/{generate,review,deep_analyze,improve,summary}.md` + `recap.md`；
  每个仅引用 `{{user_question}}` 与紧邻前序 step key，并含"重申原始需求/防跑题"强制提醒段。
- **会话注入**：`python scripts/seed_session.py --site chatgpt --profile data/profiles/chatgpt_acc1`
  本地有头登录 → 持久化 profile → 注入 Volume，详见 `docs/session_seeding.md`。

### Provider 环境变量（API 路线）

| 变量 | 用途 |
|------|------|
| `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` | Gemini API |
| `GEMINI_MODEL` | 可选，默认 `gemini-1.5-pro` |
| `DASHSCOPE_API_KEY` 或 `QWEN_API_KEY` | Qwen（DashScope 兼容端点） |
| `QWEN_MODEL` | 可选，默认 `qwen-plus` |
| `RHCLOUD_HEADLESS` | 网页 Provider 是否无头（默认 `1`；容器内经 Xvfb 有头时设 `0`） |

---

## 接入网关（Developer C）

FastAPI 网关把内核包成可调用的 HTTP/SSE 服务。完整端点/请求响应/SSE 帧/错误码见
**`docs/api.md`**。要点：

- **端点**：`POST /jobs`（创建运行）、`GET /jobs/{id}`（轮询兜底）、
  `GET /jobs/{id}/events`（可重连 SSE）、`GET /jobs/{id}/export?mode=`（导出三态）、
  `GET /health`（探活 + 指标）。
- **鉴权**：API Key + HMAC（`X-Api-Key`/`X-Timestamp`/`X-Signature`，
  `canonical = METHOD\nPATH\nTS\nsha256(body)`，时间戳 ±300s 防重放）。凭据经环境变量注入；
  未配置时**鉴权 fail-closed**（所有 authed 路由 401），`uvicorn src.main:app` 仍可导入。
- **可重连 SSE**：事件先持久化（`events.jsonl`）再下发；以持久化事件日志 + 每连接游标 +
  严格 `seq` 去重驱动回放，`Last-Event-ID` 重连**不丢/不重**，多读者各自完整；15s 心跳；
  结束发 `event: done`。
- **限流/并发**：超 `MAX_CONCURRENT_JOBS` → 429；按 key 每分钟超 `RATE_LIMIT_PER_MIN` → 429。
  CORS 仅放行 `FRONTEND_ORIGIN`，绝不 `*`。
- **导出三态**：`merged`（合并 md）/`steps`（单步 zip）/`json`（context.json），读 A 的落盘。
- **告警**：连续 `ALERT_CONSECUTIVE_THRESHOLD` 次同类失败（`session_expired`/`transient`/…）
  打显著 ERROR 日志，成功即清零。

本地启动（配置好凭据后）：

```bash
export RHCLOUD_API_KEYS="client-a:$(openssl rand -hex 16)"
export FRONTEND_ORIGIN="http://localhost:3000"
uvicorn src.main:app --port 8000
# GET /health → {"status":"ok",...}
```

### 网关环境变量

| 变量 | 默认 | 含义 |
|------|------|------|
| `RHCLOUD_API_KEYS` 或 `RHCLOUD_API_KEY`+`RHCLOUD_API_SECRET` | — | HMAC 凭据 |
| `FRONTEND_ORIGIN` | `https://your-frontend.pages.dev` | 唯一放行 CORS 源 |
| `MAX_CONCURRENT_JOBS` | `2` | 并发 Job 上限（超则 429） |
| `RATE_LIMIT_PER_MIN` | `30` | 单 key 每分钟建 Job 上限（超则 429） |
| `ALERT_CONSECUTIVE_THRESHOLD` | `3` | 连续同类失败告警阈值 |
| `PROVIDERS_PATH` / `PROMPTS_DIR` / `SESSIONS_ROOT` | `config/providers.yaml` / `prompts` / `data/sessions` | 路径覆盖 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

---

## 前端（Developer C）

`frontend/` 为 Next.js（App Router）控制台：输入区（问题 + 流水线选择 + 提交）→ 执行区
（按步节点卡片 `运行中 → 完成/失败` + 内联渲染 Markdown）→ 结果区（导出三态 + 再来一轮）。
SSE 用 `fetch` + `ReadableStream` 手动解析（带 HMAC 签名头）、`Last-Event-ID` 断线续读、
失败轮询兜底。详见 `frontend/README.md`。

```bash
cd frontend && cp .env.example .env.local   # 填 API 基址与 HMAC key/secret
npm install && npm run dev                   # http://localhost:3000
# 无后端可独立开发：.env.local 设 NEXT_PUBLIC_USE_MOCK=1
npm run build                                # 静态导出到 ./out，部署 Cloudflare Pages
```

> **安全**：`NEXT_PUBLIC_*` 会被打进前端包，公开 SPA 无法保密 HMAC secret——仅适用于受信/
> 内网（访问受控）部署；面向不可信用户时应在后端前置签名代理持有 secret（契约不变）。

---

## 部署

```bash
docker build -t rhcloud .
# 容器内通过 xvfb-run 启动 uvicorn src.main:app（网关已交付，见上）
```

会话清理（保留期可经环境变量 `SESSION_RETENTION_DAYS` 覆盖，默认 14；`--days` 优先级高于环境变量）：

```bash
python -m src.cleanup --root data/sessions [--days 14] [--dry-run]
```
