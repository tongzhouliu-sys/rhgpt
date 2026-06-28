"use client";

import React from "react";

export interface AgentInfo {
  id: string;
  name: string;
  brandColor: string;
  bgGlow: string;
}

export const AGENT_MAP: Record<string, AgentInfo> = {
  chatgpt: { id: "chatgpt", name: "ChatGPT 4o", brandColor: "#10a37f", bgGlow: "rgba(16, 163, 127, 0.2)" },
  claude: { id: "claude", name: "Claude 3.5", brandColor: "#d97706", bgGlow: "rgba(217, 119, 6, 0.2)" },
  deepseek: { id: "deepseek", name: "DeepSeek V3", brandColor: "#3b82f6", bgGlow: "rgba(59, 130, 246, 0.2)" },
  kimi: { id: "kimi", name: "Kimi Chat", brandColor: "#e11d48", bgGlow: "rgba(225, 29, 72, 0.2)" },
  zai: { id: "zai", name: "智谱清言", brandColor: "#8b5cf6", bgGlow: "rgba(139, 92, 246, 0.2)" },
  gemini_api: { id: "gemini_api", name: "Gemini 1.5 Pro", brandColor: "#0ea5e9", bgGlow: "rgba(14, 165, 233, 0.2)" },
  qwen_api: { id: "qwen_api", name: "通义千问", brandColor: "#f97316", bgGlow: "rgba(249, 115, 22, 0.2)" },
};

export function getAgentMeta(provider?: string): AgentInfo {
  if (!provider) {
    return { id: "default", name: "AI 调度中心", brandColor: "#38bdf8", bgGlow: "rgba(56, 189, 248, 0.2)" };
  }
  const low = provider.toLowerCase();
  for (const key of Object.keys(AGENT_MAP)) {
    if (low.includes(key) || AGENT_MAP[key].name.toLowerCase().includes(low)) {
      return AGENT_MAP[key];
    }
  }
  if (low.includes("gemini")) return AGENT_MAP["gemini_api"];
  if (low.includes("qwen") || low.includes("千问")) return AGENT_MAP["qwen_api"];
  if (low.includes("智谱")) return AGENT_MAP["zai"];

  return { id: provider, name: provider, brandColor: "#a855f7", bgGlow: "rgba(168, 85, 247, 0.2)" };
}

interface AgentLogoProps {
  provider?: string;
  size?: number;
  className?: string;
}

export default function AgentLogo({ provider, size = 24, className = "" }: AgentLogoProps) {
  const meta = getAgentMeta(provider);
  const id = meta.id;

  // Render provider specific stylized SVG logos
  const renderSvg = () => {
    switch (id) {
      case "chatgpt":
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke={meta.brandColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 14a4 4 0 1 1 0-8 4 4 0 0 1 0 8z" />
            <circle cx="12" cy="12" r="2" fill={meta.brandColor} />
          </svg>
        );
      case "claude":
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke={meta.brandColor} strokeWidth="2" strokeLinecap="round">
            <path d="M12 3v18M3 12h18M5.5 5.5l13 13M18.5 5.5l-13 13" />
          </svg>
        );
      case "deepseek":
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <path d="M4 14c2-5 6-9 11-9 4 0 5 3 3 6-2 4-7 8-12 8 0 0 1-3 3-5z" fill={meta.brandColor} opacity="0.8" />
            <circle cx="15" cy="8" r="1.5" fill="#fff" />
          </svg>
        );
      case "kimi":
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke={meta.brandColor} strokeWidth="2">
            <path d="M12 2l2.5 7.5H22l-6 4.5 2.5 7.5-6.5-5-6.5 5 2.5-7.5-6-4.5h7.5z" fill={meta.brandColor} opacity="0.3" />
            <circle cx="12" cy="12" r="4" stroke={meta.brandColor} strokeWidth="2" />
          </svg>
        );
      case "zai":
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <rect x="4" y="4" width="16" height="16" rx="4" fill={meta.brandColor} opacity="0.8" />
            <path d="M8 12h8M12 8v8" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
          </svg>
        );
      case "gemini_api":
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <path d="M12 2C12 7.5 7.5 12 2 12c5.5 0 10 4.5 10 10 0-5.5 4.5-10 10-10-5.5 0-10-4.5-10-10z" fill={meta.brandColor} />
          </svg>
        );
      case "qwen_api":
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke={meta.brandColor} strokeWidth="2">
            <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
            <path d="M12 12l8-4.5M12 12v9M12 12L4 7.5" />
          </svg>
        );
      default:
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke={meta.brandColor} strokeWidth="2">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="2" />
            <path d="M12 7v4" />
            <circle cx="8" cy="15" r="1" fill={meta.brandColor} />
            <circle cx="16" cy="15" r="1" fill={meta.brandColor} />
          </svg>
        );
    }
  };

  return (
    <span
      className={`agent-logo-wrapper ${className}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: size + 8,
        height: size + 8,
        borderRadius: "50%",
        backgroundColor: meta.bgGlow,
        border: `1px solid ${meta.brandColor}40`,
        flexShrink: 0,
      }}
      title={meta.name}
    >
      {renderSvg()}
    </span>
  );
}
