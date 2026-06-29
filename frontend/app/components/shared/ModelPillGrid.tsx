"use client";

import React from "react";
import type { ProviderInfo } from "../../../lib/api";
import AgentLogo from "../AgentLogo";

interface ModelPillGridProps {
  availableModels: ProviderInfo[];
  selectedModels: string[];
  toggleModel: (id: string) => void;
  selectOnlyAPI: () => void;
  selectAllModels: () => void;
  disabled?: boolean;
  showHeaders?: boolean;
}

export const ModelPillGrid: React.FC<ModelPillGridProps> = React.memo(
  ({
    availableModels,
    selectedModels,
    toggleModel,
    selectOnlyAPI,
    selectAllModels,
    disabled = false,
    showHeaders = true,
  }) => {
    return (
      <div className="model-select-wrapper">
        {showHeaders && (
          <div className="model-select-header">
            <label className="field" style={{ margin: 0 }}>
              🤖 选择参与接力互动的大模型 (可多选，直连 API 优先)
            </label>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                className="ghost"
                style={{ padding: "5px 12px", fontSize: "12px" }}
                onClick={selectOnlyAPI}
                disabled={disabled}
              >
                ⚡ 仅选直连 API
              </button>
              <button
                type="button"
                className="ghost"
                style={{ padding: "5px 12px", fontSize: "12px" }}
                onClick={selectAllModels}
                disabled={disabled}
              >
                🌐 全选所有模型
              </button>
            </div>
          </div>
        )}
        <div className="model-select-grid">
          {availableModels.map((m) => {
            const checked = selectedModels.includes(m.id);
            return (
              <label
                key={m.id}
                className={`model-pill ${checked ? (m.api ? "active active-api" : "active") : ""}`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleModel(m.id)}
                  disabled={disabled}
                />
                <AgentLogo provider={m.site} size={16} />
                <span>
                  {m.label}
                  {m.model ? ` (${m.model})` : ""}
                </span>
                <span className={`model-badge-tag ${m.api ? "api" : "web"}`}>
                  {m.api ? "API" : "Web"}
                </span>
              </label>
            );
          })}
        </div>
      </div>
    );
  }
);

ModelPillGrid.displayName = "ModelPillGrid";
