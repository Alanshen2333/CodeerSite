"use client";

import { Card, List, Typography, Avatar } from "antd";
import { UserOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import type { Commit } from "@/types";

dayjs.extend(relativeTime);

interface CommitListProps {
  commits: Commit[];
}

export default function CommitList({ commits }: CommitListProps) {
  return (
    <List
      dataSource={commits}
      renderItem={(commit) => (
        <List.Item className="px-0">
          <Card className="w-full shadow-sm">
            <div className="flex items-start gap-3">
              <Avatar size="small" icon={<UserOutlined />} className="bg-primary text-white shrink-0" />
              <div className="min-w-0 flex-1">
                <Typography.Text className="block truncate text-text font-medium">
                  {commit.message}
                </Typography.Text>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-text-secondary">
                  <span>{commit.author_name || "Unknown"}</span>
                  {commit.date && (
                    <span title={dayjs(commit.date).format("YYYY-MM-DD HH:mm:ss")}>
                      {dayjs(commit.date).fromNow()}
                    </span>
                  )}
                </div>
              </div>
              <Typography.Text
                copyable={{
                  text: commit.sha,
                  tooltips: ["复制 SHA", "已复制"],
                }}
                className="font-mono text-xs text-text-tertiary shrink-0"
              >
                {commit.sha?.slice(0, 7)}
              </Typography.Text>
            </div>
          </Card>
        </List.Item>
      )}
    />
  );
}
