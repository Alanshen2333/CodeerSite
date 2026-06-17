"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, Space, Button, Tag, Select, Input, Typography, message } from "antd";
import {
  ArrowLeftOutlined, DeleteOutlined, UserOutlined, ClockCircleOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getIssue, updateIssue, deleteIssue } from "@/lib/api/issues";
import type { Issue } from "@/types";
import MarkdownRenderer from "@/components/qa/MarkdownRenderer";
import Link from "next/link";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import { priorityColor, priorityLabel, issueStatusLabel } from "@/styles/constants";

const { Text } = Typography;
const { TextArea } = Input;

const statusOptions = Object.entries(issueStatusLabel).map(([value, label]) => ({
  value,
  label,
}));

export default function IssueDetailPage() {
  const { slug, num } = useParams<{ slug: string; num: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [issue, setIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const r = await getIssue(slug, Number(num));
        setIssue(r.issue);
      } catch {
        setIssue(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [slug, num]);

  const handleStatusChange = async (newStatus: string) => {
    if (!issue) return;
    try {
      const r = await updateIssue(slug, issue.issue_number, { status: newStatus });
      setIssue(r.issue);
      message.success("状态已更新");
    } catch {
      message.error("更新失败");
    }
  };

  const handleDelete = async () => {
    if (!issue || !confirm("确定删除此 Issue？")) return;
    try {
      await deleteIssue(slug, issue.issue_number);
      message.success("已删除");
      router.push(`/projects/${slug}/issues`);
    } catch {
      message.error("删除失败");
    }
  };

  const handleSave = async () => {
    if (!issue) return;
    try {
      const r = await updateIssue(slug, issue.issue_number, { title: editTitle, body: editBody });
      setIssue(r.issue);
      setEditing(false);
      message.success("已保存");
    } catch {
      message.error("保存失败");
    }
  };

  if (loading) return <LoadingState size="large" />;
  if (!issue) return <PageContainer><EmptyState description="Issue 不存在" /></PageContainer>;

  return (
    <PageContainer>
      <div className="mb-4">
        <Space>
          <Link href={`/projects/${slug}/issues`}>
            <Button icon={<ArrowLeftOutlined />} size="small">返回</Button>
          </Link>
          <Tag color={priorityColor[issue.priority]}>
            {priorityLabel[issue.priority] || issue.priority}
          </Tag>
        </Space>
      </div>

      {editing ? (
        <Card>
          <Input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            className="mb-3"
            size="large"
          />
          <TextArea
            rows={8}
            value={editBody}
            onChange={(e) => setEditBody(e.target.value)}
            className="mb-3"
          />
          <Space>
            <Button type="primary" onClick={handleSave}>保存</Button>
            <Button onClick={() => setEditing(false)}>取消</Button>
          </Space>
        </Card>
      ) : (
        <>
          <h1 className="text-2xl font-semibold text-text">
            #{issue.issue_number} {issue.title}
          </h1>
          <Space className="mb-4" wrap>
            <Select
              size="small"
              value={issue.status}
              onChange={handleStatusChange}
              options={statusOptions}
              className="w-[100px]"
            />
            <Text type="secondary"><UserOutlined /> {issue.author?.display_name || issue.author?.username}</Text>
            <Text type="secondary"><ClockCircleOutlined /> {new Date(issue.created_at).toLocaleDateString("zh-CN")}</Text>
            {issue.assignee && (
              <Text type="secondary">→ {issue.assignee.display_name || issue.assignee.username}</Text>
            )}
            {user?.id === issue.author_id && (
              <>
                <Button
                  size="small"
                  onClick={() => {
                    setEditTitle(issue.title);
                    setEditBody(issue.body || "");
                    setEditing(true);
                  }}
                >
                  编辑
                </Button>
                <Button size="small" danger icon={<DeleteOutlined />} onClick={handleDelete}>
                  删除
                </Button>
              </>
            )}
          </Space>
          <Card>
            {issue.body_html ? (
              <MarkdownRenderer html={issue.body_html} />
            ) : (
              <Text type="secondary">暂无描述</Text>
            )}
          </Card>
        </>
      )}
    </PageContainer>
  );
}
