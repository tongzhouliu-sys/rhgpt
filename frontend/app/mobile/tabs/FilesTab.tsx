"use client";

import React from "react";
import { USE_MOCK } from "../../../lib/api";
import { useAppJob } from "../../context/AppContext";

interface FilesTabProps {
  onGoToTask: () => void;
}

export const FilesTab: React.FC<FilesTabProps> = React.memo(({ onGoToTask }) => {
  const { phase, jobId, onExport, againRound } = useAppJob();
  const finished = phase === "done";

  return (
    <div className="mobile-tab-content">
      <div className="mobile-chat-header">
        <span className="brand" style={{ fontSize: "16px" }}>RHCLOUD V1</span>
        <span style={{ fontSize: "12px", color: "var(--muted)" }}>文件导出中心</span>
      </div>

      <div className="mobile-card">
        <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", color: "var(--accent)" }}>📥 结果文件导出</h3>
        <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: "1.5", marginBottom: "20px" }}>
          当多模型协同任务完成后，您可以在此处按格式导出产出成果。
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <button
            className="ghost"
            onClick={() => onExport("merged")}
            disabled={!finished || !jobId || USE_MOCK}
            style={{ height: "48px", width: "100%", justifyContent: "center" }}
          >
            📄 导出合并 Markdown
          </button>

          <button
            className="ghost"
            onClick={() => onExport("steps")}
            disabled={!finished || !jobId || USE_MOCK}
            style={{ height: "48px", width: "100%", justifyContent: "center" }}
          >
            📦 导出单步 ZIP 打包
          </button>

          <button
            className="ghost"
            onClick={() => onExport("json")}
            disabled={!finished || !jobId || USE_MOCK}
            style={{ height: "48px", width: "100%", justifyContent: "center" }}
          >
            🔍 导出 JSON 上下文
          </button>

          <button
            onClick={() => {
              againRound();
              onGoToTask();
            }}
            disabled={!finished}
            style={{ height: "48px", width: "100%", marginTop: "8px" }}
          >
            🔄 基于结果再来一轮接力
          </button>
        </div>

        {USE_MOCK && (
          <p style={{ fontSize: "12px", color: "var(--muted)", marginTop: "16px", textAlign: "center" }}>
            Mock 模式下没有落盘文件，导出按钮已禁用。连接真实后端后可用。
          </p>
        )}
        {!finished && !USE_MOCK && (
          <p style={{ fontSize: "12px", color: "var(--muted)", marginTop: "16px", textAlign: "center" }}>
            当前任务尚未完成，导出功能暂不可用。
          </p>
        )}
      </div>
    </div>
  );
});

FilesTab.displayName = "FilesTab";
