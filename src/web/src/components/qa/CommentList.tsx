"use client";

import { Typography, Space, Button } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import type { Comment } from "@/types";
import { useAuth } from "@/providers/AuthProvider";

const { Text, Paragraph } = Typography;

interface CommentListProps {
  comments: Comment[];
  onDelete?: (commentId: string) => void;
}

export default function CommentList({ comments, onDelete }: CommentListProps) {
  const { user } = useAuth();

  if (!comments.length) return null;

  return (
    <div className="py-2">
      {comments.map((comment) => (
        <div key={comment.id} className="py-2 border-b border-border-secondary">
          <Paragraph className="!mb-1 !text-xs !leading-relaxed">
            {comment.body}
          </Paragraph>
          <Space size={8}>
            <Text type="secondary" className="!text-xs">
              {comment.user?.display_name || comment.user?.username || "匿名"}
            </Text>
            <Text type="secondary" className="!text-xs">
              {new Date(comment.created_at).toLocaleDateString("zh-CN", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </Text>
            {(user?.id === comment.user_id || user?.role === "admin") && onDelete && (
              <Button
                type="text"
                danger
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => onDelete(comment.id)}
              />
            )}
          </Space>
        </div>
      ))}
    </div>
  );
}
