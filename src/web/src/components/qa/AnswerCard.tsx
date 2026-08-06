"use client";

import { Card, Typography, Space, Tag, Button } from "antd";
import { CheckCircleFilled } from "@ant-design/icons";
import type { Answer } from "@/types";
import { useAuth } from "@/providers/AuthProvider";
import MarkdownRenderer from "./MarkdownRenderer";
import VoteButtons from "./VoteButtons";

const { Text } = Typography;

interface AnswerCardProps {
  answer: Answer;
  userVote?: "up" | "down" | null;
  onVote: (voteType: "up" | "down") => void;
  onAccept?: () => void;
  isQuestionOwner?: boolean;
  showAcceptButton?: boolean;
}

export default function AnswerCard({
  answer,
  userVote,
  onVote,
  onAccept,
  isQuestionOwner = false,
  showAcceptButton = true,
}: AnswerCardProps) {
  const { user } = useAuth();

  return (
    <Card
      id={`answer-${answer.id}`}
      className={`mb-3 ${answer.is_accepted ? "!border-2 !border-success" : ""}`}
      styles={{ body: { padding: "16px 20px" } }}
    >
      <div className="flex gap-4">
        {/* Vote column */}
        <div className="shrink-0 pt-1">
          <VoteButtons
            voteCount={answer.vote_count}
            userVote={userVote}
            onVote={onVote}
          />
        </div>

        {/* Answer content */}
        <div className="flex-1 min-w-0">
          {answer.is_accepted && (
            <Tag color="success" icon={<CheckCircleFilled />} className="mb-2">
              已采纳
            </Tag>
          )}

          <div className="mb-3">
            <MarkdownRenderer html={answer.body_html || answer.body} />
          </div>

          <div className="flex justify-between items-center flex-wrap gap-2">
            <Space>
              {answer.author && (
                <Text type="secondary" className="!text-xs">
                  {answer.author.display_name || answer.author.username}
                  {" · "}
                  {new Date(answer.created_at).toLocaleDateString("zh-CN", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                  {answer.updated_at !== answer.created_at && " (已编辑)"}
                </Text>
              )}
            </Space>

            {showAcceptButton && isQuestionOwner && !answer.is_accepted && onAccept && (
              <Button size="small" type="default" onClick={onAccept}>
                采纳此回答
              </Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
