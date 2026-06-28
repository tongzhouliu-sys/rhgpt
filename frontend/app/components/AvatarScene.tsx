"use client";

interface AvatarSceneProps {
  activeProvider?: string;
  stepKey?: string;
}

export default function AvatarScene({ activeProvider, stepKey }: AvatarSceneProps) {
  const providerName = activeProvider || "AI 模型集线器";
  const stepText = stepKey ? `正在执行: ${stepKey}` : "多模型协作沟通中...";

  return (
    <div className="avatar-scene">
      <div className="scene-title">🤖 智能体接力协同对话通道 (AI Avatar Collaboration Stream)</div>
      <div className="stage">
        {/* 小人 1: 提问与任务发起者 */}
        <div className="avatar-box">
          <div className="speech-bubble">任务分发中...</div>
          <div className="avatar-icon">🧑‍💻</div>
          <div className="avatar-label">调度中心</div>
        </div>

        {/* 动态数据流/粒子传输 */}
        <div className="data-stream">
          <div className="packet" />
        </div>

        {/* 小人 2: 当前响应的高级大模型 */}
        <div className="avatar-box">
          <div className="speech-bubble" style={{ background: "#a855f7", color: "#fff" }}>
            {providerName} 思考中...
          </div>
          <div className="avatar-icon">🤖</div>
          <div className="avatar-label" style={{ borderColor: "#a855f7" }}>
            {providerName}
          </div>
        </div>
      </div>
      <div style={{ textAlign: "center", marginTop: "16px", fontFamily: "var(--mono)", fontSize: "12px", color: "var(--muted)" }}>
        ⚡ {stepText}
      </div>
    </div>
  );
}
