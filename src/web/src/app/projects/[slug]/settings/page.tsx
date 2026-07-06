"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Input, Button, Card, Form, Radio, Select, Space, Popconfirm, Tag, Typography } from "antd";
import { message } from "@/lib/message";
import {
  DeleteOutlined,
  CodeOutlined,
  CopyOutlined,
  KeyOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import {
  getProject,
  updateProject,
  deleteProject,
  getMembers,
  removeMember,
  addMember,
} from "@/lib/api/projects";
import { getRepo, createRepo, deleteRepo } from "@/lib/api/repos";
import { searchUsers } from "@/lib/api/users";
import { getGitCredentials } from "@/lib/api/auth";
import type { Project, ProjectMember, Repo } from "@/types";
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
  const [repo, setRepo] = useState<Repo | null>(null);
  const [repoLoading, setRepoLoading] = useState(true);
  const [creatingRepo, setCreatingRepo] = useState(false);
  const [deletingRepo, setDeletingRepo] = useState(false);
  const [copyingCreds, setCopyingCreds] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [userOptions, setUserOptions] = useState<{ value: string; label: string }[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | undefined>();
  const [newRole, setNewRole] = useState<"admin" | "member">("member");
  const [adding, setAdding] = useState(false);

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
      // 项目拥有仓库时才拉取仓库信息
      if (p.project.has_repo) {
        try {
          const r = await getRepo(slug);
          setRepo(r.repo);
        } catch {
          setRepo(null);
        }
      } else {
        setRepo(null);
      }
    } catch {
      setProject(null);
    } finally {
      setLoading(false);
      setRepoLoading(false);
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

  const handleSearchUser = async (val: string) => {
    if (!val.trim()) {
      setUserOptions([]);
      return;
    }
    setSearching(true);
    try {
      const r = await searchUsers(val.trim(), 10);
      const memberIds = new Set(members.map((m) => m.user_id));
      setUserOptions(
        r.users
          .filter((u) => !memberIds.has(u.id) && u.id !== project?.owner_id)
          .map((u) => ({
            value: u.id,
            label: `${u.display_name || u.username} (@${u.username})`,
          })),
      );
    } catch {
      setUserOptions([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAddMember = async () => {
    if (!selectedUserId) return;
    setAdding(true);
    try {
      await addMember(slug, selectedUserId, newRole);
      message.success("已添加成员");
      setSelectedUserId(undefined);
      setUserOptions([]);
      await load();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "添加失败"
          : "添加失败";
      message.error(msg);
    } finally {
      setAdding(false);
    }
  };

  const handleCreateRepo = async () => {
    setCreatingRepo(true);
    try {
      const r = await createRepo(slug);
      setRepo(r.repo);
      setProject((p) => (p ? { ...p, has_repo: true, gitea_full_name: r.repo.full_name } : p));
      message.success("仓库已创建");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "创建仓库失败"
          : "创建仓库失败";
      message.error(msg);
    } finally {
      setCreatingRepo(false);
    }
  };

  const handleDeleteRepo = async () => {
    setDeletingRepo(true);
    try {
      await deleteRepo(slug);
      setRepo(null);
      setProject((p) => (p ? { ...p, has_repo: false, gitea_full_name: null } : p));
      message.success("仓库已删除");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "删除仓库失败"
          : "删除仓库失败";
      message.error(msg);
    } finally {
      setDeletingRepo(false);
    }
  };

  const handleCopyCloneUrl = (url: string) => {
    navigator.clipboard.writeText(url).then(() => message.success("已复制"));
  };

  const handleCopyWithCredentials = async () => {
    if (!repo) return;
    setCopyingCreds(true);
    try {
      const data = await getGitCredentials(repo.full_name);
      await navigator.clipboard.writeText(data.clone_url_with_credentials);
      message.success("已复制 HTTPS（含凭据）");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "复制失败"
          : "复制失败";
      message.error(msg);
    } finally {
      setCopyingCreds(false);
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

      <Card
        title={
          <Space>
            <CodeOutlined />
            <span>代码仓库</span>
          </Space>
        }
        className="mb-4"
        loading={repoLoading}
      >
        {repo ? (
          <Space direction="vertical" className="w-full">
            <div className="flex justify-between items-center flex-wrap gap-3">
              <div>
                <Typography.Text className="text-text font-medium">{repo.full_name}</Typography.Text>
                <div className="text-text-secondary text-sm">
                  默认分支：{repo.default_branch}
                </div>
              </div>
              <Popconfirm
                title="确定删除仓库？"
                description="Gitea 中的仓库数据将被删除，且无法恢复。"
                okText="删除"
                okButtonProps={{ danger: true }}
                onConfirm={handleDeleteRepo}
              >
                <Button danger loading={deletingRepo}>
                  删除仓库
                </Button>
              </Popconfirm>
            </div>
            <div className="flex items-center gap-2 flex-wrap p-3 bg-bg-layout rounded">
              <Typography.Text code className="text-xs">
                {repo.clone_url}
              </Typography.Text>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => handleCopyCloneUrl(repo.clone_url)}
              >
                复制
              </Button>
              <Button
                type="text"
                size="small"
                icon={<KeyOutlined />}
                loading={copyingCreds}
                onClick={handleCopyWithCredentials}
              >
                复制 HTTPS（含凭据）
              </Button>
            </div>
          </Space>
        ) : (
          <div className="flex flex-col items-center gap-3 py-4">
            <EmptyState description="尚未关联 Gitea 仓库" />
            <Button type="primary" loading={creatingRepo} onClick={handleCreateRepo}>
              创建仓库
            </Button>
          </div>
        )}
      </Card>

      <Card title="成员" className="mb-4">
        <div className="flex gap-2 mb-4 pb-4 border-b border-border">
          <Select
            showSearch
            allowClear
            placeholder="搜索用户名或昵称..."
            filterOption={false}
            onSearch={handleSearchUser}
            onChange={(v) => setSelectedUserId(v as string | undefined)}
            value={selectedUserId}
            loading={searching}
            notFoundContent={searching ? "搜索中..." : "输入用户名搜索"}
            options={userOptions}
            className="flex-1 min-w-0"
          />
          <Select
            value={newRole}
            onChange={(v) => setNewRole(v as "admin" | "member")}
            options={[
              { value: "member", label: "成员" },
              { value: "admin", label: "管理员" },
            ]}
            className="w-[110px] shrink-0"
          />
          <Button
            type="primary"
            loading={adding}
            onClick={handleAddMember}
            disabled={!selectedUserId}
          >
            添加
          </Button>
        </div>
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
