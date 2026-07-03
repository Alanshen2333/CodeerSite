"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Card, Button, Space, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { getRepo, listBranches, listCommits } from "@/lib/api/repos";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import BranchSelector from "@/components/vcs/BranchSelector";
import CommitList from "@/components/vcs/CommitList";
import ListPagination from "@/components/ui/ListPagination";
import type { Repo, Branch, Commit } from "@/types";

export default function CommitsPage() {
  return (
    <Suspense fallback={<LoadingState size="large" />}>
      <CommitsPageInner />
    </Suspense>
  );
}

function CommitsPageInner() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();

  const refParam = searchParams.get("ref") || "";
  const [ref, setRef] = useState(refParam);

  const [repo, setRepo] = useState<Repo | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const [loadingRepo, setLoadingRepo] = useState(true);
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [loadingCommits, setLoadingCommits] = useState(false);

  useEffect(() => {
    setLoadingRepo(true);
    setLoadingBranches(true);
    Promise.all([getRepo(slug), listBranches(slug)])
      .then(([repoRes, branchRes]) => {
        setRepo(repoRes.repo);
        setBranches(branchRes.branches);
        if (!ref) setRef(repoRes.repo.default_branch);
      })
      .catch(() => {
        setRepo(null);
        setBranches([]);
      })
      .finally(() => {
        setLoadingRepo(false);
        setLoadingBranches(false);
      });
  }, [slug]);

  useEffect(() => {
    if (!repo) return;
    const currentRef = ref || repo.default_branch;
    let cancelled = false;
    setLoadingCommits(true);
    listCommits(slug, { ref: currentRef, page, per_page: 20 })
      .then((r) => {
        if (!cancelled) {
          setCommits(r.commits);
          setHasMore(r.commits.length === 20);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCommits([]);
          setHasMore(false);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingCommits(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug, repo, ref, page]);

  const handleBranchChange = (value: string) => {
    setRef(value);
    setPage(1);
    const params = new URLSearchParams(window.location.search);
    params.set("ref", value);
    params.delete("page");
    router.replace(`/projects/${slug}/repos/commits?${params.toString()}`, { scroll: false });
  };

  if (loadingRepo) return <LoadingState size="large" />;
  if (!repo) {
    return (
      <PageContainer size="wide">
        <EmptyState description="无法加载仓库信息" />
      </PageContainer>
    );
  }

  const currentRef = ref || repo.default_branch;

  return (
    <PageContainer size="wide">
      <Space className="mb-4 flex-wrap">
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.back()}>
          返回
        </Button>
        <BranchSelector
          branches={branches}
          value={currentRef}
          onChange={handleBranchChange}
          loading={loadingBranches}
        />
        <Typography.Text className="text-text-secondary text-sm">
          Commit 历史
        </Typography.Text>
      </Space>

      <Card className="shadow-sm" loading={loadingCommits}>
        <CommitList commits={commits} />
        <div className="mt-4 flex justify-center">
          <ListPagination
            current={page}
            total={(page + (hasMore ? 1 : 0)) * 20}
            pageSize={20}
            onChange={setPage}
          />
        </div>
      </Card>
    </PageContainer>
  );
}
