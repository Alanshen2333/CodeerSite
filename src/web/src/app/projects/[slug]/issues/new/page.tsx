"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Input, Button, Card, Form, Select, Space, message } from "antd";
import { useAuth } from "@/providers/AuthProvider";
import { createIssue } from "@/lib/api/issues";
import { getMembers } from "@/lib/api/projects";
import { getMilestones } from "@/lib/api/milestones";
import { priorityLabel } from "@/styles/constants";
import type { ProjectMember, Milestone } from "@/types";
import PageContainer from "@/components/layout/PageContainer";
import TagSelect from "@/components/qa/TagSelect";

const { TextArea } = Input;

interface FormValues {
  title: string;
  body?: string;
  priority: string;
  assignee_id?: string;
  milestone_id?: string;
  tag_ids?: string[];
}

export default function NewIssuePage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);

  useEffect(() => {
    Promise.all([getMembers(slug), getMilestones(slug)])
      .then(([m, mi]) => {
        setMembers(m.members);
        setMilestones(mi.milestones);
      })
      .catch(() => {
        // 选项加载失败时下拉为空，不阻断表单
      });
  }, [slug]);

  if (!user) {
    router.push("/login");
    return null;
  }

  const onFinish = async (values: FormValues) => {
    setLoading(true);
    try {
      const r = await createIssue(slug, {
        title: values.title,
        body: values.body,
        priority: values.priority,
        assignee_id: values.assignee_id,
        milestone_id: values.milestone_id,
        tag_ids: values.tag_ids,
      });
      message.success("Issue 创建成功");
      router.push(`/projects/${slug}/issues/${r.issue.issue_number}`);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "创建失败"
          : "创建失败";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const priorityOptions = Object.entries(priorityLabel).map(([value, label]) => ({ value, label }));
  const assigneeOptions = members.map((m) => ({
    value: m.user_id,
    label: m.user?.display_name || m.user?.username || m.user_id,
  }));
  const milestoneOptions = milestones.map((m) => ({ value: m.id, label: m.title }));

  return (
    <PageContainer size="narrow">
      <h2 className="text-xl font-semibold text-text mb-6">新建 Issue</h2>
      <Card>
        <Form<FormValues>
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ priority: "medium" }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: "请输入标题" }, { max: 300 }]}
          >
            <Input placeholder="简明描述这个 Issue..." size="large" />
          </Form.Item>
          <Form.Item name="body" label="详情">
            <TextArea rows={6} placeholder="支持 Markdown，详细描述背景与复现步骤..." />
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <Select options={priorityOptions} />
          </Form.Item>
          <Form.Item name="assignee_id" label="指派给">
            <Select
              allowClear
              placeholder="不指派"
              options={assigneeOptions}
              notFoundContent="暂无可指派成员"
            />
          </Form.Item>
          <Form.Item name="milestone_id" label="里程碑">
            <Select
              allowClear
              placeholder="无里程碑"
              options={milestoneOptions}
              notFoundContent="暂无里程碑"
            />
          </Form.Item>
          <Form.Item name="tag_ids" label="标签">
            <TagSelect />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading} size="large">
                创建 Issue
              </Button>
              <Button onClick={() => router.back()} size="large">
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </PageContainer>
  );
}
