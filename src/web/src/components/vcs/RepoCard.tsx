"use client";

import { Card, Space, Typography, Button } from "antd";
import { BranchesOutlined, CodeOutlined, HistoryOutlined } from "@ant-design/icons";
import type { Repo } from "@/types";

interface RepoCardProps {
  repo: Repo;
  activeTab: "tree" | "commits";
  onTabChange: (tab: "tree" | "commits") => void;
}

export default function RepoCard({ repo, activeTab, onTabChange }: RepoCardProps) {
  return (
    <Card className="shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <Typography.Title level={5} className="m-0 text-text">
            {repo.full_name}
          </Typography.Title>
          {repo.description && (
            <Typography.Text className="mt-1 block text-text-secondary">
              {repo.description}
            </Typography.Text>
          )}
          <Space className="mt-2 text-xs text-text-tertiary">
            <span>默认分支：{repo.default_branch}</span>
            <span>·</span>
            <span>{repo.private ? "私有" : "公开"}</span>
          </Space>
        </div>

        <Space wrap className="shrink-0">
          <Button
            type={activeTab === "tree" ? "primary" : "default"}
            icon={<CodeOutlined />}
            onClick={() => onTabChange("tree")}
          >
            文件
          </Button>
          <Button
            type={activeTab === "commits" ? "primary" : "default"}
            icon={<HistoryOutlined />}
            onClick={() => onTabChange("commits")}
          >
            Commits
          </Button>
        </Space>
      </div>
    </Card>
  );
}
