"use client";

import { Button, Space, theme } from "antd";
import {
  CaretUpOutlined,
  CaretDownOutlined,
} from "@ant-design/icons";

interface VoteButtonsProps {
  voteCount: number;
  userVote?: "up" | "down" | null;
  onVote: (voteType: "up" | "down") => void;
  vertical?: boolean;
  size?: "small" | "default";
}

export default function VoteButtons({
  voteCount,
  userVote,
  onVote,
  vertical = true,
  size = "default",
}: VoteButtonsProps) {
  const { token } = theme.useToken();

  return (
    <Space direction={vertical ? "vertical" : "horizontal"} size={0} align="center">
      <Button
        type="text"
        size={smallSize(size)}
        icon={
          <CaretUpOutlined
            style={{
              fontSize: vertical ? 20 : 16,
              color: userVote === "up" ? token.colorPrimary : token.colorTextSecondary,
            }}
          />
        }
        onClick={() => onVote("up")}
      />
      <span
        style={{
          fontWeight: 600,
          fontSize: vertical ? 18 : 14,
          color:
            userVote === "up"
              ? token.colorPrimary
              : userVote === "down"
                ? token.colorError
                : token.colorText,
          minWidth: 32,
          textAlign: "center",
          lineHeight: 1,
        }}
      >
        {voteCount}
      </span>
      <Button
        type="text"
        size={smallSize(size)}
        icon={
          <CaretDownOutlined
            style={{
              fontSize: vertical ? 20 : 16,
              color:
                userVote === "down" ? token.colorError : token.colorTextSecondary,
            }}
          />
        }
        onClick={() => onVote("down")}
      />
    </Space>
  );
}

function smallSize(size: "small" | "default"): "small" | "middle" {
  return size === "small" ? "small" : "middle";
}
