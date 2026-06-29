"use client";

import React from "react";

export type TabType = "chat" | "task" | "files" | "settings";

interface TabBarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  running: boolean;
  finished: boolean;
}

export const TabBar: React.FC<TabBarProps> = React.memo(
  ({ activeTab, onTabChange, running, finished }) => {
    return (
      <nav className="mobile-tab-bar">
        <button
          type="button"
          className={`tab-item ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => onTabChange("chat")}
        >
          <div className="tab-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <span className="tab-label">对话</span>
        </button>

        <button
          type="button"
          className={`tab-item ${activeTab === "task" ? "active" : ""}`}
          onClick={() => onTabChange("task")}
        >
          <div className="tab-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="10" y1="6" x2="21" y2="6" />
              <line x1="10" y1="12" x2="21" y2="12" />
              <line x1="10" y1="18" x2="21" y2="18" />
              <polyline points="3 6 4 7 6 5" />
              <polyline points="3 12 4 13 6 11" />
              <polyline points="3 18 4 19 6 17" />
            </svg>
            {running && <span className="tab-pulse-dot" />}
          </div>
          <span className="tab-label">任务</span>
        </button>

        <button
          type="button"
          className={`tab-item ${activeTab === "files" ? "active" : ""}`}
          onClick={() => onTabChange("files")}
        >
          <div className="tab-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            {finished && <span className="tab-badge-dot" />}
          </div>
          <span className="tab-label">文件</span>
        </button>

        <button
          type="button"
          className={`tab-item ${activeTab === "settings" ? "active" : ""}`}
          onClick={() => onTabChange("settings")}
        >
          <div className="tab-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </div>
          <span className="tab-label">设置</span>
        </button>
      </nav>
    );
  }
);

TabBar.displayName = "TabBar";
