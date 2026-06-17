"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { Radio, Space, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { getQuestions } from "@/lib/api/questions";
import { vote, removeVote } from "@/lib/api/votes";
import { useAuth } from "@/providers/AuthProvider";
import type { Question } from "@/types";
import QuestionCard from "@/components/qa/QuestionCard";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import ListPagination from "@/components/ui/ListPagination";

function QuestionsContent() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
  const [perPage] = useState(20);
  const [sort, setSort] = useState(searchParams.get("sort") || "newest");
  const [loading, setLoading] = useState(true);

  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getQuestions({
        page,
        per_page: perPage,
        sort,
        tag: searchParams.get("tag") || undefined,
      });
      setQuestions(result.questions);
      setTotal(result.total);
    } catch {
      setQuestions([]);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, sort, searchParams]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  const handleVote = async (question: Question, voteType: "up" | "down") => {
    if (!user) {
      router.push("/login");
      return;
    }
    try {
      await vote({
        vote_type: voteType,
        target_type: "question",
        target_id: question.id,
      });
      setQuestions((prev) =>
        prev.map((q) => {
          if (q.id !== question.id) return q;
          const delta = voteType === "up" ? 1 : -1;
          return { ...q, vote_count: q.vote_count + delta };
        })
      );
    } catch {
      fetchQuestions();
    }
  };

  return (
    <PageContainer size="wide">
      <div className="flex justify-between items-center flex-wrap gap-3 mb-6">
        <h2 className="text-xl font-semibold text-text m-0">所有问题</h2>
        <Space wrap>
          <Radio.Group
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setPage(1);
            }}
            optionType="button"
            buttonStyle="solid"
            size="small"
          >
            <Radio.Button value="newest">最新</Radio.Button>
            <Radio.Button value="popular">热门</Radio.Button>
            <Radio.Button value="unanswered">未回答</Radio.Button>
          </Radio.Group>
          {user && (
            <Link href="/questions/ask">
              <Button type="primary" icon={<PlusOutlined />}>
                提问
              </Button>
            </Link>
          )}
        </Space>
      </div>

      {loading ? (
        <LoadingState />
      ) : questions.length === 0 ? (
        <EmptyState
          description="暂无问题"
          action={
            user ? (
              <Link href="/questions/ask">
                <Button type="primary">提出第一个问题</Button>
              </Link>
            ) : undefined
          }
        />
      ) : (
        <>
          {questions.map((q) => (
            <QuestionCard
              key={q.id}
              question={q}
              onVote={(vt) => handleVote(q, vt)}
            />
          ))}
          <ListPagination
            current={page}
            total={total}
            pageSize={perPage}
            onChange={(p) => setPage(p)}
          />
        </>
      )}
    </PageContainer>
  );
}

export default function QuestionsPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <QuestionsContent />
    </Suspense>
  );
}
