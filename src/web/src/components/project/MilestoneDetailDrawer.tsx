"use client";

import { useState, useEffect } from "react";
import { Drawer, Typography, Progress, Space } from "antd";
import { getIssues } from "@/lib/api/issues";
import type { Milestone, Issue } from "@/types";
import IssueCard from "@/components/project/IssueCard";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import { milestoneStatusLabel, milestonePercent, milestoneProgressText } from "@/styles/constants";

const { Text } = Typography;

interface Props {
  slug: string;
  /** 待查看的里程碑；null 表示关闭 */
  milestone: Milestone | null;
  onClose: () => void;
  /** 点击挂载的 Issue 时回调打开 Issue 抽屉 */
  onOpenIssue: (issueNumber: number) => void;
}

/** 里程碑详情抽屉 —— 展示该里程碑下挂载的 Issue 列表（复用 issue 列表 milestone_id 筛选）。 */
export default function MilestoneDetailDrawer({ slug, milestone, onClose, onOpenIssue }: Props) {
  const open = milestone !== null;
  const [issues, setIssues] = useState<Issue[]>([]);
  // 初始 true：避免首次打开在 fetch 前闪现「暂无 Issue」空态。
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!open || !milestone) return;
    setLoading(true);
    getIssues(slug, { milestone_id: milestone.id, per_page: 50 })
      .then((r) => setIssues(r.issues))
      .catch(() => setIssues([]))
      .finally(() => setLoading(false));
  }, [slug, milestone, open]);

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={milestone ? milestone.title : "里程碑"}
      width={640}
      destroyOnHidden
    >
      {milestone && (
        <>
          {milestone.description && (
            <Text type="secondary" className="block mb-4">
              {milestone.description}
            </Text>
          )}
          <Space className="mb-4" wrap>
            {milestone.due_date && (
              <Text type="secondary">截止: {milestone.due_date}</Text>
            )}
            <Text type="secondary">
              {milestoneStatusLabel[milestone.status] ?? milestone.status}
            </Text>
          </Space>
          <Progress
            percent={milestonePercent(milestone.open_issues, milestone.closed_issues)}
            size="small"
            className="mb-4"
            format={() =>
              milestoneProgressText(milestone.open_issues, milestone.closed_issues)
            }
          />

          {loading ? (
            <LoadingState />
          ) : issues.length === 0 ? (
            <EmptyState description="此里程碑下暂无 Issue" />
          ) : (
            issues.map((i) => (
              <IssueCard key={i.id} issue={i} slug={slug} onOpen={onOpenIssue} />
            ))
          )}
        </>
      )}
    </Drawer>
  );
}
