"use client";

import React, { useState } from "react";
import { useAppJob } from "../context/AppContext";
import { TabBar, type TabType } from "../components/shared/TabBar";
import { ChatTab } from "../mobile/tabs/ChatTab";
import { TaskTab } from "../mobile/tabs/TaskTab";
import { FilesTab } from "../mobile/tabs/FilesTab";
import { SettingsTab } from "../mobile/tabs/SettingsTab";

export const MobileLayout: React.FC = React.memo(() => {
  const [activeTab, setActiveTab] = useState<TabType>("chat");
  const { phase } = useAppJob();

  const running = phase === "running";
  const finished = phase === "done";

  return (
    <div className="mobile-shell">
      <main className="mobile-content-container">
        <div style={{ display: activeTab === "chat" ? "block" : "none", height: "100%" }}>
          <ChatTab
            onGoToTask={() => setActiveTab("task")}
            onGoToSettings={() => setActiveTab("settings")}
          />
        </div>

        <div style={{ display: activeTab === "task" ? "block" : "none", height: "100%" }}>
          <TaskTab onGoToChat={() => setActiveTab("chat")} />
        </div>

        <div style={{ display: activeTab === "files" ? "block" : "none", height: "100%" }}>
          <FilesTab onGoToTask={() => setActiveTab("task")} />
        </div>

        <div style={{ display: activeTab === "settings" ? "block" : "none", height: "100%" }}>
          <SettingsTab />
        </div>
      </main>

      <TabBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        running={running}
        finished={finished}
      />
    </div>
  );
});

MobileLayout.displayName = "MobileLayout";
