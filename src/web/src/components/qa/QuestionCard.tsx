"use client";

import { Card, Typography, Space, Tag } from "antd";
import {
  MessageOutlined,
  EyeOutlined,
  PushpinOutlined,
  LockOutlined,
} from "@ant-design/icons";
import Link from "next/link";
import type { Question } from "@/types";
import TagBadge from "./TagBadge";
import VoteButtons from "./VoteButtons";

const { Text } = Typography;

interface QuestionCardProps {
  question: Question;
  userVote?: "up" | "down" | null;
  onVote?: (voteType: "up" | "down") => void;
}

export default function QuestionCard({ question, userVote, onVote }: QuestionCardProps) {
  return (
    <Card
      hoverable
      className="mb-3"
      styles={{ body: { padding: "16px 20px" } }}
    >
      <div className="flex gap-4">
        {/* Vote column */}
        <div className="shrink-0 pt-1">
          <VoteButtons
            voteCount={question.vote_count}
            userVote={userVote}
            onVote={onVote || (() => {})}
          />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 mb-1">
            {question.is_pinned && (
              <Tag color="orange" icon={<PushpinOutlined />}>
                置顶
              </Tag>
            )}
            {question.is_closed && (
              <Tag color="default" icon={<LockOutlined />}>
                已关闭
              </Tag>
            )}
            <Link
              href={`/questions/${question.id}`}
              className="text-base font-semibold text-text no-underline leading-snug flex-1"
            >
              {question.title}
            </Link>
          </div>

          <div className="mb-2">
            {question.tags?.map((tag) => (
              <TagBadge key={tag.id} tag={tag} className="mr-1" />
            ))}
          </div>

          <Space size={16}>
            <Space size={4}>
              <MessageOutlined className="!text-text-tertiary" />
              <Text type="secondary">{question.answer_count} 回答</Text>
            </Space>
            <Space size={4}>
              <EyeOutlined className="!text-text-tertiary" />
              <Text type="secondary">{question.view_count} 浏览</Text>
            </Space>
            {question.author && (
              <Text type="secondary">
                {question.author.display_name || question.author.username} ·{" "}
                {new Date(question.created_at).toLocaleDateString("zh-CN")}
              </Text>
            )}
          </Space>
        </div>
      </div>
    </Card>
  );
}
