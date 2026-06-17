import { Empty, Button } from "antd";
import type { ReactNode } from "react";

interface EmptyStateProps {
  description?: string;
  action?: ReactNode;
  className?: string;
}

/** 统一空态 */
export default function EmptyState({
  description = "暂无数据",
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`py-16 text-center ${className}`}>
      <Empty description={description}>
        {action && <div className="mt-4">{action}</div>}
      </Empty>
    </div>
  );
}
