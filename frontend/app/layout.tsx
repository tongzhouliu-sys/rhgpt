import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RHCLOUD · 接力控制台",
  description: "多模型接力对话流水线 — 实时执行与导出",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
