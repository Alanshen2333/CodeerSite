"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Card, Row, Col, Statistic, Button, Space, Tabs } from "antd";
import { message } from "@/lib/message";
import {
  BugOutlined,
  EditOutlined,
  StarOutlined,
  StarFilled,
  CodeOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getProject, toggleProjectStar } from "@/lib/api/projects";
import { getIssues } from "@/lib/api/issues";
import { getMilestones } from "@/lib/api/milestones";
import type { Project, Issue, Milestone } from "@/types";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import IssuesPanel from "@/components/project/panels/IssuesPanel";
import KanbanPanel from "@/components/project/panels/KanbanPanel";
import MilestonesPanel from "@/components/project/panels/MilestonesPanel";
import ReposPanel from "@/components/project/panels/ReposPanel";
import IssueDetailDrawer from "@/components/project/IssueDetailDrawer";
import IssueFormDrawer from "@/components/project/IssueFormDrawer";
import MilestoneDetailDrawer from "@/components/project/MilestoneDetailDrawer";

type TabKey = "issues" | "kanban" | "milestones" | "repos";
const VALID_TABS: TabKey[] = ["issues", "kanban", "milestones", "repos"];

export default function ProjectPage() {
  return (
    <Suspense fallback={<LoadingState size="large" />}>
      <ProjectPageInner />
    </Suspense>
  );
}

