"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { Card, Tabs, Avatar, Statistic, Row, Col, Tag } from "antd";
import { UserOutlined, EnvironmentOutlined, LinkOutlined } from "@ant-design/icons";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getUser, getUserQuestions, getUserAnswers } from "@/lib/api/users";
import QuestionCard from "@/components/qa/QuestionCard";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import ListPagination from "@/components/ui/ListPagination";
import type { UserProfile, Question, Answer } from "@/types";

function UserContent() {
  const { username } = useParams<{ username: string }>();
  const router = useRouter();
  const decodedUsername = decodeURIComponent(username);

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState({ question_count: 0, answer_count: 0, accepted_count: 0, project_count: 0 });
  const [activeTab, setActiveTab] = useState("questions");

  // Questions tab
  const [questions, setQuestions] = useState<Question[]>([]);
  const [qTotal, setQTotal] = useState(0);
  const [qPage, setQPage] = useState(1);

  // Answers tab
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [aTotal, setATotal] = useState(0);
  const [aPage, setAPage] = useState(1);

  const [loading, setLoading] = useState(true);

  const perPage = 20;

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getUser(decodedUsername);
      setProfile(res.user);
      setStats(res.stats);
    } catch {
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [decodedUsername]);

  const fetchQuestions = useCallback(async (p: number) => {
    try {
      const res = await getUserQuestions(decodedUsername, { page: p, per_page: perPage });
      setQuestions(res.questions);
      setQTotal(res.total);
    } catch {
      setQuestions([]);
    }
  }, [decodedUsername, perPage]);

  const fetchAnswers = useCallback(async (p: number) => {
    try {
      const res = await getUserAnswers(decodedUsername, { page: p, per_page: perPage });
      setAnswers(res.answers as Answer[]);
      setATotal(res.total);
    } catch {
      setAnswers([]);
    }
  }, [decodedUsername, perPage]);

  useEffect(() => {
    fetchProfile();
    fetchQuestions(1);
  }, [fetchProfile, fetchQuestions]);

  const handleTabChange = (key: string) => {
    setActiveTab(key);
    if (key === "answers") fetchAnswers(aPage);
  };

  if (loading) return <LoadingState />;
  if (!profile) return <EmptyState description="用户不存在" />;

  return (
    <PageContainer size="default">
      {/* Profile Card */}
      <Card className="mb-6 border-border">
        <div className="flex items-start gap-5 flex-wrap">
          <Avatar size={80} icon={<UserOutlined />} src={profile.avatar_url} />
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-semibold text-text m-0 mb-1">
              {profile.display_name || profile.username}
            </h2>
            <p className="text-text-secondary text-sm m-0 mb-2">@{profile.username}</p>
            {profile.bio && <p className="text-text m-0 mb-2">{profile.bio}</p>}
            <div className="flex items-center gap-4 text-text-secondary text-sm flex-wrap">
              {profile.location && (
                <span className="flex items-center gap-1">
                  <EnvironmentOutlined /> {profile.location}
                </span>
              )}
              {profile.website && (
                <a href={profile.website} target="_blank" className="flex items-center gap-1 text-primary hover:underline">
                  <LinkOutlined /> {profile.website}
                </a>
              )}
              <span>加入于 {new Date(profile.created_at).toLocaleDateString("zh-CN")}</span>
            </div>
          </div>
          {profile.role !== "user" && (
            <Tag color={profile.role === "admin" ? "red" : "orange"}>{profile.role}</Tag>
          )}
        </div>
      </Card>

      {/* Stats */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card className="text-center border-border">
            <Statistic title="声望" value={profile.reputation} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="text-center border-border">
            <Statistic title="问题" value={stats.question_count || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="text-center border-border">
            <Statistic title="回答" value={stats.answer_count || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="text-center border-border">
            <Statistic title="采纳" value={stats.accepted_count || 0} />
          </Card>
        </Col>
      </Row>

      {/* Content Tabs */}
      <Card className="border-border">
        <Tabs
          activeKey={activeTab}
          onChange={handleTabChange}
          items={[
            {
              key: "questions",
              label: `问题 (${qTotal})`,
              children: (
                questions.length === 0 ? (
                  <EmptyState description="暂无问题" />
                ) : (
                  <>
                    {questions.map((q) => (
                      <QuestionCard key={q.id} question={q} />
                    ))}
                    <ListPagination
                      current={qPage}
                      total={qTotal}
                      pageSize={perPage}
                      onChange={(p) => {
                        setQPage(p);
                        fetchQuestions(p);
                      }}
                    />
                  </>
                )
              ),
            },
            {
              key: "answers",
              label: `回答 (${aTotal})`,
              children: (
                answers.length === 0 ? (
                  <EmptyState description="暂无回答" />
                ) : (
                  <>
                    {answers.map((a) => (
                      <div key={a.id} className="mb-3 p-3 border border-border rounded-lg">
                        {a.is_accepted && (
                          <Tag color="green" className="mb-1">已采纳</Tag>
                        )}
                        <div
                          className="text-text text-sm"
                          dangerouslySetInnerHTML={{ __html: a.body_html || a.body }}
                        />
                        <Link
                          href={`/questions/${a.question_id}`}
                          className="text-primary text-xs mt-1 inline-block"
                        >
                          查看问题
                        </Link>
                      </div>
                    ))}
                    <ListPagination
                      current={aPage}
                      total={aTotal}
                      pageSize={perPage}
                      onChange={(p) => {
                        setAPage(p);
                        fetchAnswers(p);
                      }}
                    />
                  </>
                )
              ),
            },
          ]}
        />
      </Card>
    </PageContainer>
  );
}

export default function UserPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <UserContent />
    </Suspense>
  );
}
