"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input, Button, Card, Form, Space, message } from "antd";
import { useAuth } from "@/providers/AuthProvider";
import { createQuestion } from "@/lib/api/questions";
import TagSelect from "@/components/qa/TagSelect";
import MarkdownRenderer from "@/components/qa/MarkdownRenderer";
import PageContainer from "@/components/layout/PageContainer";

const { TextArea } = Input;

export default function AskQuestionPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewVisible, setPreviewVisible] = useState(false);

  if (!user) {
    router.push("/login");
    return null;
  }

  const onFinish = async (values: {
    title: string;
    body: string;
    tag_ids?: string[];
  }) => {
    setLoading(true);
    try {
      const result = await createQuestion({
        title: values.title,
        body: values.body,
        tag_ids: values.tag_ids || [],
      });
      message.success("问题已发布！");
      router.push(`/questions/${result.question.id}`);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "发布失败"
          : "发布失败";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = () => {
    const body = form.getFieldValue("body");
    setPreviewHtml(body || "");
    setPreviewVisible(!previewVisible);
  };

  return (
    <PageContainer>
      <h2 className="text-xl font-semibold text-text mb-6">提出问题</h2>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[
              { required: true, message: "请输入问题标题" },
              { min: 5, message: "标题至少 5 个字符" },
              { max: 300, message: "标题不能超过 300 个字符" },
            ]}
          >
            <Input placeholder="例如：如何在 Flask 中配置中间件？" size="large" />
          </Form.Item>

          <Form.Item
            name="body"
            label="描述 (支持 Markdown)"
            rules={[
              { required: true, message: "请输入问题描述" },
              { min: 10, message: "描述至少 10 个字符" },
            ]}
          >
            <TextArea
              rows={12}
              placeholder={"详细描述你的问题...\n\n支持 Markdown 语法：\n- **粗体**\n- `代码`\n- ```代码块```"}
            />
          </Form.Item>

          <Form.Item className="!mb-1">
            <Button onClick={handlePreview} size="small">
              {previewVisible ? "关闭预览" : "预览"}
            </Button>
          </Form.Item>

          {previewVisible && previewHtml && (
            <Card size="small" className="mb-4 bg-gray-50">
              <div className="whitespace-pre-wrap font-mono text-xs">
                {previewHtml}
              </div>
            </Card>
          )}

          <Form.Item name="tag_ids" label="标签（最多5个）">
            <TagSelect />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading} size="large">
                发布问题
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
