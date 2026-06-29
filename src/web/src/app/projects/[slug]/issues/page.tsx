"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Space, Button, Select } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getIssues } from "@/lib/api/issues";
import { searchTags } from "@/lib/api/tags";
import type { Issue, Tag } from "@/types";
import IssueCard from "@/components/project/IssueCard";
import TagBadge from "@/components/qa/TagBadge";
import Link from "next/link";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import ListPagination from "@/components/ui/ListPagination";
import { issueStatusLabel, priorityLabel } from "@/styles/constants";

export default function IssueListPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string | undefined>();
  const [priority, setPriority] = useState<string | undefined>();
  const [tagId, setTagId] = useState<string | undefined>();
  const [tagOptions, setTagOptions] = useState<Tag[]>([]);
  const [tagSearching, setTagSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const r = await getIssues(slug, { page, per_page: 20, status, priority, tag_id: tagId });
      setIssues(r.issues);
      setTotal(r.total);
    } catch {
      setIssues([]);
    } finally {
      setLoading(false);
    }
  }, [slug, page, status, priority, tagId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  const handleSearchTag = async (q: string) => {
    if (!q || q.length < 1) {
      setTagOptions([]);
      return;
    }
    setTagSearching(true);
    try {
      setTagOptions(await searchTags(q));
    } catch {
      setTagOptions([]);
    } finally {
      setTagSearching(false);
    }
  };

  return (
    <PageContainer size="wide">
      <div className="flex justify-between items-center flex-wrap gap-3 mb-4">
        <h2 className="text-xl font-semibold text-text m-0">Issues</h2>
        <Space wrap>
          <Select
            placeholder="状态"
            allowClear
            className="w-[100px]"
            value={status}
            onChange={(v) => {
              setStatus(v);
              setPage(1);
            }}
            options={Object.entries(issueStatusLabel).map(([value, label]) => ({
              value,
              label,
            }))}
          />
          <Select
            placeholder="优先级"
            allowClear
            className="w-[100px]"
            value={priority}
            onChange={(v) => {
              setPriority(v);
              setPage(1);
            }}
            options={Object.entries(priorityLabel).map(([value, label]) => ({
              value,
              label,
            }))}
          />
          <Select
            placeholder="标签"
            allowClear
            showSearch
            className="w-[160px]"
            value={tagId}
            onChange={(v) => {
              setTagId(v);
              setPage(1);
            }}
            onSearch={handleSearchTag}
            loading={tagSearching}
            filterOption={false}
            notFoundContent={null}
            options={tagOptions.map((t) => ({
              value: t.id,
              label: <TagBadge tag={t} clickable={false} />,
            }))}
          />
          {user && (
            <Link href={`/projects/${slug}/issues/new`}>
              <Button type="primary" icon={<PlusOutlined />}>
                新建 Issue
              </Button>
            </Link>
          )}
        </Space>
      </div>

      {loading ? (
        <LoadingState />
      ) : issues.length === 0 ? (
        <EmptyState
          description="暂无 Issue"
          action={
            user ? (
              <Link href={`/projects/${slug}/issues/new`}>
                <Button type="primary">创建第一个 Issue</Button>
              </Link>
            ) : undefined
          }
        />
      ) : (
        <>
          {issues.map((i) => (
            <IssueCard key={i.id} issue={i} slug={slug} />
          ))}
          <ListPagination
            current={page}
            total={total}
            pageSize={20}
            onChange={setPage}
          />
        </>
      )}
    </PageContainer>
  );
}
