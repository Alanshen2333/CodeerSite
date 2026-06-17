"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, Row, Col, Statistic, Button, Space, Tabs } from "antd";
import {
  BugOutlined,
  EditOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getProject } from "@/lib/api/projects";
import { getIssues } from "@/lib/api/issues";
import type { Project, Issue } from "@/types";
import IssueCard from "@/components/project/IssueCard";
import Link from "next/link";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";

export default function ProjectPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [stats, setStats] = useState({ open: 0, in_progress: 0, closed: 0, total: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [pRes, iRes] = await Promise.all([
          getProject(slug),
          getIssues(slug, { per_page: 5, sort: "newest" }),
        ]);
        setProject(pRes.project);
        setIssues(iRes.issues);
        setStats(iRes.stats);
      } catch {
        setProject(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [slug]);

  if (loading) return <LoadingState size="large" />;
  if (!project) return <PageContainer size="wide"><EmptyState description="项目不存在" /></PageContainer>;

  const isOwner = user?.id === project.owner_id;

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

      <div className="flex justify-between items-center mb-3">
        <h3 className="text-base font-semibold text-text m-0">最近 Issue</h3>
        <Space>
          <Link href={`/projects/${slug}/issues`}>
            <Button type="link">查看全部</Button>
          </Link>
          <Link href={`/projects/${slug}/issues/new`}>
            <Button type="primary" size="small">新建 Issue</Button>
          </Link>
        </Space>
      </div>

      {issues.length === 0 ? (
        <Card><EmptyState description="暂无 Issue" /></Card>
      ) : (
        issues.map((i) => <IssueCard key={i.id} issue={i} slug={slug} />)
      )}

      <div className="mt-6">
        <Tabs
          items={[
            { key: "issues", label: <Link href={`/projects/${slug}/issues`}>Issues</Link> },
            { key: "kanban", label: <Link href={`/projects/${slug}/kanban`}>看板</Link> },
            { key: "milestones", label: <Link href={`/projects/${slug}/milestones`}>里程碑</Link> },
          ]}
        />
      </div>
    </PageContainer>
  );
}
