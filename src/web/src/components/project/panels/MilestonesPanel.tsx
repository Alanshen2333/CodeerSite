"use client";

import { useState, useEffect } from "react";
import { Card, Button, Space, Typography, Progress, Popconfirm } from "antd";
import { message } from "@/lib/message";
import { PlusOutlined, DeleteOutlined, EditOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getMilestones, updateMilestone, deleteMilestone } from "@/lib/api/milestones";
import type { Milestone } from "@/types";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import MilestoneFormModal from "@/components/project/MilestoneFormModal";
import { milestoneStatusLabel, milestonePercent, milestoneProgressText } from "@/styles/constants";

const { Text } = Typography;

interface Props {
  slug: string;
  /** 点里程碑标题回调（打开详情抽屉看挂载 Issue） */
  onOpenMilestone: (milestone: Milestone) => void;
  /** 抽屉内 Issue 变更后递增，触发里程碑计数刷新 */
  refreshTick?: number;
}

/** 里程碑面板 —— 迁自独立页并补全：编辑/重开/详情/描述。 */
export default function MilestonesPanel({ slug, onOpenMilestone, refreshTick }: Props) {
  const { user } = useAuth();
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Milestone | null>(null);

  const fetch = async () => {
    try {
      const r = await getMilestones(slug);
      setMilestones(r.milestones);
    } catch {
      setMilestones([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetch();
  }, [slug, refreshTick]);

  const handleToggleStatus = async (m: Milestone) => {
    try {
      await updateMilestone(slug, m.id, { status: m.status === "closed" ? "open" : "closed" });
      fetch();
    } catch {
      message.error("操作失败");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMilestone(slug, id);
      fetch();
    } catch {
      message.error("删除失败");
    }
  };

  if (loading) return <LoadingState size="large" />;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-base font-semibold text-text m-0">里程碑</h3>
        {user && (
          <Button
            icon={<PlusOutlined />}
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            新建里程碑
          </Button>
        )}
      </div>

      {milestones.length === 0 ? (
        <EmptyState description="暂无里程碑" />
      ) : (
        milestones.map((m) => {
          const percent = milestonePercent(m.open_issues, m.closed_issues);
          return (
            <Card key={m.id} size="small" className="mb-3">
              <div className="flex justify-between items-start gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                  <Space>
                    <button
                      type="button"
                      onClick={() => onOpenMilestone(m)}
                      className="text-left cursor-pointer p-0 border-0 bg-transparent"
                    >
                      <Text strong className="hover:text-primary">{m.title}</Text>
                    </button>
                    {m.status === "closed" ? (
                      <Text type="secondary">({milestoneStatusLabel[m.status]})</Text>
                    ) : m.due_date ? (
                      <Text type="secondary">截止: {m.due_date}</Text>
                    ) : null}
                  </Space>
                  {m.description && (
                    <Text type="secondary" className="block mt-1">
                      {m.description}
                    </Text>
                  )}
                  <Progress
                    percent={percent}
                    size="small"
                    className="mt-2"
                    format={() => milestoneProgressText(m.open_issues, m.closed_issues)}
                  />
                </div>
                {user && (
                  <Space>
                    <Button size="small" onClick={() => handleToggleStatus(m)}>
                      {m.status === "closed" ? "重开" : "关闭"}
                    </Button>
                    <Button
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => {
                        setEditing(m);
                        setFormOpen(true);
                      }}
                    >
                      编辑
                    </Button>
                    <Popconfirm title="删除？" onConfirm={() => handleDelete(m.id)}>
                      <Button size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </Space>
                )}
              </div>
            </Card>
          );
        })
      )}

      <MilestoneFormModal
        slug={slug}
        open={formOpen}
        milestone={editing}
        onClose={() => setFormOpen(false)}
        onSaved={fetch}
      />
    </div>
  );
}
