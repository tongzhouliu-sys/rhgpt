"use client";

import React from "react";
import { renderMarkdown } from "../../../lib/markdown";
import AgentLogo from "../AgentLogo";

export type NodeStatus = "running" | "succeeded" | "failed";

export interface NodeState {
  key: string;
  provider?: string;
  label?: string;
  model?: string;
  status: NodeStatus;
  queuedPosition?: number;
  content?: string;
  error?: { type: string; message: string };
  runnerups?: Record<string, string>;
  runnerupTyping?: Record<string, boolean>;
  runnerupLabels?: Record<string, string>;
}

const BADGE: Record<NodeStatus, string> = {
  running: "运行中",
  succeeded: "完成",
  failed: "失败",
};

const STEP_LABELS: Record<string, string> = {
  generate: "1/5 初稿生成",
  review: "2/5 交叉评审",
  deep_analyze: "3/5 逻辑拆解",
  improve: "4/5 方案优化",
  summary: "5/5 总结收尾",
};

interface NodeCardProps {
  nodeKey: string;
  node: NodeState;
  open: boolean;
  onToggleExpand: (key: string) => void;
}

export const NodeCard: React.FC<NodeCardProps> = React.memo(
  ({ nodeKey, node, open, onToggleExpand }) => {
    const n = node;
    const hasRunnerups = n.runnerups && Object.keys(n.runnerups).length > 0;
    const isQueued = n.status === "running" && n.queuedPosition !== undefined;
    const isWinnerTyping =
      n.status === "running" &&
      n.content &&
      !n.content.startsWith("⚡") &&
      !n.content.startsWith("🔄") &&
      !n.content.startsWith("⏳");
    const isTransitioning =
      n.status === "running" &&
      n.content &&
      (n.content.startsWith("🔄") || n.content.startsWith("⏳"));

    return (
      <div className={`node ${n.status}`}>
        <div className={`card ${n.status} ${open ? "open" : ""}`}>
          <div
            className="head"
            onClick={() => onToggleExpand(nodeKey)}
            style={{ cursor: "pointer", userSelect: "none" }}
            title="点击展开/折叠该模型回答"
          >
            <span className="key">{STEP_LABELS[nodeKey] || nodeKey}</span>
            {n.provider && (
              <div className="provider-tag">
                <AgentLogo provider={n.provider} size={16} />
                <span>{n.label || n.provider}</span>
                {n.model && (
                  <span style={{ fontSize: "10px", color: "var(--muted)", fontFamily: "var(--mono)" }}>
                    ({n.model})
                  </span>
                )}
              </div>
            )}
            {n.status === "succeeded" && n.provider && hasRunnerups && (
              <span className="winner-crown">🏆 最快</span>
            )}
            <span className="badge">
              {isQueued
                ? `⏳ 排队中 (${n.queuedPosition}位)`
                : n.status === "running" && isWinnerTyping
                ? "打字中..."
                : BADGE[n.status]}
            </span>
            {hasRunnerups && (
              <span style={{ fontSize: "11px", color: "var(--accent)", fontFamily: "var(--mono)", fontWeight: 600 }}>
                +{Object.keys(n.runnerups!).length} 个模型方案
              </span>
            )}
            <span style={{ fontSize: "12px", color: "var(--muted)", marginLeft: "4px", fontFamily: "var(--mono)" }}>
              {open ? "▲" : "▼"}
            </span>
          </div>

          {/* Step transition animation / queuing animation */}
          {open && isTransitioning && (
            <div className="body">
              <div className="step-transition-card">
                <div className="step-transition-spinner" />
                <span>{n.content}</span>
              </div>
            </div>
          )}

          {/* Main body: parallel race lanes */}
          {open && !isTransitioning && (n.status === "succeeded" || (n.status === "running" && n.content)) && (
            <div className="body">
              {/* Winner (primary) lane */}
              <div className={`race-lane-card is-winner ${isWinnerTyping ? "is-typing" : ""}`}>
                <div className="race-lane-header">
                  {n.provider && <AgentLogo provider={n.provider} size={14} />}
                  <span className="winner-title">{n.label || n.provider || "模型"}</span>
                  {n.model && (
                    <span style={{ fontSize: "10px", color: "var(--muted)", fontFamily: "var(--mono)" }}>
                      ({n.model})
                    </span>
                  )}
                  {n.status === "succeeded" && <span className="winner-crown">🏆 最快锁定</span>}
                  {isWinnerTyping && (
                    <div className="lane-typing-dots">
                      <span />
                      <span />
                      <span />
                    </div>
                  )}
                </div>
                <div className="race-lane-body">
                  <div className="md" dangerouslySetInnerHTML={{ __html: renderMarkdown(n.content || "") }} />
                  {isWinnerTyping && <span className="typing-cursor" />}
                </div>
              </div>

              {/* Runnerup race lanes — all visible, streaming live */}
              {hasRunnerups && (
                <div className={`race-lanes ${Object.keys(n.runnerups!).length > 1 ? "has-multiple" : ""}`}>
                  {Object.entries(n.runnerups!).map(([rProvider, rContent]) => {
                    const isRTyping = n.runnerupTyping?.[rProvider] !== false && n.status === "running";
                    return (
                      <div key={rProvider} className={`race-lane-card ${isRTyping ? "is-typing" : ""}`}>
                        <div className="race-lane-header">
                          <AgentLogo provider={rProvider} size={14} />
                          <span>{n.runnerupLabels?.[rProvider] || rProvider}</span>
                          {!isRTyping && (
                            <span style={{ fontSize: "10px", color: "var(--success)", fontFamily: "var(--mono)", fontWeight: 700 }}>
                              ✓ 完成
                            </span>
                          )}
                          {isRTyping && (
                            <div className="lane-typing-dots">
                              <span />
                              <span />
                              <span />
                            </div>
                          )}
                        </div>
                        <div className="race-lane-body">
                          <div className="md" dangerouslySetInnerHTML={{ __html: renderMarkdown(rContent) }} />
                          {isRTyping && <span className="typing-cursor" />}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {open && n.status === "failed" && (
            <div className="errbox">
              {n.error ? `${n.error.type}: ${n.error.message}` : "步骤失败"}
            </div>
          )}
        </div>
      </div>
    );
  }
);

NodeCard.displayName = "NodeCard";
