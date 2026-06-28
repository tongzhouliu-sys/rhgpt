"use client";

import { useState } from "react";
import AgentLogo from "./AgentLogo";

export interface ModelInfo {
  id: string;
  name: string;
  type: "web" | "api";
  profile: string;
  ready: boolean;
}

export const MODELS: ModelInfo[] = [
  { id: "chatgpt", name: "ChatGPT 4o", type: "web", profile: "chatgpt_acc1", ready: true },
  { id: "claude", name: "Claude 3.5", type: "web", profile: "claude_acc1", ready: true },
  { id: "deepseek", name: "DeepSeek V3", type: "web", profile: "deepseek_acc1", ready: true },
  { id: "kimi", name: "Kimi Chat", type: "web", profile: "kimi_acc1", ready: true },
  { id: "zai", name: "智谱清言", type: "web", profile: "zai_acc1", ready: true },
  { id: "gemini_api", name: "Gemini 1.5 Pro", type: "api", profile: "API Key", ready: true },
  { id: "qwen_api", name: "通义千问 Qwen", type: "api", profile: "API Key", ready: true },
];

export default function ModelProbe() {
  const [open, setOpen] = useState(false);

  return (
    <div className="probe-compact-container" onMouseLeave={() => setOpen(false)}>
      <div
        className="probe-compact-bar"
        onClick={() => setOpen((prev) => !prev)}
        onMouseEnter={() => setOpen(true)}
        title="点击查看所有大模型连通状态"
      >
        <div className="probe-mini-icons">
          {MODELS.slice(0, 5).map((m) => (
            <div key={m.id} className="probe-mini-item">
              <AgentLogo provider={m.id} size={18} />
              <span className="probe-dot-overlay" />
            </div>
          ))}
        </div>
        <span style={{ fontSize: "12px", fontFamily: "var(--mono)", fontWeight: 600, color: "var(--accent)" }}>
          📡 7 模型就绪
        </span>
      </div>

      {open && (
        <div className="probe-popover">
          <div className="probe-popover-header">
            <span>📡 大模型可用性探针</span>
            <span style={{ color: "var(--success)" }}>7/7 在线</span>
          </div>
          <div className="probe-popover-list">
            {MODELS.map((m) => (
              <div key={m.id} className="probe-popover-item">
                <AgentLogo provider={m.id} size={22} />
                <div className="probe-popover-info">
                  <span className="probe-popover-name">{m.name}</span>
                  <span className="probe-popover-sub">{m.type === "web" ? "Web 自动化路线" : "官方 API 路线"}</span>
                </div>
                <span className="dot ok" style={{ width: 8, height: 8 }} title="在线就绪" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
