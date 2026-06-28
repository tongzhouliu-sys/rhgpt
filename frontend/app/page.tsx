"use client";

import { useCallback, useRef, useState } from "react";
import {
  createJob,
  downloadExport,
  streamEvents,
  USE_MOCK,
  type ExportMode,
  type RhEvent,
} from "../lib/api";
import { renderMarkdown } from "../lib/markdown";

type Phase = "idle" | "running" | "done" | "error";
type NodeStatus = "running" | "succeeded" | "failed";

interface NodeState {
  key: string;
  provider?: string;
  status: NodeStatus;
  content?: string;
  error?: { type: string; message: string };
}

const PIPELINES = [
  { value: "pipelines/round1.yaml", label: "round1 · 首轮" },
  { value: "pipelines/continue.yaml", label: "continue · 再来一轮" },
];

const BADGE: Record<NodeStatus, string> = {
  running: "运行中",
  succeeded: "完成",
  failed: "失败",
};

export default function Page() {
  const [question, setQuestion] = useState("");
  const [pipeline, setPipeline] = useState(PIPELINES[0].value);
  const [phase, setPhase] = useState<Phase>("idle");
  const [order, setOrder] = useState<string[]>([]);
  const [nodes, setNodes] = useState<Record<string, NodeState>>({});
  const [jobId, setJobId] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const applyEvent = useCallback((ev: RhEvent) => {
    if (ev.type === "pipeline_finished") {
      setPhase("done");
      return;
    }
    if (ev.type === "fatal") {
      setBanner(ev.error ? `${ev.error.type}: ${ev.error.message}` : "运行中断");
      setPhase("error");
      return;
    }
    const key = ev.key;
    if (!key) return;
    setOrder((prev) => (prev.includes(key) ? prev : [...prev, key]));
    setNodes((prev) => {
      const next = { ...prev };
      const cur = next[key] ?? { key, status: "running" as NodeStatus };
      if (ev.provider) cur.provider = ev.provider;
      if (ev.type === "step_started") cur.status = "running";
      else if (ev.type === "step_succeeded") {
        cur.status = "succeeded";
        cur.content = ev.content ?? "";
      } else if (ev.type === "step_failed") {
        cur.status = "failed";
        cur.error = ev.error;
      }
      next[key] = { ...cur };
      return next;
    });
  }, []);

  const run = useCallback(async () => {
    const q = question.trim();
    if (!q || phase === "running") return;
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    setBanner(null);
    setOrder([]);
    setNodes({});
    setJobId(null);
    setPhase("running");

    try {
      const id = await createJob(q, pipeline);
      setJobId(id);
      await streamEvents(id, applyEvent, ac.signal);
      setPhase((p) => (p === "running" ? "done" : p));
    } catch (err) {
      if (ac.signal.aborted) return;
      setBanner(err instanceof Error ? err.message : "提交失败");
      setPhase("error");
    }
  }, [question, pipeline, phase, applyEvent]);

  const againRound = useCallback(() => {
    // C8: carry the prior round's final synthesis as the seed for continue.yaml.
    const lastKey = [...order].reverse().find((k) => nodes[k]?.status === "succeeded");
    const seed = lastKey ? nodes[lastKey]?.content ?? "" : "";
    setQuestion(seed);
    setPipeline("pipelines/continue.yaml");
    setPhase("idle");
    setBanner(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [order, nodes]);

  const onExport = useCallback(
    async (mode: ExportMode) => {
      if (!jobId) return;
      try {
        await downloadExport(jobId, mode);
      } catch (err) {
        setBanner(err instanceof Error ? err.message : "导出失败");
      }
    },
    [jobId]
  );

  const running = phase === "running";
  const finished = phase === "done";
  const statusDot = running ? "run" : phase === "done" ? "ok" : phase === "error" ? "err" : "";
  const statusText =
    phase === "idle"
      ? "待命"
      : running
      ? jobId
        ? `运行中 · job ${jobId.slice(0, 8)}`
        : "提交中…"
      : phase === "done"
      ? "已完成"
      : "已中断";

  return (
    <main className="wrap">
      <header className="masthead">
        <span className="brand">RHCLOUD</span>
        <h1>接力控制台</h1>
        <span className="sub">multi-model relay {USE_MOCK ? "· MOCK" : ""}</span>
      </header>

      <section className="panel">
        <label className="field" htmlFor="q">
          问题
        </label>
        <textarea
          id="q"
          rows={4}
          placeholder="例如：帮我设计一个高并发短链服务"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={running}
        />
        <div className="controls">
          <div className="grow">
            <label className="field" htmlFor="pl">
              流水线
            </label>
            <select id="pl" value={pipeline} onChange={(e) => setPipeline(e.target.value)} disabled={running}>
              {PIPELINES.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
          <button onClick={run} disabled={running || !question.trim()}>
            {running ? "执行中…" : "开始执行"}
          </button>
        </div>
      </section>

      {phase !== "idle" && (
        <>
          <div className="statusline">
            <span className={`dot ${statusDot}`} />
            <span>{statusText}</span>
          </div>

          <div className="relay">
            {order.map((key) => {
              const n = nodes[key];
              const open = n.status === "succeeded" || n.status === "failed";
              return (
                <div key={key} className={`node ${n.status}`}>
                  <div className={`card ${n.status} ${open ? "open" : ""}`}>
                    <div className="head">
                      <span className="key">{key}</span>
                      {n.provider && <span className="provider">{n.provider}</span>}
                      <span className="badge">{BADGE[n.status]}</span>
                    </div>
                    {n.status === "succeeded" && n.content !== undefined && (
                      <div className="body">
                        <div className="md" dangerouslySetInnerHTML={{ __html: renderMarkdown(n.content) }} />
                      </div>
                    )}
                    {n.status === "failed" && (
                      <div className="errbox">
                        {n.error ? `${n.error.type}: ${n.error.message}` : "步骤失败"}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {banner && <div className="banner">{banner}</div>}

      {finished && jobId && (
        <section className="result">
          <h2>结果</h2>
          <div className="exports">
            <button className="ghost" onClick={() => onExport("merged")} disabled={USE_MOCK}>
              导出合并 Markdown
            </button>
            <button className="ghost" onClick={() => onExport("steps")} disabled={USE_MOCK}>
              导出单步打包
            </button>
            <button className="ghost" onClick={() => onExport("json")} disabled={USE_MOCK}>
              导出 JSON
            </button>
            <button onClick={againRound}>再来一轮</button>
          </div>
          {USE_MOCK && <p className="note">Mock 模式下没有落盘文件，导出按钮已禁用。连接真实后端后可用。</p>}
        </section>
      )}
    </main>
  );
}
