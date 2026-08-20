"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Input, Button, Card, Form, Space } from "antd";
import { message } from "@/lib/message";
import { useAuth } from "@/providers/AuthProvider";
import { createQuestion } from "@/lib/api/questions";
import TagSelect from "@/components/qa/TagSelect";
import PageContainer from "@/components/layout/PageContainer";

const { TextArea } = Input;

const DRAFT_KEY = "codeersite:ask_draft";

interface DraftData {
  title?: string;
  body?: string;
  tag_ids?: string[];
}

function loadDraft(): DraftData | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveDraft(data: DraftData) {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
  } catch {
    // ignore
  }
}

function clearDraft() {
  try {
    localStorage.removeItem(DRAFT_KEY);
  } catch {
    // ignore
  }
}

export default function AskQuestionPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewVisible, setPreviewVisible] = useState(false);
  const [draftLoaded, setDraftLoaded] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, router, user]);

  // 加载草稿（仅一次）
  useEffect(() => {
    if (authLoading || !user || draftLoaded) return;
    const draft = loadDraft();
    if (draft) {
      form.setFieldsValue({
        title: draft.title || "",
        body: draft.body || "",
        tag_ids: draft.tag_ids || [],
      });
      // 如果有内容，提示用户已恢复草稿
      if (draft.title || draft.body) {
        message.info("已恢复上次未提交的草稿");
      }
    }
    setDraftLoaded(true);
  }, [authLoading, form, draftLoaded, user]);

  // 自动保存草稿（防抖 1s）
  const autoSave = useCallback(() => {
    const values = form.getFieldsValue();
    saveDraft({
      title: values.title || "",
      body: values.body || "",
      tag_ids: values.tag_ids || [],
    });
  }, [form]);

  useEffect(() => {
    if (authLoading || !user || !draftLoaded) return;
    const timer = setInterval(autoSave, 1000);
    return () => clearInterval(timer);
  }, [authLoading, autoSave, draftLoaded, user]);

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
      clearDraft();
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

  const handleClearDraft = () => {
    clearDraft();
    form.resetFields();
    message.success("草稿已清除");
  };

  if (authLoading || !user) return null;

  return (
    <PageContainer>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-text m-0">提出问题</h2>
        <Button size="small" onClick={handleClearDraft}>
          清除草稿
        </Button>
      </div>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          autoComplete="off"
          onValuesChange={autoSave}
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
            <Card size="small" className="mb-4 !bg-bg-elevated">
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
