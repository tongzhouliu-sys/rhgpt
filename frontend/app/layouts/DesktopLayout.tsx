"use client";

import React from "react";
import { USE_MOCK } from "../../lib/api";
import { PIPELINES, useAppJob, useAppSettings } from "../context/AppContext";
import ModelProbe from "../components/ModelProbe";
import AvatarScene from "../components/AvatarScene";
import { ModelPillGrid } from "../components/shared/ModelPillGrid";
import { ProgressBanner } from "../components/shared/ProgressBanner";
import { NodeCard } from "../components/shared/NodeCard";

export const DesktopLayout: React.FC = React.memo(() => {
  const {
    theme,
    pipeline,
    availableModels,
    selectedModels,
    toggleTheme,
    toggleModel,
    selectOnlyAPI,
    selectAllModels,
    setPipeline,
  } = useAppSettings();

  const {
    question,
    setQuestion,
    phase,
    order,
    nodes,
    jobId,
    banner,
    expandedKeys,
    concurrentBusy,
    setConcurrentBusy,
    run,
    cancel,
    againRound,
    onExport,
    toggleExpand,
  } = useAppJob();

  const running = phase === "running";
  const finished = phase === "done";

  const currentRunningKey = order.find((k) => nodes[k]?.status === "running");
  const currentProvider = currentRunningKey ? nodes[currentRunningKey]?.provider : undefined;

  return (
    <main className="wrap">
      {/* 顶部 Navigation / Masthead */}
      <header className="masthead">
        <div className="brand-group">
          <div className="brand-row">
            <span className="brand">RHCLOUD V1</span>
            <h1>AI 智能接力协作控制台</h1>
          </div>
          <span className="sub">multi-model relay console {USE_MOCK ? "· MOCK 模式" : ""}</span>
        </div>

        <div className="masthead-actions">
          {/* 大模型可用性探针（右侧图标展示） */}
          <ModelProbe />

          {/* 深色 / 浅色皮肤切换按钮 */}
          <button className="theme-toggle" onClick={toggleTheme} title="切换外观主题">
            {theme === "dark" ? "☀️ 浅色" : "🌙 深色"}
          </button>
        </div>
      </header>

      {/* 交互控制面板 */}
      <section className="panel">
        <label className="field" htmlFor="q">
          输入您的任务或提问 (Prompt)
        </label>
        <textarea
          id="q"
          rows={4}
          placeholder="例如：帮我设计一个高并发短链服务架构，包含缓存与数据库设计"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={running}
        />

        <ModelPillGrid
          availableModels={availableModels}
          selectedModels={selectedModels}
          toggleModel={toggleModel}
          selectOnlyAPI={selectOnlyAPI}
          selectAllModels={selectAllModels}
          disabled={running}
        />

        <div className="controls">
          <div className="grow">
            <label className="field" htmlFor="pl">
              选择执行流水线
            </label>
            <select id="pl" value={pipeline} onChange={(e) => setPipeline(e.target.value)} disabled={running}>
              {PIPELINES.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
          <button id="start-btn" onClick={run} disabled={running || !question.trim()}>
            {running ? "🚀 智能协同中…" : "🚀 开始接力执行"}
          </button>
          {running && (
            <button className="ghost" onClick={cancel} style={{ color: "var(--danger)", borderColor: "var(--danger)" }}>
              🛑 终止任务
            </button>
          )}
        </div>
      </section>

      {/* 并发已满或限制时的友好降级交互卡片 */}
      {concurrentBusy && (
        <section className="panel" style={{ border: "1px solid var(--warn)", background: "rgba(251, 191, 36, 0.08)", marginTop: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "var(--warn)", fontWeight: 700, fontSize: "16px" }}>
            <span style={{ fontSize: "22px" }}>⚠️</span>
            <span>当前通道并发已满 (Max Concurrent Jobs Reached)</span>
          </div>
          <p style={{ margin: "12px 0 18px 0", fontSize: "14px", lineHeight: "1.6", color: "var(--text)" }}>
            系统检测到当前模型通道繁忙。您无需终止任务，建议立即一键切换为高效【直连 API 模型组】继续工作，或点击重试：
          </p>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={() => {
                setConcurrentBusy(false);
                selectOnlyAPI();
                setTimeout(() => {
                  const btn = document.getElementById("start-btn");
                  if (btn) btn.click();
                }, 100);
              }}
              style={{ background: "linear-gradient(135deg, var(--warn), #f59e0b)", color: "#000" }}
            >
              ⚡ 切换为【直连 API】继续重试
            </button>
            <button
              type="button"
              className="ghost"
              onClick={() => {
                setConcurrentBusy(false);
                const btn = document.getElementById("start-btn");
                if (btn) btn.click();
              }}
            >
              🔄 原模型组重试
            </button>
          </div>
        </section>
      )}

      {/* 动态小人沟通互动办公室场景 (运行中或已有执行步骤时展示) */}
      {(running || phase !== "idle") && (
        <AvatarScene activeProvider={currentProvider} stepKey={currentRunningKey} question={question} />
      )}

      {/* 任务执行时间轴与节点卡片 */}
      {phase !== "idle" && (
        <>
          <ProgressBanner
            running={running}
            finished={finished}
            phase={phase}
            orderLength={order.length}
            currentRunningKey={currentRunningKey}
          />

          <div className="relay">
            {order.map((key, idx) => {
              const n = nodes[key];
              if (!n) return null;
              const isLast = idx === order.length - 1;
              const open = expandedKeys[key] !== undefined ? expandedKeys[key] : isLast;
              return (
                <NodeCard
                  key={key}
                  nodeKey={key}
                  node={n}
                  open={open}
                  onToggleExpand={toggleExpand}
                />
              );
            })}
          </div>
        </>
      )}

      {banner && <div className="banner" style={{ marginTop: "20px", color: "var(--danger)" }}>{banner}</div>}

      {/* 导出结果面板 */}
      {finished && jobId && (
        <section className="panel" style={{ marginTop: "28px" }}>
          <h3 style={{ margin: "0 0 16px 0", color: "var(--accent)" }}>📥 任务导出与续写</h3>
          <div className="controls" style={{ marginTop: 0 }}>
            <button className="ghost" onClick={() => onExport("merged")} disabled={USE_MOCK}>
              导出合并 Markdown
            </button>
            <button className="ghost" onClick={() => onExport("steps")} disabled={USE_MOCK}>
              导出单步打包
            </button>
            <button className="ghost" onClick={() => onExport("json")} disabled={USE_MOCK}>
              导出 JSON
            </button>
            <button onClick={againRound}>再来一轮接力</button>
          </div>
          {USE_MOCK && <p style={{ fontSize: "12px", color: "var(--muted)", marginTop: "12px" }}>Mock 模式下没有落盘文件，导出按钮已禁用。连接真实后端后可用。</p>}
        </section>
      )}
    </main>
  );
});

DesktopLayout.displayName = "DesktopLayout";
