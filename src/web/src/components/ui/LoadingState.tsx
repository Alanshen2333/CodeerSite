import { Spin } from "antd";
import { LoadingOutlined } from "@ant-design/icons";

interface LoadingStateProps {
  /** 控制 Spin 和容器大小 */
  size?: "small" | "default" | "large";
  tip?: string;
}

const sizeMap = {
  small: { spinSize: "small" as const, padding: "py-8" },
  default: { spinSize: "medium" as const, padding: "py-12" },
  large: { spinSize: "large" as const, padding: "py-20" },
};

/** 统一加载态 */
export default function LoadingState({ size = "default", tip }: LoadingStateProps) {
  const { spinSize, padding } = sizeMap[size];

  return (
    <div className={`text-center ${padding}`}>
      <Spin
        size={spinSize}
        indicator={<LoadingOutlined spin />}
        tip={tip}
      >
        {/* Spin 需要 children 才能渲染 tip */}
        {tip ? <div className="mt-4" /> : null}
      </Spin>
    </div>
  );
}
