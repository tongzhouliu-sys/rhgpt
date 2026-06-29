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

  const [arrived, setArrived] = useState(false);

  useEffect(() => {
    if (activeProvider || stepKey) {
      setArrived(false);
      const timer = setTimeout(() => {
        setArrived(true);
      }, 1200);
      return () => clearTimeout(timer);
    } else {
      setArrived(false);
    }
  }, [activeProvider, stepKey]);

  const isActive = !!(activeProvider || stepKey);

  return (
    <div className="office-scene-container">
      <div className="office-header">
        <span>🎙️ AI 智能体协同会议中心 (Agent Conference Room)</span>
        <span style={{ color: meta.brandColor }}>⚡ {stepText}</span>
      </div>

      <div className="office-room">
        {/* Left: Moderator / 会议主持人 at podium */}
        <div className="office-station">
          <div
            className="office-bubble"
            style={{
              opacity: isActive && !arrived ? 1 : 0.5,
              transform: isActive && !arrived ? "scale(1)" : "scale(0.9)",
              transition: "opacity 0.4s ease, transform 0.4s ease",
            }}
          >
            {isActive && !arrived
              ? `📋 议题发布中: "${promptSnippet}"`
              : "📋 等待议题…"}
          </div>
          <div
            className="avatar-character"
            style={{
              filter: isActive && !arrived ? "brightness(1.15) drop-shadow(0 0 8px rgba(255,200,60,0.5))" : "none",
              transform: isActive && !arrived ? "scale(1.08)" : "scale(1)",
              transition: "filter 0.4s ease, transform 0.4s ease",
            }}
          >
            🧑‍💼
          </div>
          <div className="station-desk">
            <div className="desk-monitor" />
            <span style={{ fontSize: 11, fontFamily: "var(--mono)", color: "var(--muted)" }}>会议主持人</span>
          </div>
        </div>

        {/* Center: Conference table with microphone */}
        <div className="meeting-table">
          <div
            className="meeting-table-surface"
            style={{
              borderColor: isActive ? meta.brandColor + "80" : undefined,
            }}
          >
            <span
              className="meeting-mic"
              style={{
                opacity: isActive ? 1 : 0.4,
                transform: arrived ? "scale(1.15)" : "scale(1)",
                filter: arrived ? `drop-shadow(0 0 10px ${meta.brandColor}88)` : "none",
                transition: "opacity 0.4s ease, transform 0.5s ease, filter 0.5s ease",
              }}
            >
              🎙️
            </span>
            <span
              style={{
                fontSize: 10,
                fontFamily: "var(--mono)",
                color: "var(--muted)",
                marginTop: 4,
                textAlign: "center",
              }}
            >
              {arrived ? "发言进行中" : isActive ? "议题传达中…" : "会议桌"}
            </span>
          </div>
        </div>

        {/* Right: AI Agent speaker */}
        <div className="office-station">
          {arrived ? (
            <div
              className="office-bubble agent-response"
              style={{
                background: meta.brandColor,
                opacity: 1,
                transform: "scale(1)",
                transition: "opacity 0.4s ease, transform 0.4s ease",
              }}
            >
              🤖 {providerName}: 好的，请稍等！
            </div>
          ) : (
            <div
              className="office-bubble"
              style={{
                background: "transparent",
                border: "none",
                boxShadow: "none",
                opacity: 0.6,
                transform: "scale(0.9)",
                transition: "opacity 0.4s ease, transform 0.4s ease",
              }}
            >
              等待发言…
            </div>
          )}

          <div
            style={{
              position: "relative",
              marginBottom: 4,
              transform: arrived ? "scale(1.12)" : "scale(1)",
              filter: arrived ? `drop-shadow(0 0 12px ${meta.brandColor}66)` : "none",
              transition: "transform 0.5s ease, filter 0.5s ease",
            }}
          >
            <AgentLogo provider={activeProvider} size={40} />
          </div>

          <div className="station-desk" style={{ borderColor: meta.brandColor + "60" }}>
            <div
              className={`desk-monitor ${arrived ? "typing" : ""}`}
              style={{ borderColor: meta.brandColor }}
            />
            <span style={{ fontSize: 12, fontWeight: 700, color: meta.brandColor }}>
              {providerName}
            </span>
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
