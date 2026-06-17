"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { Input, Select, Tag, Card, Space } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { useRouter, useSearchParams } from "next/navigation";
import { search } from "@/lib/api/search";
import type { SearchResultItem } from "@/types";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import ListPagination from "@/components/ui/ListPagination";

const TYPE_LABELS: Record<string, string> = {
  question: "问题",
  answer: "回答",
  issue: "Issue",
  project: "项目",
};

const TYPE_COLORS: Record<string, string> = {
  question: "blue",
  answer: "green",
  issue: "orange",
  project: "purple",
};

function getLink(item: SearchResultItem): string {
  const extra = item.extra as Record<string, unknown> | undefined;
  switch (item.source_type) {
    case "question":
      return `/questions/${item.doc_id}`;
    case "answer":
      return `/questions/${extra?.question_id || ""}`;
    case "issue":
      return `/projects/${extra?.project_slug || ""}/issues/${extra?.issue_number || ""}`;
    case "project":
      return `/projects/${extra?.slug || ""}`;
    default:
      return "#";
  }
}

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [searchType, setSearchType] = useState<string>(searchParams.get("type") || "");
  const [items, setItems] = useState<SearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(!!initialQuery);

  const doSearch = useCallback(async (q: string, p: number) => {
    if (!q.trim()) return;
    setLoading(true);
    setHasSearched(true);
    try {
      const result = await search({ q, type: searchType || undefined, page: p, per_page: perPage });
      setItems(result.items);
      setTotal(result.total);
    } catch {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [searchType, perPage]);

  useEffect(() => {
    if (initialQuery) {
      doSearch(initialQuery, page);
    }
  }, []);

  const handleSearch = () => {
    setPage(1);
    const params = new URLSearchParams();
    params.set("q", query);
    if (searchType) params.set("type", searchType);
    router.replace(`/search?${params.toString()}`);
    doSearch(query, 1);
  };

  const handlePageChange = (p: number) => {
    setPage(p);
    doSearch(query, p);
  };

  return (
    <PageContainer size="wide">
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-text mb-4">全局搜索</h2>
        <Space.Compact className="w-full">
          <Input
            size="large"
            placeholder="搜索问题、回答、Issue、项目..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onPressEnter={handleSearch}
            prefix={<SearchOutlined />}
          />
          <Select
            size="large"
            value={searchType}
            onChange={setSearchType}
            className="w-28"
          >
            <Select.Option value="">全部</Select.Option>
            <Select.Option value="question">问题</Select.Option>
            <Select.Option value="answer">回答</Select.Option>
            <Select.Option value="issue">Issue</Select.Option>
            <Select.Option value="project">项目</Select.Option>
          </Select>
        </Space.Compact>
      </div>

      {!hasSearched ? (
        <EmptyState description="输入关键词搜索" />
      ) : loading ? (
        <LoadingState />
      ) : items.length === 0 ? (
        <EmptyState description="未找到结果" />
      ) : (
        <>
          <div className="text-text-secondary mb-4 text-sm">
            找到 {total} 条结果
          </div>
          <div className="flex flex-col gap-3">
            {items.map((item) => (
              <Card
                key={`${item.source_type}-${item.doc_id}`}
                hoverable
                className="cursor-pointer border-border"
                onClick={() => router.push(getLink(item))}
              >
                <div className="flex items-start gap-3">
                  <Tag color={TYPE_COLORS[item.source_type] || "default"}>
                    {TYPE_LABELS[item.source_type] || item.source_type}
                  </Tag>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-base font-medium text-text m-0 mb-1 truncate">
                      {item.title}
                    </h4>
                    <p className="text-text-secondary text-sm m-0 line-clamp-2">
                      {item.body_text || item.title}
                    </p>
                    {item.tags && item.tags.length > 0 && (
                      <div className="mt-2 flex gap-1">
                        {item.tags.map((t) => (
                          <Tag key={t}>{t}</Tag>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
          <ListPagination
            current={page}
            total={total}
            pageSize={perPage}
            onChange={handlePageChange}
          />
        </>
      )}
    </PageContainer>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <SearchContent />
    </Suspense>
  );
}
