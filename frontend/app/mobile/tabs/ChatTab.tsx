"use client";

import React from "react";
import { useAppJob, useAppSettings } from "../../context/AppContext";
import AgentLogo from "../../components/AgentLogo";

interface ChatTabProps {
  onGoToTask: () => void;
  onGoToSettings: () => void;
}

export const ChatTab: React.FC<ChatTabProps> = React.memo(({ onGoToTask, onGoToSettings }) => {
  const { question, setQuestion, phase, run, cancel, jobId, chatHistory, loadHistoryItem } = useAppJob();
  const { availableModels, selectedModels } = useAppSettings();

  const running = phase === "running";
  const activeModels = availableModels.filter((m) => selectedModels.includes(m.id));

  return (
    <div className="mobile-tab-content">
      {/* 顶部简易品牌标 */}
      <div className="mobile-chat-header">
        <span className="brand" style={{ fontSize: "16px" }}>RHCLOUD V1</span>
        <span style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--mono)" }}>AI 智能接力</span>
      </div>

      {/* 运行中任务摘要引导卡 */}
      {running && (
        <div className="mobile-running-card" onClick={onGoToTask}>
          <div className="mobile-running-info">
            <span className="tab-pulse-dot" style={{ position: "static", display: "inline-block" }} />
            <strong>AI 接力正在协同运行中...</strong>
          </div>
          <span style={{ fontSize: "12px", color: "var(--accent)" }}>查看详情 ›</span>
        </div>
      )}

      {/* 输入框卡片 */}
      <div className="mobile-card">
        <label className="field" htmlFor="mobile-q">
          输入您的任务或提问 (Prompt)
        </label>
        <textarea
          id="mobile-q"
          rows={4}
          placeholder="例如：帮我设计一个高并发短链服务架构..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={running}
          style={{ width: "100%", marginBottom: "12px" }}
        />

        {/* 已选模型微缩图（点击跳设置） */}
        <div className="mobile-model-summary" onClick={onGoToSettings}>
          <span style={{ fontSize: "12px", color: "var(--muted)" }}>参与模型 ({activeModels.length}):</span>
          <div className="mobile-model-logos">
            {activeModels.slice(0, 5).map((m) => (
              <AgentLogo key={m.id} provider={m.site} size={16} />
            ))}
            {activeModels.length > 5 && (
              <span style={{ fontSize: "11px", color: "var(--muted)" }}>+{activeModels.length - 5}</span>
            )}
          </div>
          <span style={{ fontSize: "12px", color: "var(--accent)", marginLeft: "auto" }}>修改 ›</span>
        </div>

        <div style={{ marginTop: "16px", display: "flex", gap: "10px" }}>
          <button
            id="mobile-start-btn"
            onClick={run}
            disabled={running || !question.trim()}
            style={{ flex: 1, height: "46px" }}
          >
            {running ? "🚀 协同中…" : "🚀 开始接力执行"}
          </button>
          {running && (
            <button
              className="ghost"
              onClick={cancel}
              style={{ color: "var(--danger)", borderColor: "var(--danger)", height: "46px" }}
            >
              🛑 终止
            </button>
          )}
        </div>
      </div>

      {/* 历史记录 */}
      {chatHistory.length > 0 && (
        <div className="mobile-card" style={{ marginTop: "16px" }}>
          <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", color: "var(--muted)" }}>🕒 历史记录</h4>
          <div className="mobile-history-list">
            {chatHistory.map((item) => (
              <div
                key={item.jobId}
                className="mobile-history-item"
                onClick={() => {
                  loadHistoryItem(item);
                  onGoToTask();
                }}
              >
                <div className="mobile-history-q">{item.question}</div>
                <div className="mobile-history-meta">
                  <span>{new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  <span className={`status-tag ${item.finalStatus}`}>{item.finalStatus}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

ChatTab.displayName = "ChatTab";
