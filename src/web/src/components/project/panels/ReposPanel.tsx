"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, Button, Space, Typography } from "antd";
import {
  CodeOutlined,
  PlusOutlined,
  BranchesOutlined,
  HistoryOutlined,
} from "@ant-design/icons";
import { getRepo } from "@/lib/api/repos";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import type { Repo } from "@/types";

interface ReposPanelProps {
  slug: string;
  hasRepo: boolean;
  isOwner: boolean;
}

export default function ReposPanel({ slug, hasRepo, isOwner }: ReposPanelProps) {
  const router = useRouter();
  const [repo, setRepo] = useState<Repo | null>(null);
  const [loading, setLoading] = useState(hasRepo);

  useEffect(() => {
    if (!hasRepo) return;
    getRepo(slug)
      .then((r) => setRepo(r.repo))
      .catch(() => setRepo(null))
      .finally(() => setLoading(false));
  }, [slug, hasRepo]);

  if (!hasRepo) {
    return (
      <EmptyState
        description="该项目尚未关联代码仓库"
        action={
          isOwner ? (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => router.push(`/projects/${slug}/settings`)}
            >
              前往设置关联仓库
            </Button>
          ) : null
        }
      />
    );
  }

  if (loading) return <LoadingState />;

  return (
    <Card className="shadow-sm">
      {repo ? (
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <Typography.Title level={5} className="m-0 text-text">
              {repo.full_name}
            </Typography.Title>
            <Typography.Text className="text-text-secondary">
              默认分支：{repo.default_branch} · {repo.private ? "私有" : "公开"}
            </Typography.Text>
          </div>
          <Space wrap>
            <Button
              type="primary"
              icon={<CodeOutlined />}
              onClick={() => router.push(`/projects/${slug}/repos`)}
            >
              浏览代码
            </Button>
            <Button
              icon={<HistoryOutlined />}
              onClick={() => router.push(`/projects/${slug}/repos/commits`)}
            >
              Commits
            </Button>
          </Space>
        </div>
      ) : (
        <EmptyState description="仓库信息加载失败" />
      )}
    </Card>
  );
}
