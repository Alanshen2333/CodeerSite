import type { ReactNode } from "react";
import { layout } from "@/styles/tokens";

interface PageContainerProps {
  children: ReactNode;
  /** wide=960px, default=800px, narrow=640px */
  size?: "wide" | "default" | "narrow";
  className?: string;
}

/** 页面容器 — 统一 max-width + 水平居中 + 响应式安全边距 */
export default function PageContainer({
  children,
  size = "default",
  className = "",
}: PageContainerProps) {
  const maxWidth =
    size === "wide"
      ? layout.contentWide
      : size === "narrow"
        ? layout.contentNarrow
        : layout.contentDefault;

  return (
    <div
      className={`mx-auto px-4 sm:px-6 lg:px-8 py-6 ${className}`}
      style={{ maxWidth }}
    >
      {children}
    </div>
  );
}
