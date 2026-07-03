"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Card, Breadcrumb, Button, Space, Typography } from "antd";
import { HomeOutlined, ArrowLeftOutlined } from "@ant-design/icons";
import { getRepo, getBlob } from "@/lib/api/repos";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import BlobViewer from "@/components/vcs/BlobViewer";
import type { Repo, Blob } from "@/types";

export default function BlobPage() {
  return (
    <Suspense fallback={<LoadingState size="large" />}>
      <BlobPageInner />
    </Suspense>
  );
}

function BlobPageInner() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();

  const path = searchParams.get("path") || "";
  const ref = searchParams.get("ref") || "";

  const [repo, setRepo] = useState<Repo | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [loadingRepo, setLoadingRepo] = useState(true);
  const [loadingBlob, setLoadingBlob] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    getRepo(slug)
      .then((r) => setRepo(r.repo))
      .catch(() => setRepo(null))
      .finally(() => setLoadingRepo(false));
  }, [slug]);

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    setLoadingBlob(true);
    setError(false);
    getBlob(slug, { path, ref: ref || undefined })
      .then((r) => {
        if (!cancelled) setBlob(r.blob);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoadingBlob(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug, path, ref]);

  if (loadingRepo) return <LoadingState size="large" />;
  if (!repo) {
    return (
      <PageContainer size="wide">
        <EmptyState description="无法加载仓库信息" />
      </PageContainer>
    );
  }

  const currentRef = ref || repo.default_branch;
  const pathParts = path.split("/").filter(Boolean);
  const dirPath = pathParts.slice(0, -1).join("/");

  return (
    <PageContainer size="wide">
      <Space className="mb-4">
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.back()}>
          返回
        </Button>
        <Typography.Text className="text-text-secondary text-sm">
          分支：{currentRef}
        </Typography.Text>
      </Space>

      <Card className="mb-4 shadow-sm">
        <Breadcrumb
          items={[
            {
              title: (
                <a
                  href={`/projects/${slug}/repos?ref=${encodeURIComponent(currentRef)}`}
                  className="text-text-secondary hover:text-text"
                >
                  <HomeOutlined />
                </a>
              ),
            },
            ...pathParts.map((part, idx) => {
              const isLast = idx === pathParts.length - 1;
              const p = pathParts.slice(0, idx + 1).join("/");
              return {
                title: isLast ? (
                  <span className="text-text">{part}</span>
                ) : (
                  <a
                    href={`/projects/${slug}/repos?ref=${encodeURIComponent(
                      currentRef,
                    )}&path=${encodeURIComponent(p)}`}
                    className="text-text-secondary hover:text-text"
                  >
                    {part}
                  </a>
                ),
              };
            }),
          ]}
        />
      </Card>

      {error ? (
        <EmptyState description="文件加载失败" />
      ) : loadingBlob ? (
        <LoadingState />
      ) : blob ? (
        <BlobViewer blob={blob} />
      ) : (
        <EmptyState description="文件不存在" />
      )}
    </PageContainer>
  );
}