function ProjectPageInner() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState({ open: 0, in_progress: 0, closed: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  // 抽屉内 Issue/里程碑变更后递增，触发各面板刷新
  const [refreshTick, setRefreshTick] = useState(0);

  // ── URL query 驱动 Tab + 抽屉 ──
  const tabParam = searchParams.get("tab") as TabKey | null;
  const activeTab: TabKey = tabParam && VALID_TABS.includes(tabParam) ? tabParam : "issues";
  const issueNumParam = searchParams.get("issue");
  const parsedIssueNum = issueNumParam ? Number(issueNumParam) : NaN;
  const openIssueNum =
    Number.isFinite(parsedIssueNum) && parsedIssueNum > 0 ? parsedIssueNum : null;
  const newIssueOpen = searchParams.get("new_issue") === "1";
  const milestoneIdParam = searchParams.get("milestone");

  const [activeMilestone, setActiveMilestone] = useState<Milestone | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [pRes, iRes] = await Promise.all([
          getProject(slug),
          getIssues(slug, { per_page: 1 }),
        ]);
        setProject(pRes.project);
        setStats(iRes.stats);
      } catch {
        setProject(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [slug]);

  // 用 query 更新 URL（同路由改 query，client state 保留）。
  // 基于 window.location.search 读取最新 URL 而非闭包里的 searchParams 快照，
  // 避免同一 tick 内连续多次 pushQuery 时后者覆盖前者写入的 param。
  const pushQuery = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(
        typeof window !== "undefined" ? window.location.search : searchParams.toString(),
      );
      for (const [k, v] of Object.entries(updates)) {
        if (v === null) params.delete(k);
        else params.set(k, v);
      }
      const qs = params.toString();
      router.replace(`/projects/${slug}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [router, slug, searchParams],
  );

  // 里程碑详情抽屉：URL ?milestone=<id> 驱动。param 有值但 activeMilestone 缺失/不匹配时
  // 按 id 从后端列表查找并设置，使深链/刷新能恢复抽屉；param 清空时关闭。
  useEffect(() => {
    if (!milestoneIdParam) {
      setActiveMilestone(null);
      return;
    }
    if (activeMilestone?.id === milestoneIdParam) return;
    getMilestones(slug)
      .then((r) => {
        const found = r.milestones.find((m) => m.id === milestoneIdParam) ?? null;
        setActiveMilestone(found);
      })
      .catch(() => setActiveMilestone(null));
  }, [milestoneIdParam, slug]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return <LoadingState size="large" />;
  if (!project)
    return (
      <PageContainer size="wide">
        <EmptyState description="项目不存在" />
      </PageContainer>
    );

  const isOwner = user?.id === project.owner_id;

  const handleToggleStar = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    if (!project) return;
    const prevStarred = project.starred ?? false;
    const prevCount = project.star_count;
    setProject({
      ...project,
      starred: !prevStarred,
      star_count: prevCount + (prevStarred ? -1 : 1),
    });
    try {
      const r = await toggleProjectStar(slug);
      setProject((p) => (p ? { ...p, starred: r.starred, star_count: r.star_count } : p));
    } catch (err: unknown) {
      setProject((p) => (p ? { ...p, starred: prevStarred, star_count: prevCount } : p));
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "操作失败"
          : "操作失败";
      message.error(msg);
    }
  };

  const handleOpenIssue = (issueNumber: number) => pushQuery({ issue: String(issueNumber), new_issue: null, milestone: null });
  const handleCloseIssue = () => pushQuery({ issue: null });
  const handleNewIssue = () => pushQuery({ new_issue: "1", issue: null, milestone: null });
  const handleCloseNewIssue = () => pushQuery({ new_issue: null });
  const handleOpenMilestone = (m: Milestone) => {
    setActiveMilestone(m);
    pushQuery({ milestone: m.id, issue: null, new_issue: null });
  };
  const handleCloseMilestone = () => pushQuery({ milestone: null });

  const handleChanged = () => setRefreshTick((t) => t + 1);

  const handleIssueCreated = (issue: Issue) => {
    handleChanged();
    // 创建后直接打开新 Issue 的详情抽屉
    pushQuery({ new_issue: null, issue: String(issue.issue_number) });
  };

  return (
    <PageContainer size="wide">
      <div className="flex justify-between items-start flex-wrap gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-semibold text-text m-0">{project.name}</h1>
          {project.description && (
            <p className="text-text-secondary mt-2">{project.description}</p>
          )}
        </div>
        <Space>
          <Button
            icon={project.starred ? <StarFilled /> : <StarOutlined />}
            onClick={handleToggleStar}
          >
            {project.star_count}
          </Button>
          {isOwner && (
            <Button icon={<EditOutlined />} onClick={() => router.push(`/projects/${slug}/settings`)}>
              设置
            </Button>
          )}
        </Space>
      </div>

      <Row gutter={16} className="mb-6">
        <Col xs={12} sm={6}>
          <Card className="shadow-sm">
            <Statistic title="Issue" value={stats.total} prefix={<BugOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="shadow-sm">
            <Statistic title="待处理" value={stats.open} styles={{ content: { color: "#5e6ad2" } }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="shadow-sm">
            <Statistic title="进行中" value={stats.in_progress} styles={{ content: { color: "#f5a623" } }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="shadow-sm">
            <Statistic title="已关闭" value={stats.closed} styles={{ content: { color: "#0eb478" } }} />
          </Card>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={(k) => pushQuery({ tab: k })}
        items={[
          {
            key: "issues",
            label: "Issues",
            children: (
              <IssuesPanel
                slug={slug}
                onOpenIssue={handleOpenIssue}
                onNewIssue={handleNewIssue}
                refreshTick={refreshTick}
              />
            ),
          },
          {
            key: "kanban",
            label: "看板",
            children: (
              <KanbanPanel slug={slug} onOpenIssue={handleOpenIssue} refreshTick={refreshTick} />
            ),
          },
          {
            key: "milestones",
            label: "里程碑",
            children: (
              <MilestonesPanel
                slug={slug}
                onOpenMilestone={handleOpenMilestone}
                refreshTick={refreshTick}
              />
            ),
          },
          {
            key: "repos",
            label: "代码",
            icon: <CodeOutlined />,
            children: <ReposPanel slug={slug} hasRepo={project.has_repo} isOwner={isOwner} />,
          },
        ]}
      />

      {/* 抽屉：URL query 驱动开合 */}
      <IssueDetailDrawer
        slug={slug}
        issueNumber={openIssueNum}
        onClose={handleCloseIssue}
        onChanged={handleChanged}
      />
      <IssueFormDrawer
        slug={slug}
        open={newIssueOpen}
        onClose={handleCloseNewIssue}
        onCreated={handleIssueCreated}
      />
      <MilestoneDetailDrawer
        slug={slug}
        milestone={activeMilestone}
        onClose={handleCloseMilestone}
        onOpenIssue={handleOpenIssue}
      />
    </PageContainer>
  );
}
