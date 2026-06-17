"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, Button, Space, Input, DatePicker, Progress, Typography, message, Popconfirm } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getMilestones, createMilestone, updateMilestone, deleteMilestone } from "@/lib/api/milestones";
import type { Milestone } from "@/types";
import Link from "next/link";
import dayjs from "dayjs";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";

const { Text } = Typography;

export default function MilestonesPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState<string | null>(null);

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
  }, [slug]);

  const handleCreate = async () => {
    if (!title.trim()) return;
    try {
      await createMilestone(slug, { title: title.trim(), due_date: dueDate || undefined });
      setTitle("");
      setDueDate(null);
      setShowForm(false);
      fetch();
    } catch {
      message.error("创建失败");
    }
  };

  const handleClose = async (id: string) => {
    try {
      await updateMilestone(slug, id, { status: "closed" });
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
    <PageContainer>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-text m-0">里程碑</h2>
        <Space>
          <Link href={`/projects/${slug}`}>
            <Button>返回项目</Button>
          </Link>
          {user && (
            <Button icon={<PlusOutlined />} onClick={() => setShowForm(true)}>
              新建里程碑
            </Button>
          )}
        </Space>
      </div>

      {showForm && (
        <Card size="small" className="mb-4">
          <Space direction="vertical" className="w-full">
            <Input
              placeholder="里程碑名称"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <DatePicker
              placeholder="截止日期（选填）"
              onChange={(d) => setDueDate(d ? d.format("YYYY-MM-DD") : null)}
              className="w-full"
            />
            <Space>
              <Button type="primary" onClick={handleCreate}>创建</Button>
              <Button onClick={() => setShowForm(false)}>取消</Button>
            </Space>
          </Space>
        </Card>
      )}

      {milestones.length === 0 ? (
        <EmptyState description="暂无里程碑" />
      ) : (
        milestones.map((m) => {
          const total = m.open_issues + m.closed_issues;
          const percent = total > 0 ? Math.round((m.closed_issues / total) * 100) : 0;
          return (
            <Card
              key={m.id}
              size="small"
              className="mb-3"
              title={
                <Space>
                  <Text strong>{m.title}</Text>
                  {m.status === "closed" ? (
                    <Text type="secondary">(已关闭)</Text>
                  ) : m.due_date ? (
                    <Text type="secondary">截止: {m.due_date}</Text>
                  ) : null}
                </Space>
              }
              extra={
                <Space>
                  {m.status === "open" && (
                    <Button size="small" onClick={() => handleClose(m.id)}>
                      关闭
                    </Button>
                  )}
                  <Popconfirm title="删除？" onConfirm={() => handleDelete(m.id)}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </Space>
              }
            >
              {m.description && <Text type="secondary">{m.description}</Text>}
              <Progress
                percent={percent}
                size="small"
                className="mt-2"
                format={() => `${m.closed_issues}/${total} 已关闭`}
              />
            </Card>
          );
        })
      )}
    </PageContainer>
  );
}
