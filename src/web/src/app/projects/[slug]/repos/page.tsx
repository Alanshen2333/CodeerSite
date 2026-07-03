"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Card, Breadcrumb, Button, Space, Typography } from "antd";
import { HomeOutlined, SettingOutlined, PlusOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getRepo, listBranches, getTree, listCommits } from "@/lib/api/repos";
import { getProject } from "@/lib/api/projects";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import RepoCard from "@/components/vcs/RepoCard";
import BranchSelector from "@/components/vcs/BranchSelector";
import FileTree from "@/components/vcs/FileTree";
import CommitList from "@/components/vcs/CommitList";
import ListPagination from "@/components/ui/ListPagination";
import type { Repo, Branch, TreeEntry, Commit, Project } from "@/types";

type TabKey = "tree" | "commits";

export default function RepoPage() {
  return (
    <Suspense fallback={<LoadingState size="large" />}>
      <RepoPageInner />
    </Suspense>
  );
}

function RepoPageInner() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();

  const [project, setProject] = useState<Project | null>(null);
  const [repo, setRepo] = useState<Repo | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [tree, setTree] = useState<TreeEntry[]>([]);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [commitPage, setCommitPage] = useState(1);
  const [hasMoreCommits, setHasMoreCommits] = useState(false);

  const [ref, setRef] = useState(searchParams.get("ref") || "");
  const path = searchParams.get("path") || "";
  const tab: TabKey = (searchParams.get("tab") as TabKey) === "commits" ? "commits" : "tree";

  const [loadingProject, setLoadingProject] = useState(true);
  const [loadingRepo, setLoadingRepo] = useState(true);
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [loadingTree, setLoadingTree] = useState(false);
  const [loadingCommits, setLoadingCommits] = useState(false);

  // 加载项目基础信息
  useEffect(() => {
    getProject(slug)
      .then((r) => setProject(r.project))
      .catch(() => setProject(null))
      .finally(() => setLoadingProject(false));
  }, [slug]);

  // 加载仓库与分支
  useEffect(() => {
    let cancelled = false;
    setLoadingRepo(true);
    setLoadingBranches(true);

    Promise.all([getRepo(slug), listBranches(slug)])
      .then(([repoRes, branchRes]) => {
        if (cancelled) return;
        setRepo(repoRes.repo);
        setBranches(branchRes.branches);
        if (!ref && repoRes.repo.default_branch) {
          setRef(repoRes.repo.default_branch);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRepo(null);
          setBranches([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingRepo(false);
          setLoadingBranches(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [slug, ref]);

  // 加载文件树
  useEffect(() => {
    if (tab !== "tree" || !repo) return;
    const currentRef = ref || repo.default_branch;
    let cancelled = false;
    setLoadingTree(true);
    getTree(slug, { ref: currentRef, path })
      .then((r) => {
        if (!cancelled) setTree(r.tree);
      })
      .catch(() => {
        if (!cancelled) setTree([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingTree(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug, repo, ref, path, tab]);

  // 加载 commits
  useEffect(() => {
    if (tab !== "commits" || !repo) return;
    const currentRef = ref || repo.default_branch;
    let cancelled = false;
    setLoadingCommits(true);
    listCommits(slug, { ref: currentRef, page: commitPage, per_page: 20 })
      .then((r) => {
        if (!cancelled) {
          setCommits(r.commits);
          setHasMoreCommits(r.commits.length === 20);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCommits([]);
          setHasMoreCommits(false);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingCommits(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug, repo, ref, tab, commitPage]);

  const pushQuery = (updates: Record<string, string | null>) => {
    const params = new URLSearchParams(window.location.search);
    for (const [k, v] of Object.entries(updates)) {
      if (v === null) params.delete(k);
      else params.set(k, v);
    }
    const qs = params.toString();
    router.replace(`/projects/${slug}/repos${qs ? `?${qs}` : ""}`, { scroll: false });
  };

  const handleTabChange = (key: TabKey) => {
    if (key === tab) return;
    pushQuery({ tab: key, page: null });
    setCommitPage(1);
  };

  const handleBranchChange = (value: string) => {
    setRef(value);
    pushQuery({ ref: value, path: null, page: null });
  };

  const handleNavigate = (targetPath: string) => {
    const entry = tree.find((e) => e.path === targetPath);
    if (!entry) return;
    if (entry.type === "dir") {
      pushQuery({ path: targetPath });
    } else {
      const params = new URLSearchParams();
      params.set("path", targetPath);
      if (ref) params.set("ref", ref);
      router.push(`/projects/${slug}/repos/blob?${params.toString()}`);
    }
  };

  const handleBreadcrumb = (index: number) => {
    if (index === -1) {
      pushQuery({ path: null });
      return;
    }
    const parts = path.split("/").filter(Boolean);
    const newPath = parts.slice(0, index + 1).join("/");
    pushQuery({ path: newPath });
  };

  if (loadingProject) return <LoadingState size="large" />;
  if (!project) {
    return (
      <PageContainer size="wide">
        <EmptyState description="项目不存在" />
      </PageContainer>
    );
  }

  const isOwner = user?.id === project.owner_id;

  if (!project.has_repo) {
    return (
      <PageContainer size="wide">
        <EmptyState
          description="该项目尚未关联代码仓库"
          action={
            isOwner ? (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => router.push(`/projects/${slug}/settings`)}
              >
                前往设置关联仓库
              </Button>
            ) : null
          }
        />
      </PageContainer>
    );
  }

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

  return (
    <PageContainer size="wide">
      <RepoCard repo={repo} activeTab={tab} onTabChange={handleTabChange} />

      <div className="mt-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <Space wrap className="items-center">
          <BranchSelector
            branches={branches}
            value={currentRef}
            onChange={handleBranchChange}
            loading={loadingBranches}
          />
          {tab === "tree" && (
            <Breadcrumb className="text-sm"
              items={[
                {
                  title: (
                    <button
                      type="button"
                      onClick={() => handleBreadcrumb(-1)}
                      className="flex items-center gap-1 text-text-secondary hover:text-text"
                    >
                      <HomeOutlined />
                    </button>
                  ),
                },
                ...pathParts.map((part, idx) => ({
                  title: (
                    <button
                      type="button"
                      onClick={() => handleBreadcrumb(idx)}
                      className="text-text-secondary hover:text-text"
                    >
                      {part}
                    </button>
                  ),
                })),
              ]}
            />
          )}
        </Space>
      </div>

      <div className="mt-4">
        {tab === "tree" && (
          <Card className="shadow-sm" loading={loadingTree}>
            <FileTree
              entries={tree}
              currentPath={path}
              onNavigate={handleNavigate}
            />
          </Card>
        )}

        {tab === "commits" && (
          <Card className="shadow-sm" loading={loadingCommits}>
            <CommitList commits={commits} />
            <div className="mt-4 flex justify-center">
              <ListPagination
                current={commitPage}
                total={hasMoreCommits ? commitPage * 20 + 1 : commitPage * 20}
                pageSize={20}
                onChange={(p) => setCommitPage(p)}
              />
            </div>
          </Card>
        )}
      </div>
    </PageContainer>
  );
}
