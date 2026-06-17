"use client";

import { useState, useEffect } from "react";
import { Typography, Row, Col, Card, Statistic, Button, Space } from "antd";
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
import type { Question } from "@/types";
import Link from "next/link";
import QuestionCard from "@/components/qa/QuestionCard";
import PageContainer from "@/components/layout/PageContainer";
import PageHeader from "@/components/layout/PageHeader";
import LoadingState from "@/components/ui/LoadingState";

const { Title, Paragraph } = Typography;

export default function Home() {
  const { user } = useAuth();
  const [hotQuestions, setHotQuestions] = useState<Question[]>([]);
  const [stats, setStats] = useState({ questions: 0, answers: 0, projects: 0, users: 1 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const result = await getQuestions({ sort: "popular", per_page: 5 });
        setHotQuestions(result.questions);
        setStats((prev) => ({
          ...prev,
          questions: result.total,
        }));
      } catch {
        // Silently fail
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div>
      {/* Hero — 简洁、专业 */}
      <section className="bg-bg-container border-b border-border">
        <PageContainer size="wide" className="!py-16 md:!py-20">
          <div className="text-center max-w-2xl mx-auto">
            <Title level={1} className="!text-3xl md:!text-4xl !mb-4 !font-bold !text-text">
              Codeersite
            </Title>
            <Paragraph className="!text-text-secondary !text-base md:!text-lg !mb-8 !max-w-xl !mx-auto">
              面向开发者的社区平台 — 融合问答讨论与项目管理，让协作更高效
            </Paragraph>
            <Space size="middle">
              {user ? (
                <>
                  <Link href="/questions/ask">
                    <Button type="primary" size="large" icon={<PlusOutlined />} className="!rounded-lg !h-10">
                      提出问题
                    </Button>
                  </Link>
                  <Link href="/projects">
                    <Button size="large" icon={<ProjectOutlined />} className="!rounded-lg !h-10">
                      浏览项目
                    </Button>
                  </Link>
                </>
              ) : (
                <>
                  <Link href="/register">
                    <Button type="primary" size="large" className="!rounded-lg !h-10">
                      立即注册
                    </Button>
                  </Link>
                  <Link href="/questions">
                    <Button size="large" className="!rounded-lg !h-10">
                      浏览问答
                    </Button>
                  </Link>
                </>
              )}
            </Space>
          </div>
        </PageContainer>
      </section>

      {/* Stats */}
      <PageContainer size="wide" className="!py-0">
        <div className="-mt-8">
          <Row gutter={16}>
            <Col xs={12} sm={6}>
              <Card className="shadow-sm">
                <Statistic title="问题" value={stats.questions} prefix={<QuestionCircleOutlined />} />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="shadow-sm">
                <Statistic title="回答" value={stats.answers} prefix={<CommentOutlined />} />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="shadow-sm">
                <Statistic title="项目" value={stats.projects} prefix={<ProjectOutlined />} />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="shadow-sm">
                <Statistic title="用户" value={stats.users} prefix={<UserOutlined />} />
              </Card>
            </Col>
          </Row>
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
          hotQuestions.map((q) => (
            <QuestionCard key={q.id} question={q} />
          ))
        )}
      </PageContainer>

      {/* Features */}
      <PageContainer size="wide" className="!pt-0">
        <Row gutter={[24, 24]}>
          <Col xs={24} md={12}>
            <Card
              className="shadow-sm"
              title={<><QuestionCircleOutlined /> 问答社区</>}
              extra={<Link href="/questions"><ArrowRightOutlined /></Link>}
            >
              <Paragraph className="!text-text-secondary !mb-0">
                提出问题，获取答案。投票选出最佳回答，积累社区声望。支持 Markdown
                编辑，标签分类，全文搜索。
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card
              className="shadow-sm"
              title={<><ProjectOutlined /> 项目管理</>}
              extra={<Link href="/projects"><ArrowRightOutlined /></Link>}
            >
              <Paragraph className="!text-text-secondary !mb-0">
                创建项目，跟踪 Issue，使用看板管理任务。设置里程碑规划开发节奏，
                与团队成员高效协作。
              </Paragraph>
            </Card>
          </Col>
        </Row>
      </PageContainer>
    </div>
  );
}
