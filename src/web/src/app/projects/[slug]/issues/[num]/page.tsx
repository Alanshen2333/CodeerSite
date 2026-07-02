"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, Space, Button, Tag, Select, Input, Typography } from "antd";
import { message } from "@/lib/message";
import {
  ArrowLeftOutlined, DeleteOutlined, UserOutlined, ClockCircleOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getIssue, updateIssue, deleteIssue } from "@/lib/api/issues";
import { getComments, createComment, deleteComment } from "@/lib/api/comments";
import type { Issue, Comment } from "@/types";
import MarkdownRenderer from "@/components/qa/MarkdownRenderer";
import CommentList from "@/components/qa/CommentList";
import CommentForm from "@/components/qa/CommentForm";
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
  const [comments, setComments] = useState<Comment[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const r = await getIssue(slug, Number(num));
        setIssue(r.issue);
        // 加载 issue 评论（多态 target_type=issue）
        const cRes = await getComments({ target_type: "issue", target_id: r.issue.id });
        setComments(cRes.comments);
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

  const handleAddComment = async (body: string) => {
    if (!issue) return;
    try {
      await createComment({ body, target_type: "issue", target_id: issue.id });
      const cRes = await getComments({ target_type: "issue", target_id: issue.id });
      setComments(cRes.comments);
    } catch {
      message.error("评论失败");
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    try {
      await deleteComment(commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
    } catch {
      message.error("删除评论失败");
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

          {/* 评论 */}
          <Card title="评论" className="mt-4">
            <CommentList comments={comments} onDelete={handleDeleteComment} />
            {user ? (
              <CommentForm
                targetType="issue"
                targetId={issue.id}
                onSubmit={handleAddComment}
              />
            ) : (
              <Text type="secondary" className="!text-xs">
                <Link href="/login">登录</Link>后可评论
              </Text>
            )}
          </Card>
        </>
      )}
    </PageContainer>
  );
}
