"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { message } from "antd";
import { getTag } from "@/lib/api/tags";
import { getQuestions } from "@/lib/api/questions";
import { vote } from "@/lib/api/votes";
import { useAuth } from "@/providers/AuthProvider";
import { useRouter } from "next/navigation";
import type { Question, Tag } from "@/types";
import QuestionCard from "@/components/qa/QuestionCard";
import TagBadge from "@/components/qa/TagBadge";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import ListPagination from "@/components/ui/ListPagination";

export default function TagDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const router = useRouter();

  const [tag, setTag] = useState<Tag | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchQuestions = useCallback(async () => {
    try {
      const result = await getQuestions({ tag: slug, page, per_page: 20 });
      setQuestions(result.questions);
      setTotal(result.total);
    } catch {
      setQuestions([]);
    }
  }, [slug, page]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const tRes = await getTag(slug);
        setTag(tRes.tag);
        await fetchQuestions();
      } catch {
        message.error("标签不存在");
      } finally {
        setLoading(false);
      }
    })();
  }, [slug, fetchQuestions]);

  const handleVote = async (question: Question, voteType: "up" | "down") => {
    if (!user) {
      router.push("/login");
      return;
    }
    try {
      await vote({ vote_type: voteType, target_type: "question", target_id: question.id });
      fetchQuestions();
    } catch {
      // ignore
    }
  };

  if (loading) {
    return <LoadingState size="large" />;
  }

  if (!tag) {
    return (
      <PageContainer size="wide">
        <EmptyState description="标签不存在" />
      </PageContainer>
    );
  }

  return (
    <PageContainer size="wide">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-text mb-2">
          <TagBadge tag={tag} clickable={false} className="mr-2" />
          标签：{tag.name}
        </h2>
        {tag.description && (
          <p className="text-text-secondary text-sm mb-1">{tag.description}</p>
        )}
        <p className="text-text-tertiary text-xs">{tag.usage_count} 个问题</p>
      </div>

      {questions.length === 0 ? (
        <EmptyState description="该标签下暂无问题" />
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
            pageSize={20}
            onChange={(p) => setPage(p)}
          />
        </>
      )}
    </PageContainer>
  );
}
