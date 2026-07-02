"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Card,
  Space,
  Button,
  Input,
  Tag,
  Divider,
  Pagination,
} from "antd";
import { message } from "@/lib/message";
import {
  LockOutlined,
  PushpinOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getQuestion, deleteQuestion, closeQuestion, reopenQuestion, togglePinQuestion } from "@/lib/api/questions";
import { getAnswers, createAnswer, acceptAnswer, deleteAnswer, unacceptAnswer } from "@/lib/api/answers";
import { vote, removeVote } from "@/lib/api/votes";
import { getComments, createComment, deleteComment } from "@/lib/api/comments";
import type { Question, Answer, Comment } from "@/types";
import VoteButtons from "@/components/qa/VoteButtons";
import MarkdownRenderer from "@/components/qa/MarkdownRenderer";
import TagBadge from "@/components/qa/TagBadge";
import AnswerCard from "@/components/qa/AnswerCard";
import CommentList from "@/components/qa/CommentList";
import CommentForm from "@/components/qa/CommentForm";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";

const { TextArea } = Input;

export default function QuestionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();

  const [question, setQuestion] = useState<Question | null>(null);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [answerBody, setAnswerBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [answerPage, setAnswerPage] = useState(1);
  const [answerTotal, setAnswerTotal] = useState(0);

  const isOwner = user?.id === question?.author_id;
  const isMod = user?.role === "admin" || user?.role === "moderator";

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [qRes, aRes, cRes] = await Promise.all([
        getQuestion(id),
        getAnswers({ question_id: id, page: answerPage }),
        getComments({ target_type: "question", target_id: id }),
      ]);
      setQuestion(qRes.question);
      setAnswers(aRes.answers);
      setAnswerTotal(aRes.total);
      setComments(cRes.comments);
    } catch {
      message.error("加载问题失败");
    } finally {
      setLoading(false);
    }
  }, [id, answerPage]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleVote = async (voteType: "up" | "down", targetType: "question" | "answer", targetId: string) => {
    if (!user) {
      router.push("/login");
      return;
    }
    try {
      await vote({ vote_type: voteType, target_type: targetType, target_id: targetId });
      fetchData();
    } catch {
      // ignore
    }
  };

  const handleSubmitAnswer = async () => {
    if (!answerBody.trim() || !user) return;
    setSubmitting(true);
    try {
      await createAnswer({ question_id: id, body: answerBody.trim() });
      setAnswerBody("");
      message.success("回答已发布！");
      fetchData();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "发布失败"
          : "发布失败";
      message.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAccept = async (answerId: string) => {
    try {
      await acceptAnswer(answerId);
      message.success("已采纳此回答");
      fetchData();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "操作失败"
          : "操作失败";
      message.error(msg);
    }
  };

  const handleDeleteQuestion = async () => {
    if (!confirm("确定要删除这个问题吗？")) return;
    try {
      await deleteQuestion(id);
      message.success("问题已删除");
      router.push("/questions");
    } catch {
      message.error("删除失败");
    }
  };

  const handleCloseToggle = async () => {
    if (!question) return;
    try {
      if (question.is_closed) {
        await reopenQuestion(id);
      } else {
        await closeQuestion(id);
      }
      fetchData();
    } catch {
      message.error("操作失败");
    }
  };

  const handlePinToggle = async () => {
    try {
      await togglePinQuestion(id);
      fetchData();
    } catch {
      message.error("操作失败");
    }
  };

  const handleAddComment = async (body: string) => {
    try {
      await createComment({
        body,
        target_type: "question",
        target_id: id,
      });
      const cRes = await getComments({ target_type: "question", target_id: id });
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

  if (loading) {
    return <LoadingState size="large" />;
  }

  if (!question) {
    return (
      <PageContainer>
        <EmptyState description="问题不存在" />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* Question header */}
      <div className="flex gap-4 mb-4">
        <div className="shrink-0 pt-1">
          <VoteButtons
            voteCount={question.vote_count}
            onVote={(vt) => handleVote(vt, "question", question.id)}
          />
        </div>
        <div className="flex-1 min-w-0">
          <Space size={8} className="mb-2" wrap>
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
          </Space>
          <h1 className="text-2xl font-semibold text-text mt-0 mb-3">
            {question.title}
          </h1>
          <Space wrap className="mb-3">
            {question.tags?.map((tag) => (
              <TagBadge key={tag.id} tag={tag} />
            ))}
          </Space>
          <div className="mb-4">
            <MarkdownRenderer html={question.body_html || question.body} />
          </div>
          <div className="flex justify-between flex-wrap gap-2 mb-0">
            <div>
              {question.author && (
                <span className="text-xs text-text-tertiary">
                  {question.author.display_name || question.author.username}
                  {" · "}
                  {new Date(question.created_at).toLocaleDateString("zh-CN", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                  {" · "}
                  {question.view_count} 次浏览
                </span>
              )}
            </div>
            <Space>
              {isMod && (
                <Button size="small" onClick={handlePinToggle}>
                  {question.is_pinned ? "取消置顶" : "置顶"}
                </Button>
              )}
              {(isOwner || isMod) && (
                <Button size="small" onClick={handleCloseToggle}>
                  {question.is_closed ? "重新打开" : "关闭问题"}
                </Button>
              )}
              {(isOwner || isMod) && (
                <Button
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={handleDeleteQuestion}
                >
                  删除
                </Button>
              )}
            </Space>
          </div>

          {/* Question comments */}
          <div className="mt-3 pt-3 border-t border-border-secondary">
            <CommentList comments={comments} onDelete={handleDeleteComment} />
            {user && (
              <CommentForm
                targetType="question"
                targetId={question.id}
                onSubmit={handleAddComment}
              />
            )}
          </div>
        </div>
      </div>

      <Divider />

      {/* Answers */}
      <h2 className="text-lg font-semibold text-text mb-4">
        {answerTotal} 个回答
      </h2>

      {answers.map((answer) => (
        <AnswerCard
          key={answer.id}
          answer={answer}
          onVote={(vt) => handleVote(vt, "answer", answer.id)}
          onAccept={() => handleAccept(answer.id)}
          isQuestionOwner={isOwner}
          showAcceptButton={!question.is_closed}
        />
      ))}

      {answerTotal > 20 && (
        <div className="text-center my-4">
          <Pagination
            current={answerPage}
            total={answerTotal}
            pageSize={20}
            onChange={(p) => setAnswerPage(p)}
            showSizeChanger={false}
            simple
          />
        </div>
      )}

      {/* Answer form */}
      {user && !question.is_closed && (
        <Card title="撰写你的回答" className="mt-6">
          <TextArea
            rows={6}
            value={answerBody}
            onChange={(e) => setAnswerBody(e.target.value)}
            placeholder="写下你的回答...（支持 Markdown）"
          />
          <Button
            type="primary"
            loading={submitting}
            onClick={handleSubmitAnswer}
            disabled={!answerBody.trim()}
            className="mt-3"
          >
            提交回答
          </Button>
        </Card>
      )}

      {!user && (
        <Card className="mt-6 text-center">
          <Button type="primary" onClick={() => router.push("/login")}>
            登录后回答
          </Button>
        </Card>
      )}
    </PageContainer>
  );
}
