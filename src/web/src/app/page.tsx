"use client";

import { useState, useEffect } from "react";
import { Button, Space } from "antd";
import {
  QuestionCircleOutlined,
  ProjectOutlined,
  UserOutlined,
  CommentOutlined,
  ArrowRightOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getQuestions } from "@/lib/api/questions";
import { getStats } from "@/lib/api/stats";
import type { Question } from "@/types";
import Link from "next/link";
import QuestionCard from "@/components/qa/QuestionCard";
import PageContainer from "@/components/layout/PageContainer";
import PageHeader from "@/components/layout/PageHeader";
import LoadingState from "@/components/ui/LoadingState";

/** 入场动画 stagger —— Tailwind 构建期扫描，必须显式列出，禁用模板拼接 */
const ENTER_DELAYS = [
  "enter-delay-0",
  "enter-delay-1",
  "enter-delay-2",
  "enter-delay-3",
  "enter-delay-4",
  "enter-delay-5",
] as const;

const STATS_META = [
  { key: "questions", label: "问题", icon: <QuestionCircleOutlined /> },
  { key: "answers", label: "回答", icon: <CommentOutlined /> },
  { key: "projects", label: "项目", icon: <ProjectOutlined /> },
  { key: "users", label: "用户", icon: <UserOutlined /> },
] as const;

const FEATURES = [
  {
    icon: <QuestionCircleOutlined />,
    title: "问答社区",
    description:
      "提出问题，获取答案。投票选出最佳回答，积累社区声望。支持 Markdown 编辑，标签分类，全文搜索。",
    href: "/questions",
  },
  {
    icon: <ProjectOutlined />,
    title: "项目管理",
    description:
      "创建项目，跟踪 Issue，使用看板管理任务。设置里程碑规划开发节奏，与团队成员高效协作。",
    href: "/projects",
  },
] as const;

export default function Home() {
  const { user } = useAuth();
  const [hotQuestions, setHotQuestions] = useState<Question[]>([]);
  const [stats, setStats] = useState({ questions: 0, answers: 0, projects: 0, users: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [statsResult, questionsResult] = await Promise.all([
          getStats(),
          getQuestions({ sort: "popular", per_page: 5 }),
        ]);
        setStats(statsResult);
        setHotQuestions(questionsResult.questions);
      } catch {
        // Silently fail
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div>
      {/* Hero —— 光晕 + 淡网格氛围层 */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 pointer-events-none bg-hero-glow" />
        <div className="absolute inset-0 pointer-events-none bg-grid-fade" />
        <PageContainer size="wide" className="relative !py-24 md:!py-32">
          <div className="text-center max-w-2xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4 text-gradient animate-enter">
              Codeersite
            </h1>
            <p className="text-text-secondary text-base md:text-lg mb-8 max-w-xl mx-auto animate-enter enter-delay-1">
              面向开发者的社区平台 — 融合问答讨论与项目管理，让协作更高效
            </p>
            <div className="animate-enter enter-delay-2">
              <Space size="middle">
                {user ? (
                  <>
                    <Link href="/questions/ask">
                      <Button type="primary" size="large" icon={<PlusOutlined />}>
                        提出问题
                      </Button>
                    </Link>
                    <Link href="/projects">
                      <Button size="large" icon={<ProjectOutlined />}>
                        浏览项目
                      </Button>
                    </Link>
                  </>
                ) : (
                  <>
                    <Link href="/register">
                      <Button type="primary" size="large">
                        立即注册
                      </Button>
                    </Link>
                    <Link href="/questions">
                      <Button size="large">浏览问答</Button>
                    </Link>
                  </>
                )}
              </Space>
            </div>
          </div>
        </PageContainer>
      </section>

      {/* Stats —— 玻璃拟态卡，上浮压住 hero 边界以透出 blur */}
      <PageContainer size="wide" className="!py-0">
        <div className="-mt-10 grid grid-cols-2 sm:grid-cols-4 gap-4">
          {STATS_META.map((meta, i) => (
            <div
              key={meta.key}
              className={`glass-card rounded-lg p-5 text-text card-lift animate-enter ${ENTER_DELAYS[i + 1]}`}
            >
              <div className="flex items-center gap-2 text-text-tertiary text-sm">
                <span className="text-primary text-base">{meta.icon}</span>
                {meta.label}
              </div>
              <div className="mt-2 text-2xl font-semibold tracking-tight">
                {stats[meta.key]}
              </div>
            </div>
          ))}
        </div>
      </PageContainer>

      {/* Hot Questions */}
      <PageContainer size="wide">
        <PageHeader
          title="热门问题"
          actions={
            <Link href="/questions?sort=popular">
              <Button type="link" icon={<ArrowRightOutlined />}>
                查看更多
              </Button>
            </Link>
          }
        />
        {loading ? (
          <LoadingState />
        ) : (
          hotQuestions.map((q, i) => (
            <div key={q.id} className={`animate-enter ${ENTER_DELAYS[Math.min(i, 5)]}`}>
              <QuestionCard question={q} />
            </div>
          ))
        )}
      </PageContainer>

      {/* Features —— 自定义卡片，图标淡色点缀 */}
      <PageContainer size="wide" className="!pt-0">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {FEATURES.map((feature, i) => (
            <div
              key={feature.title}
              className={`rounded-lg border border-border bg-bg-container p-6 card-lift animate-enter ${ENTER_DELAYS[i]}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary-soft text-lg">
                  {feature.icon}
                </div>
                <Link
                  href={feature.href}
                  className="text-text-tertiary hover:text-primary"
                  aria-label={`前往${feature.title}`}
                >
                  <ArrowRightOutlined />
                </Link>
              </div>
              <h3 className="mt-4 text-lg font-semibold">{feature.title}</h3>
              <p className="mt-2 mb-0 text-text-secondary text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </PageContainer>
    </div>
  );
}
