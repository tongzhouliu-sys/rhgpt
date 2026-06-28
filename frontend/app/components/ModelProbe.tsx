"use client";

interface ModelInfo {
  id: string;
  name: string;
  type: "web" | "api";
  profile: string;
  ready: boolean;
}

const MODELS: ModelInfo[] = [
  { id: "chatgpt", name: "ChatGPT 4o", type: "web", profile: "chatgpt_acc1", ready: true },
  { id: "claude", name: "Claude 3.5", type: "web", profile: "claude_acc1", ready: true },
  { id: "deepseek", name: "DeepSeek V3", type: "web", profile: "deepseek_acc1", ready: true },
  { id: "kimi", name: "Kimi Chat", type: "web", profile: "kimi_acc1", ready: true },
  { id: "zai", name: "智谱清言 (Zai)", type: "web", profile: "zai_acc1", ready: true },
  { id: "gemini_api", name: "Gemini 1.5 Pro", type: "api", profile: "API Key", ready: true },
  { id: "qwen_api", name: "通义千问 Qwen", type: "api", profile: "API Key", ready: true },
];

export default function ModelProbe() {
  return (
    <section className="panel probe-section">
      <div className="probe-header-title">
        <label className="field" style={{ margin: 0 }}>
          📡 大模型可用性探针 (Model Readiness Probe)
        </label>
        <span className="probe-tag" style={{ color: "var(--accent)" }}>
          7 个模型监控中
        </span>
      </div>
      <div className="probe-grid">
        {MODELS.map((m) => (
          <div key={m.id} className="probe-card">
            <div className="probe-header">
              <span className="probe-name">{m.name}</span>
              <span className="probe-tag">{m.type === "web" ? "Web自动化" : "官方API"}</span>
            </div>
            <div className="probe-status">
              <span className={`probe-indicator ${m.type === "web" ? "ready" : "api"}`} />
              <span style={{ color: "var(--text)" }}>{m.profile}</span>
              <span style={{ marginLeft: "auto", color: "var(--muted)", fontSize: "10px" }}>
                在线就绪
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
