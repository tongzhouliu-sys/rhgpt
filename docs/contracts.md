# RHCLOUD V1 — 内核契约（Contracts）

> 本文件由 **开发者 A（后端内核 + 基础设施）** 维护并冻结。
> B（Providers / 浏览器自动化）与 C（API 网关 / 前端）依此并行开发。
> **签名一旦冻结不得擅改**；任何变更需三方确认并同步本文件版本。

版本：V1 · 冻结日期：见 git 历史 · 维护者：A

---

## 0. 模块归属速查

| 归属 | 文件 / 目录 |
|---|---|
| A | `src/runtime.py` `src/builder.py` `src/manager.py` `src/validation.py` `src/cleanup.py` `src/logging_conf.py` `src/providers/_errors.py` `src/providers/stub.py` `config/providers.yaml`(schema) `Dockerfile` `requirements*.txt` `.github/workflows/ci.yml` `tests/` |
| B | `src/providers/{chatgpt,claude,deepseek,zai,kimi,gemini,qwen}.py`、各站点会话/浏览器自动化、生产 `pipelines/*.yaml`、生产 `prompts/*.md` |
| C | `src/main.py`(FastAPI)、`emit` 实现、`events.jsonl` 落盘、SSE、鉴权(API Key + HMAC)、导出三模式、前端 |

> A 的可运行示例只存在于 `tests/fixtures/` 与 `scripts/smoke_stub.py`；A **不**编写生产 `pipelines/*.yaml` 与 `prompts/*.md`（那是 B 的归属）。

---

## 1. 契约一：Provider（B 实现，A 冻结）

每个站点一个模块 `src/providers/{site}.py`，对外暴露唯一函数：

```python
def run(profile: str, prompt: str, *, timeout_ms: int = 120000, **options) -> str:
    ...
```

- **返回**：非空 Markdown 文本（`str`）。返回空串/`None` 被 Runtime 视为**瞬时失败**并触发重试，而非静默通过。
- **无基类、无注册表**：Manager 通过 `importlib.import_module("src.providers." + site)` 动态加载，仅要求模块层有 `run`。
- `profile`：账号/会话标识；API 类 Provider 传 `""`。
- `**options`：向后兼容预留，未知键应被忽略。
- 函数运行在后台 Worker 线程（无 asyncio 事件循环），因此 Provider 内部使用**同步** Playwright 是安全的（[修正-1]）。

### 1.1 错误类型（`src/providers/_errors.py`，A 提供，B 复用）

```python
class ProviderError(Exception): ...          # 基类
class SessionExpiredError(ProviderError): ... # 致命：会话失效/需重新登录
class GenerationTimeout(ProviderError): ...   # 瞬时：单次生成超时
```

分类语义（Runtime 据此处理）：

| 抛出 | 类别 | Runtime 行为 | `error.type` |
|---|---|---|---|
| `SessionExpiredError` | **致命 FATAL** | **不重试**，立即失败并中断 pipeline | `session_expired` |
| `GenerationTimeout` / 其他任意 `Exception` | **瞬时 TRANSIENT** | 指数退避重试至 `retries` 次，仍失败则记错 | `transient` |
| 返回空内容 | 瞬时 TRANSIENT | 同上（视为瞬时） | `transient` |

> B 可在 `_errors.py` 之外扩展自有异常；只要继承自 `Exception` 即落入瞬时类。若需新增**致命**类型，必须改本文件并让 A 在 Runtime 中显式分类。

---

## 2. 契约二：编排入口（A 实现，C 调用）

```python
def run_pipeline(
    pipeline_path: str,
    user_question: str,
    session_dir: str,
    emit: Callable[[dict], None],
) -> dict:
    ...
```

