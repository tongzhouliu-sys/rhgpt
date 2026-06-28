// In-browser mock backend (spec: "C 的 mock 后端"). Lets the frontend run with
// NEXT_PUBLIC_USE_MOCK=1 and no API: fakes a job_id and replays a scripted,
// timed event sequence shaped exactly like contract 2's events.

import type { JobState, RhEvent } from "./api";

interface MockJob {
  status: "running" | "succeeded" | "failed";
  events: RhEvent[];
  question: string;
  pipeline: string;
}

const store = new Map<string, MockJob>();

function script(question: string): RhEvent[] {
  return [
    { seq: 1, type: "step_started", key: "generate", provider: "chatgpt_web_1" },
    {
      seq: 2,
      type: "step_succeeded",
      key: "generate",
      provider: "chatgpt_web_1",
      content: `## 初稿\n\n针对「${question}」的初步方案：\n\n- 接入层：边缘网关 + 限流\n- 存储：分片 KV\n- \`hash(longUrl)\` 生成短码`,
    },
    { seq: 3, type: "step_started", key: "grok_review", provider: "grok_web_1" },
    {
      seq: 4,
      type: "step_succeeded",
      key: "grok_review",
      provider: "grok_web_1",
      content: "## 评审\n\n**优点**：架构清晰。\n**风险**：未覆盖热点 key 与缓存击穿，建议加二级缓存。",
    },
    { seq: 5, type: "step_started", key: "claude_deep", provider: "claude_web_1" },
    {
      seq: 6,
      type: "step_succeeded",
      key: "claude_deep",
      provider: "claude_web_1",
      content: "## 终稿\n\n综合两版，给出最终设计：\n\n1. 边缘网关统一鉴权/限流\n2. 写路径异步落库\n3. 读路径多级缓存 + 布隆过滤",
    },
    { seq: 7, type: "pipeline_finished" },
  ];
}

export async function mockCreateJob(question: string, pipeline: string): Promise<string> {
  const jobId = `mock-${Math.random().toString(36).slice(2, 10)}`;
  store.set(jobId, { status: "running", events: [], question, pipeline });
  return jobId;
}

export async function mockGetJob(jobId: string): Promise<JobState> {
  const job = store.get(jobId);
  if (!job) throw new Error("job not found");
  return { status: job.status, events: [...job.events] };
}

export async function mockStreamEvents(
  jobId: string,
  onEvent: (e: RhEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const job = store.get(jobId);
  if (!job) throw new Error("job not found");
  for (const ev of script(job.question)) {
    if (signal?.aborted) return;
    await new Promise((r) => setTimeout(r, 700));
    job.events.push(ev);
    onEvent(ev);
  }
  job.status = "succeeded";
}
