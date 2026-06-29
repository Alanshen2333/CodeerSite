"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Input, Button, Card, Form, Radio, Space, message, Popconfirm, Tag } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import {
  getProject,
  updateProject,
  deleteProject,
  getMembers,
  removeMember,
} from "@/lib/api/projects";
import type { Project, ProjectMember } from "@/types";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";

const { TextArea } = Input;

// 项目级角色映射（constants.ts 的 roleLabel 只有系统角色 user/moderator/admin）
const memberRoleLabel: Record<string, string> = { owner: "拥有者", admin: "管理员", member: "成员" };
const memberRoleColor: Record<string, string> = { owner: "gold", admin: "blue", member: "default" };

interface FormValues {
  name: string;
  description?: string;
  visibility: "public" | "private";
}

export default function SettingsPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [form] = Form.useForm<FormValues>();
  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = async () => {
    try {
      const [p, m] = await Promise.all([getProject(slug), getMembers(slug)]);
      setProject(p.project);
      setMembers(m.members);
      form.setFieldsValue({
        name: p.project.name,
        description: p.project.description || "",
        visibility: p.project.visibility,
      });
    } catch {
      setProject(null);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, [slug]);

  if (loading) return <LoadingState size="large" />;
  if (!project) {
    return (
      <PageContainer size="narrow">
        <EmptyState description="项目不存在" />
      </PageContainer>
    );
  }
  if (!user) {
    router.push("/login");
    return null;
  }
  if (user.id !== project.owner_id) {
    return (
      <PageContainer size="narrow">
        <EmptyState description="仅项目拥有者可访问设置" />
      </PageContainer>
    );
  }

  const onFinish = async (values: FormValues) => {
    setSaving(true);
    try {
      const r = await updateProject(slug, values);
      setProject(r.project);
      message.success("已保存");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "保存失败"
          : "保存失败";
      message.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteProject(slug);
      message.success("项目已删除");
      router.push("/projects");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "删除失败"
          : "删除失败";
      message.error(msg);
    } finally {
      setDeleting(false);
    }
  };

  const handleRemoveMember = async (userId: string, name: string) => {
    try {
      await removeMember(slug, userId);
      setMembers((ms) => ms.filter((m) => m.user_id !== userId));
      message.success(`已移除 ${name}`);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "移除失败"
          : "移除失败";
      message.error(msg);
    }
  };

  return (
    <PageContainer size="narrow">
      <h2 className="text-xl font-semibold text-text mb-6">项目设置</h2>

      <Card title="基本信息" className="mb-4">
        <Form<FormValues>
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ visibility: "public" }}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: "请输入项目名称" }, { max: 100 }]}
          >
            <Input placeholder="项目名称" size="large" />
          </Form.Item>
          <Form.Item name="description" label="项目描述" rules={[{ max: 2000 }]}>
            <TextArea rows={4} placeholder="简单描述一下你的项目..." />
          </Form.Item>
          <Form.Item name="visibility" label="可见性">
            <Radio.Group>
              <Radio.Button value="public">公开</Radio.Button>
              <Radio.Button value="private">私有</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={saving} size="large">
              保存
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="成员" className="mb-4">
        {members.length === 0 ? (
          <EmptyState description="暂无成员" />
        ) : (
          <Space orientation="vertical" className="w-full">
            {members.map((m) => {
              const name = m.user?.display_name || m.user?.username || m.user_id;
              return (
                <div
                  key={m.user_id}
                  className="flex justify-between items-center py-2 border-b border-border last:border-0"
                >
                  <Space>
                    <span className="text-text">{name}</span>
                    <Tag color={memberRoleColor[m.role]}>{memberRoleLabel[m.role]}</Tag>
                  </Space>
                  {m.role !== "owner" && (
                    <Popconfirm
                      title={`移除 ${name}？`}
                      onConfirm={() => handleRemoveMember(m.user_id, name)}
                    >
                      <Button size="small" danger icon={<DeleteOutlined />}>
                        移除
                      </Button>
                    </Popconfirm>
                  )}
                </div>
              );
            })}
          </Space>
        )}
      </Card>

      <Card title="危险区">
        <div className="flex justify-between items-center gap-4 flex-wrap">
          <div>
            <p className="text-text m-0">删除项目</p>
            <p className="text-text-secondary text-sm m-0">
              删除后无法恢复，所有 Issue、里程碑、看板数据将被清除。
            </p>
          </div>
          <Popconfirm
            title="确定删除此项目？"
            okText="删除"
            okButtonProps={{ danger: true }}
            onConfirm={handleDelete}
          >
            <Button danger loading={deleting}>
              删除项目
            </Button>
          </Popconfirm>
        </div>
      </Card>
    </PageContainer>
  );
}