- C 在后台 Worker 线程中调用；返回最终 `context`（`{"user_question": ..., "outputs": {key: text}}`）。
- `emit` 由 C 注入：每个事件先由 Runtime 赋 `seq` 再回调 `emit(event)`。
- 还有若干**带默认值的关键字参数**（`builder` / `manager` / `validate` / `job_id`），仅用于测试与启动装配，**不改变** C 现有 4 参调用点。

### 2.1 seq 规则

- Runtime 维护单调递增 `seq`，**从 1 开始**，每次 `emit` 前 `+1`。
- `emit` 收到的事件已带 `seq`；stub/C 只负责落盘与转发，**不得重编号**。

---

## 3. 事件 Schema（写入 `events.jsonl`，由 C 的 emit 落盘）

每行一个 JSON 对象。字段：

| 字段 | 类型 | 出现时机 |
|---|---|---|
| `seq` | int | 所有事件，单调递增、从 1 起 |
| `type` | str | `step_started` / `step_succeeded` / `step_failed` / `pipeline_finished` / `fatal` |
| `key` | str | 步骤类事件（finished/顶层 fatal 可无） |
| `provider` | str | 步骤类事件 |
| `content` | str | **仅** `step_succeeded` |
| `error` | obj | **仅** `step_failed` / `fatal`，形如 `{"type": "...", "message": "..."}` |

事件序列示例：

```
成功两步：
  step_started(s1) → step_succeeded(s1) → step_started(s2) → step_succeeded(s2) → pipeline_finished
致命中断（会话失效）：
  step_started(s1) → step_failed(s1, error.type=session_expired) → pipeline_finished
```

> **出错即中断**：任一步骤失败后，Runtime 不再执行后续步骤，仍会发出 `pipeline_finished`。

### 3.1 顶层 `fatal` 事件（C 注意）

Runtime 正常路径只产出上述 step/finished 事件。若 **Worker 层**（run_pipeline 之外，例如线程崩溃、参数非法在调用前）发生带外致命错误，由 **C** 负责构造 `type="fatal"` 事件并**沿用当前 job 的 seq 续号**写入同一 `events.jsonl`，避免 seq 跳号或重置。

---

## 4. 持久化归属（[修正] / §7）

| 文件 | 写入方 | 命名 |
|---|---|---|
| `{NN}_{key}_prompt.md` | **A**(Runtime) | `NN = index+1`，两位补零 |
| `{NN}_{key}_response.md` | **A**(Runtime) | 仅成功步骤 |
| `{NN}_{key}_error.json` | **A**(Runtime) | 仅失败步骤，内容即 `error` 对象 |
| `context.json` | **A**(Runtime) | 全量 `context` |
| `events.jsonl` | **C**(emit) | Runtime **绝不**写该文件 |

> 文件名形如 `01_s1_prompt.md`、`02_s2_response.md`。Runtime 只写前四类；`events.jsonl` 是 C 在 `emit` 里落盘的唯一事实来源。

---

## 5. Provider 配置 Schema（`config/providers.yaml`）

```yaml
defaults:
  timeout_ms: 120000
  retries: 2
  retry_backoff_ms: 3000
providers:
  chatgpt_web_1:
    site: chatgpt        # → 加载 src/providers/chatgpt.py
    profile: default     # 账号/会话标识；API 类填 ""
    # 可选覆盖：timeout_ms / retries / retry_backoff_ms
  gemini_api_1:
    site: gemini
    profile: ""
```

- 新增账号 = 在 `providers` 下加几行；新增站点 = 加 `src/providers/{site}.py`。Manager / Runtime / Builder **均无需改动**（FR-04 / §14 DoD）。
- `profile` 必填（API 用 `""`）；三个可选项必须是整数。

### 5.1 V1 站点集合（§17.1）

- **API 类**：`gemini`、`qwen`（`profile=""`）。
- **Web 类**：`chatgpt`、`claude`、`deepseek`、`zai`、`kimi`。
- Grok **不纳入** V1。
- 鉴权：API Key + HMAC（C 实现）；会话保留 14 天（A 的 `cleanup`）。

