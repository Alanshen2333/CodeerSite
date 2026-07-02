"use client";

import { useState, useEffect } from "react";
import { Drawer, Space, Button, Tag, Select, Input, Typography, Popconfirm } from "antd";
import { message } from "@/lib/message";
import {
  DeleteOutlined,
  UserOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getIssue, updateIssue, deleteIssue } from "@/lib/api/issues";
import { getComments, createComment, deleteComment } from "@/lib/api/comments";
import type { Issue, Comment } from "@/types";
import MarkdownRenderer from "@/components/qa/MarkdownRenderer";
import CommentList from "@/components/qa/CommentList";
import CommentForm from "@/components/qa/CommentForm";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import Link from "next/link";
import { priorityColor, priorityLabel, issueStatusLabel } from "@/styles/constants";

const { Text } = Typography;
const { TextArea } = Input;

const statusOptions = Object.entries(issueStatusLabel).map(([value, label]) => ({
  value,
  label,
}));

interface Props {
  slug: string;
  /** 待打开的 Issue 编号；null 表示关闭 */
  issueNumber: number | null;
  onClose: () => void;
  /** Issue 被编辑或删除时通知父级刷新列表 */
  onChanged?: () => void;
}

/** Issue 详情抽屉 —— 原地查看/编辑/评论，替代独立详情页。 */
export default function IssueDetailDrawer({ slug, issueNumber, onClose, onChanged }: Props) {
  const { user } = useAuth();
  const open = issueNumber !== null;
  const [issue, setIssue] = useState<Issue | null>(null);
  // 初始 true：避免首次打开 / 切换 Issue 时在 fetch 前闪现旧内容或「不存在」空态。
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");
  const [comments, setComments] = useState<Comment[]>([]);

  useEffect(() => {
    if (!open || issueNumber === null) return;
    setLoading(true);
    setEditing(false);
    (async () => {
      try {
        const r = await getIssue(slug, issueNumber);
        setIssue(r.issue);
        const cRes = await getComments({ target_type: "issue", target_id: r.issue.id });
        setComments(cRes.comments);
      } catch {
        setIssue(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [slug, issueNumber, open]);

  const handleStatusChange = async (newStatus: string) => {
    if (!issue) return;
    try {
      const r = await updateIssue(slug, issue.issue_number, { status: newStatus });
      setIssue(r.issue);
      onChanged?.();
      message.success("状态已更新");
    } catch {
      message.error("更新失败");
    }
  };

  const handleDelete = async () => {
    if (!issue) return;
    try {
      await deleteIssue(slug, issue.issue_number);
      message.success("已删除");
      onChanged?.();
      onClose();
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
      onChanged?.();
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

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={issue ? `#${issue.issue_number}` : "Issue 详情"}
      width={640}
      destroyOnHidden
    >
      {loading ? (
        <LoadingState />
      ) : !issue ? (
        <EmptyState description="Issue 不存在" />
      ) : editing ? (
        <Space orientation="vertical" className="w-full">
          <Input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            size="large"
          />
          <TextArea rows={8} value={editBody} onChange={(e) => setEditBody(e.target.value)} />
          <Space>
            <Button type="primary" onClick={handleSave}>保存</Button>
            <Button onClick={() => setEditing(false)}>取消</Button>
          </Space>
        </Space>
      ) : (
        <>
          <Space className="mb-3" wrap>
            <Tag color={priorityColor[issue.priority]}>
              {priorityLabel[issue.priority] || issue.priority}
            </Tag>
            <Select
              size="small"
              value={issue.status}
              onChange={handleStatusChange}
              options={statusOptions}
              className="w-[100px]"
            />
          </Space>

          <h2 className="text-xl font-semibold text-text mb-2">{issue.title}</h2>
          <Space className="mb-4" wrap>
            <Text type="secondary">
              <UserOutlined /> {issue.author?.display_name || issue.author?.username}
            </Text>
            <Text type="secondary">
              <ClockCircleOutlined /> {new Date(issue.created_at).toLocaleDateString("zh-CN")}
            </Text>
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
                <Popconfirm title="删除此 Issue？" onConfirm={handleDelete}>
                  <Button size="small" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              </>
            )}
          </Space>

          <div className="border-t border-border pt-4">
            {issue.body_html ? (
              <MarkdownRenderer html={issue.body_html} />
            ) : (
              <Text type="secondary">暂无描述</Text>
            )}
          </div>

          <div className="border-t border-border mt-6 pt-4">
            <h3 className="text-base font-semibold text-text mb-3">评论</h3>
            <CommentList comments={comments} onDelete={handleDeleteComment} />
            {user ? (
              <div className="mt-3">
                <CommentForm targetType="issue" targetId={issue.id} onSubmit={handleAddComment} />
              </div>
            ) : (
              <Text type="secondary" className="!text-xs">
                <Link href="/login">登录</Link>后可评论
              </Text>
            )}
          </div>
        </>
      )}
    </Drawer>
  );
}
