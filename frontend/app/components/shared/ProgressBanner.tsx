"use client";

import React from "react";

const STEP_LABELS: Record<string, string> = {
  generate: "1/5 初稿生成",
  review: "2/5 交叉评审",
  deep_analyze: "3/5 逻辑拆解",
  improve: "4/5 方案优化",
  summary: "5/5 总结收尾",
};

interface ProgressBannerProps {
  running: boolean;
  finished: boolean;
  phase: string;
  orderLength: number;
  currentRunningKey?: string;
}

export const ProgressBanner: React.FC<ProgressBannerProps> = React.memo(
  ({ running, finished, phase, orderLength, currentRunningKey }) => {
    const statusDot = running ? "run" : phase === "done" ? "ok" : phase === "error" ? "err" : "";

    return (
      <div className="progress-banner-card">
        <div className="progress-banner-header">
          <div className="progress-banner-title">
            <span className={`dot ${statusDot}`} />
            <strong style={{ fontSize: "15px" }}>
              {running
                ? `⏳ AI 接力协同中 · 当前第 ${Math.min(orderLength, 5)} / 5 步`
                : finished
                ? "🎉 所有 5 轮多模型协同接力已完美完成"
                : "⚠️ 任务中断或出错"}
            </strong>
          </div>
          {running && (
            <span className="progress-banner-step-tag">
              {currentRunningKey
                ? `👉 正在进行: ${STEP_LABELS[currentRunningKey] || currentRunningKey}`
                : "🔄 阶段交接与竞速锁定中..."}
            </span>
          )}
        </div>

        <div className="progress-track">
          <div
            className="progress-fill"
            style={{
              width: `${finished ? 100 : Math.min(100, Math.max(12, (orderLength / 5) * 100))}%`,
            }}
          />
        </div>

        {running && (
          <div className="progress-tips-row">
            <span>💡 ⚡ 全步骤并发竞速中：选中的模型在每一轮均同时赛马，谁最快首 Token 吐字谁锁定获胜，并实时秒级刷屏！</span>
          </div>
        )}
      </div>
    );
  }
);

ProgressBanner.displayName = "ProgressBanner";