---

## 6. Prompt 模板与变量（§6.1）

模板位于 `prompts/{name}.md`。**仅两类变量**会被替换：

- `{{user_question}}` → 用户原始问题
- `{{<step_key>}}` → **已产出**的前序步骤输出

替换语义（Builder，[修正-3]）：

- 仅 **裸标识符** `{{name}}`（无空格、无点号、无管道符）被视为变量。
- 含空格/点号/表达式者（`{{ vue_var }}`、`{{ user.name }}`、`{{ a | b }}`）**原样保留**，不破坏模型输出里的合法双花括号。
- **单遍正则替换**：注入值即使包含 `{{...}}` 也不会被二次扫描替换（杜绝回注）。
- 未知裸变量**原样保留**（在持久化的 `_prompt.md` 中可见，作为显式失败信号，而非静默删除）。

---

## 7. A 暴露给 C 的校验 API（`src/validation.py`，§6.1.2 / §8.5）

```python
validate_pipeline_file(pipeline_path, providers_path="config/providers.yaml",
                       prompts_dir="prompts") -> dict   # 提交时校验，失败抛 ValidationError
validate_all(pipelines_dir="pipelines", providers_path=..., prompts_dir=...) -> None  # 启动自检
```

- **C 在 `POST /jobs` 调 `validate_pipeline_file`**：捕获 `ValidationError` → 返回 **HTTP 400**（错误信息在 `.errors: list[str]`）。
- Runtime 内部亦调 `validate_pipeline` 作纵深防御（同一份 providers 配置 / prompts 目录）。

四项校验（全部 fail-closed）：

1. 每个 `step.provider` 存在于 `providers.yaml`；
2. 每个 `step.prompt` 对应 `prompts/{prompt}.md` 文件存在；
3. 同一 pipeline 内 `key` 唯一；
4. **前向引用**：模板引用的每个 `{{key}}` 必须是 `user_question` 或**更早**步骤的 key；引用后续/自身 key（输出尚未产生）或未知名称 → 错误。这是 V1 最易踩的逻辑 bug，校验层兜住。

---

## 8. Stub 约定（A2，供 B/C 并行与 A 自测）

- `src/providers/stub.py`：M1 占位 Provider，确定性非空 Markdown（sha1 指纹，不回显全量 prompt）。在 `providers.yaml` 用 `site: stub` 即可端到端跑通而不依赖 B。
- `src/stubs.py`：模拟 C 的 `emit`——
  - `make_recording_emit() -> (emit, events)`：纯内存，`events` 可直接断言；
  - `make_file_emit(session_dir) -> (emit, events)`：内存 + 追加写 `events.jsonl`（验证 on-disk 事件日志）；
  - `print_emit(ev)`：stdout sink，临时手测用。
- `scripts/smoke_stub.py`：用 stub 链路端到端跑一遍 fixtures 并打印落盘文件（M1 人工验证）。

---

## 9. 日志与指标（`src/logging_conf.py`，§10）

- **结构化日志**：每行一个 JSON，字段白名单 `ts, level, logger, event, job_id, step_key, provider, site, attempt, duration_ms, error_type`。**绝不**记录 prompt/response 正文（仅存于 `_prompt.md`/`_response.md`）。
- **进程内指标**（依赖无关，`metrics.snapshot()` 可供 C 的 `/health` 或未来 `/metrics`）：`jobs_total`、`jobs_failed_total`、`step_duration_seconds{provider,site}`、`step_retries_total`、`session_expired_total{provider}`、`active_jobs`。

---

## 10. 变更流程

任何对**契约一签名 / 契约二签名 / 事件 Schema / 持久化命名 / 错误分类**的改动：

1. 先改本文件并 bump 版本；
2. 三方（A/B/C）确认；
3. 同步更新 `tests/` 中对应断言。

未走该流程的契约改动一律视为破坏性回归。
