"use client";

import { useEffect, useState } from "react";
import AgentLogo, { getAgentMeta } from "./AgentLogo";

interface AvatarSceneProps {
  activeProvider?: string;
  stepKey?: string;
  question?: string;
}

export default function AvatarScene({ activeProvider, stepKey, question }: AvatarSceneProps) {
  const meta = getAgentMeta(activeProvider);
  const providerName = meta.name;
  const stepText = stepKey ? `正在协同处理步骤: ${stepKey}` : "AI 调度与流程对接中...";
  const promptSnippet = question?.trim() ? (question.length > 28 ? question.slice(0, 28) + "…" : question) : "帮我设计智能协同架构及流程";

  // Control animation stages: "running" -> messenger walking, "arrived" -> agent replying "好的，请稍等" & typing
  const [arrived, setArrived] = useState(false);

  useEffect(() => {
    if (activeProvider || stepKey) {
      setArrived(false);
      const timer = setTimeout(() => {
        setArrived(true);
      }, 1200); // Messenger arrives after 1.2s
      return () => clearTimeout(timer);
    } else {
      setArrived(false);
    }
  }, [activeProvider, stepKey]);

  return (
    <div className="office-scene-container">
      <div className="office-header">
        <span>🏢 AI 智能体办公室协同交互中心 (Agent Office Floor)</span>
        <span style={{ color: meta.brandColor }}>⚡ {stepText}</span>
      </div>

      <div className="office-room">
        {/* 1. 调度员岗位 (Left side) */}
        <div className="office-station">
          <div className="office-bubble">Dispatching task...</div>
          <div className="avatar-character">🧑‍💻</div>
          <div className="station-desk">
            <div className="desk-monitor" />
            <span style={{ fontSize: 11, fontFamily: "var(--mono)", color: "var(--muted)" }}>中枢总控</span>
          </div>
        </div>

        {/* 2. 奔跑传递信息的调度小人 (Messenger) */}
        <div className={`messenger-runner ${activeProvider || stepKey ? (arrived ? "running" : "running") : "idle"}`}>
          {!arrived ? (
            <div className="office-bubble">💬 "{promptSnippet}"</div>
          ) : (
            <div className="office-bubble" style={{ opacity: 0.7, transform: "scale(0.85)" }}>
              📥 已达目标工位
            </div>
          )}
          <div className="avatar-character bounce">🏃‍♂️</div>
        </div>

        {/* 3. 目标智能体工作站 (Right side) */}
        <div className="office-station">
          {arrived ? (
            <div className="office-bubble agent-response" style={{ background: meta.brandColor }}>
              🤖 {providerName}: 好的，请稍等！
            </div>
          ) : (
            <div className="office-bubble" style={{ background: "transparent", border: "none", boxShadow: "none", opacity: 0.6 }}>
              等待任务…
            </div>
          )}

          <div style={{ position: "relative", marginBottom: 4 }}>
            <AgentLogo provider={activeProvider} size={40} />
          </div>

          <div className="station-desk" style={{ borderColor: meta.brandColor + "60" }}>
            <div className={`desk-monitor ${arrived ? "typing" : ""}`} style={{ borderColor: meta.brandColor }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: meta.brandColor }}>{providerName}</span>
            {arrived && (
              <div className="typing-indicator">
                <span className="typing-dot" style={{ background: meta.brandColor }} />
                <span className="typing-dot" style={{ background: meta.brandColor }} />
                <span className="typing-dot" style={{ background: meta.brandColor }} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
