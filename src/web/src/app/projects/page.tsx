"use client";

import { useState, useEffect } from "react";
import { Radio, Space, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import Link from "next/link";
import { useAuth } from "@/providers/AuthProvider";
import { getProjects } from "@/lib/api/projects";
import type { Project } from "@/types";
import ProjectCard from "@/components/project/ProjectCard";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import ListPagination from "@/components/ui/ListPagination";

export default function ProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("newest");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const r = await getProjects({ page, per_page: 20, sort });
        setProjects(r.projects);
        setTotal(r.total);
      } catch {
        setProjects([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [page, sort]);

  return (
    <PageContainer size="wide">
      <div className="flex justify-between items-center flex-wrap gap-3 mb-6">
        <h2 className="text-xl font-semibold text-text m-0">项目</h2>
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
            <Radio.Button value="active">活跃</Radio.Button>
            <Radio.Button value="stars">最多 Star</Radio.Button>
          </Radio.Group>
          {user && (
            <Link href="/projects/new">
              <Button type="primary" icon={<PlusOutlined />}>
                创建项目
              </Button>
            </Link>
          )}
        </Space>
      </div>

      {loading ? (
        <LoadingState />
      ) : projects.length === 0 ? (
        <EmptyState
          description="暂无项目"
          action={
            user ? (
              <Link href="/projects/new">
                <Button type="primary">创建第一个项目</Button>
              </Link>
            ) : undefined
          }
        />
      ) : (
        <>
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
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
