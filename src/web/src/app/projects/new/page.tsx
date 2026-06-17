"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input, Button, Card, Form, Space, Radio, message } from "antd";
import { useAuth } from "@/providers/AuthProvider";
import { createProject } from "@/lib/api/projects";
import PageContainer from "@/components/layout/PageContainer";

const { TextArea } = Input;

export default function NewProjectPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  if (!user) {
    router.push("/login");
    return null;
  }

  const onFinish = async (values: { name: string; description?: string; visibility: string }) => {
    setLoading(true);
    try {
      const r = await createProject(values);
      message.success("项目创建成功！");
      router.push(`/projects/${r.project.slug}`);
    } catch (err: any) {
      message.error(err?.response?.data?.message || "创建失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer size="narrow">
      <h2 className="text-xl font-semibold text-text mb-6">创建项目</h2>
      <Card>
        <Form layout="vertical" onFinish={onFinish} initialValues={{ visibility: "public" }}>
          <Form.Item
            name="name"
            label="项目名称"
            rules={[
              { required: true, message: "请输入项目名称" },
              { max: 100 },
            ]}
          >
            <Input placeholder="例如：my-awesome-project" size="large" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <TextArea rows={4} placeholder="简单描述一下你的项目..." />
          </Form.Item>
          <Form.Item name="visibility" label="可见性">
            <Radio.Group>
              <Radio.Button value="public">公开</Radio.Button>
              <Radio.Button value="private">私有</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading} size="large">
                创建项目
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
