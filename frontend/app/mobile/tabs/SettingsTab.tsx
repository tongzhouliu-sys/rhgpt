"use client";

import React from "react";
import { PIPELINES, useAppJob, useAppSettings } from "../../context/AppContext";
import { ModelPillGrid } from "../../components/shared/ModelPillGrid";
import ModelProbe from "../../components/ModelProbe";

export const SettingsTab: React.FC = React.memo(() => {
  const { theme, pipeline, availableModels, selectedModels, toggleTheme, toggleModel, selectOnlyAPI, selectAllModels, setPipeline } =
    useAppSettings();
  const { phase } = useAppJob();
  const running = phase === "running";

  return (
    <div className="mobile-tab-content">
      <div className="mobile-chat-header">
        <span className="brand" style={{ fontSize: "16px" }}>RHCLOUD V1</span>
        <span style={{ fontSize: "12px", color: "var(--muted)" }}>系统与模型配置</span>
      </div>

      {/* 主题控制 */}
      <div className="mobile-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <strong style={{ fontSize: "15px" }}>外观主题</strong>
          <div style={{ fontSize: "12px", color: "var(--muted)", marginTop: "2px" }}>
            当前皮肤: {theme === "dark" ? "深色暗夜" : "浅色明亮"}
          </div>
        </div>
        <button className="theme-toggle" onClick={toggleTheme} style={{ padding: "8px 16px" }}>
          {theme === "dark" ? "☀️ 浅色" : "🌙 深色"}
        </button>
      </div>

      {/* 流水线配置 */}
      <div className="mobile-card" style={{ marginTop: "14px" }}>
        <label className="field" htmlFor="mobile-pl" style={{ margin: "0 0 8px 0" }}>
          选择默认执行流水线
        </label>
        <select
          id="mobile-pl"
          value={pipeline}
          onChange={(e) => setPipeline(e.target.value)}
          disabled={running}
          style={{ width: "100%", height: "42px" }}
        >
          {PIPELINES.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      {/* 模型选择网格 */}
      <div className="mobile-card" style={{ marginTop: "14px" }}>
        <ModelPillGrid
          availableModels={availableModels}
          selectedModels={selectedModels}
          toggleModel={toggleModel}
          selectOnlyAPI={selectOnlyAPI}
          selectAllModels={selectAllModels}
          disabled={running}
        />
      </div>

      {/* 探针常驻 */}
      <div className="mobile-card" style={{ marginTop: "14px", padding: "12px" }}>
        <ModelProbe alwaysOpen={true} />
      </div>
    </div>
  );
});

SettingsTab.displayName = "SettingsTab";
