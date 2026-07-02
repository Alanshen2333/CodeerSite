"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  ColorPicker,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
} from "antd";
import { message } from "@/lib/message";
import { PlusOutlined, ArrowLeftOutlined, DeleteOutlined } from "@ant-design/icons";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import PageContainer from "@/components/layout/PageContainer";
import PageHeader from "@/components/layout/PageHeader";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import {
  getAdminBadges,
  createBadge,
  updateBadge,
  deleteBadge,
  getBadgeRecipients,
  awardBadge,
  revokeBadge,
} from "@/lib/api/badges";
import { searchUsers } from "@/lib/api/users";
import { colors } from "@/styles/tokens";
import type { Badge, UserBadge, PublicUser } from "@/types";

const { TextArea } = Input;

interface BadgeFormValues {
  name: string;
  description?: string;
  icon?: string;
  color: string;
}

/** 渲染徽章图标 + 名称（图标缺失时用首字兜底）。 */
function BadgeLabel({ badge }: { badge: Badge }) {
  const glyph = badge.icon?.trim() || badge.name.slice(0, 1);
  return (
    <Space>
      <span
        className="inline-flex items-center justify-center rounded-full text-sm font-semibold"
        style={{ width: 28, height: 28, color: badge.color, border: `1px solid ${badge.color}` }}
      >
        {glyph}
      </span>
      <span className="font-medium text-text">{badge.name}</span>
    </Space>
  );
}

export default function BadgeAdminPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Badge | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm<BadgeFormValues>();

  // 获得者抽屉状态
  const [recipientsBadge, setRecipientsBadge] = useState<Badge | null>(null);
  const [recipients, setRecipients] = useState<UserBadge[]>([]);
  const [recipientsLoading, setRecipientsLoading] = useState(false);
  const [userOptions, setUserOptions] = useState<{ value: string; label: string }[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | undefined>();
  const [awardReason, setAwardReason] = useState<string>("");
  const [awarding, setAwarding] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setBadges(await getAdminBadges());
    } catch {
      setBadges([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user || user.role !== "admin") {
      router.push("/");
      return;
    }
    load();
  }, [load, user, router]);

  if (!user || user.role !== "admin") return null;

  // ── 新建 / 编辑 ──────────────────────────────────────
  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ color: colors.primary });
    setModalOpen(true);
  };

  const openEdit = (badge: Badge) => {
    setEditing(badge);
    form.setFieldsValue({
      name: badge.name,
      description: badge.description || "",
      icon: badge.icon || "",
      color: badge.color,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editing) {
        await updateBadge(editing.id, values);
        message.success("徽章已更新");
      } else {
        await createBadge(values);
        message.success("徽章已创建");
      }
      setModalOpen(false);
      load();
    } catch (e: unknown) {
      // antd 校验失败会抛 ValidationError，跳过；其余展示后端错误
      const err = e as { response?: { data?: { message?: string } } };
      const msg = err?.response?.data?.message;
      if (msg) message.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (badge: Badge) => {
    try {
      await deleteBadge(badge.id);
      message.success("徽章已删除");
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } };
      message.error(err?.response?.data?.message || "删除失败");
    }
  };

  // ── 发放 / 撤销 ──────────────────────────────────────
  const openRecipients = async (badge: Badge) => {
    setRecipientsBadge(badge);
    setSelectedUserId(undefined);
    setAwardReason("");
    setUserOptions([]);
    setRecipients([]);
    setRecipientsLoading(true);
    try {
      setRecipients(await getBadgeRecipients(badge.id));
    } catch {
      setRecipients([]);
    } finally {
      setRecipientsLoading(false);
    }
  };

  const handleSearchUsers = async (q: string) => {
    if (!q.trim()) {
      setUserOptions([]);
      return;
    }
    setSearching(true);
    try {
      const res = await searchUsers(q, 10);
      setUserOptions(
        res.users.map((u: PublicUser) => ({
          value: u.id,
          label: u.display_name ? `${u.username}（${u.display_name}）` : u.username,
        })),
      );
    } catch {
      setUserOptions([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAward = async () => {
    if (!recipientsBadge || !selectedUserId) return;
    setAwarding(true);
    try {
      await awardBadge(recipientsBadge.id, selectedUserId, awardReason || undefined);
      message.success("徽章已发放");
      setSelectedUserId(undefined);
      setAwardReason("");
      setUserOptions([]);
      setRecipients(await getBadgeRecipients(recipientsBadge.id));
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } };
      message.error(err?.response?.data?.message || "发放失败");
    } finally {
      setAwarding(false);
    }
  };

  const handleRevoke = async (ub: UserBadge) => {
    if (!recipientsBadge) return;
    try {
      await revokeBadge(recipientsBadge.id, ub.user_id);
      message.success("已撤销");
      setRecipients(await getBadgeRecipients(recipientsBadge.id));
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } };
      message.error(err?.response?.data?.message || "撤销失败");
    }
  };

  const columns = [
    {
      title: "徽章",
      key: "badge",
      render: (_: unknown, record: Badge) => <BadgeLabel badge={record} />,
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      render: (d: string | null) => d || <span className="text-text-tertiary">—</span>,
    },
    {
      title: "颜色",
      dataIndex: "color",
      key: "color",
      render: (c: string) => (
        <Space>
          <span
            className="inline-block rounded-full"
            style={{ width: 16, height: 16, backgroundColor: c }}
          />
          <code className="text-xs text-text-secondary">{c}</code>
        </Space>
      ),
    },
    {
      title: "类型",
      dataIndex: "kind",
      key: "kind",
      render: (k: string) => <Tag>{k}</Tag>,
    },
    {
      title: "操作",
      key: "actions",
      render: (_: unknown, record: Badge) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>编辑</Button>
          <Button size="small" onClick={() => openRecipients(record)}>获得者</Button>
          <Popconfirm title="删除此徽章？连同发放关系一并移除。" onConfirm={() => handleDelete(record)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const recipientColumns = [
    {
      title: "用户 ID",
      dataIndex: "user_id",
      key: "user_id",
      render: (id: string) => <code className="text-xs text-text-secondary">{id.slice(0, 8)}</code>,
    },
    {
      title: "颁发人",
      dataIndex: "awarded_by",
      key: "awarded_by",
      render: (id: string | null) =>
        id ? <code className="text-xs text-text-secondary">{id.slice(0, 8)}</code> : <span className="text-text-tertiary">—</span>,
    },
    {
      title: "原因",
      dataIndex: "reason",
      key: "reason",
      render: (r: string | null) => r || <span className="text-text-tertiary">—</span>,
    },
    {
      title: "颁发时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (t: string) => new Date(t).toLocaleString(),
    },
    {
      title: "操作",
      key: "actions",
      render: (_: unknown, record: UserBadge) => (
        <Popconfirm title="撤销该用户的徽章？" onConfirm={() => handleRevoke(record)}>
          <Button size="small" danger>撤销</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <PageContainer size="wide">
      <PageHeader
        title="徽章管理"
        subtitle="创建自定义徽章并向用户发放或撤销"
        breadcrumb={[{ label: "管理", href: "/admin" }, { label: "徽章" }]}
        actions={
          <Space>
            <Link href="/admin">
              <Button icon={<ArrowLeftOutlined />}>返回管理</Button>
            </Link>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              新建徽章
            </Button>
          </Space>
        }
      />

      <Card>
        {loading ? (
          <LoadingState />
        ) : badges.length === 0 ? (
          <EmptyState description="还没有徽章，点击「新建徽章」创建" />
        ) : (
          <Table
            dataSource={badges}
            columns={columns}
            rowKey="id"
            pagination={false}
            size="middle"
          />
        )}
      </Card>

      {/* 新建 / 编辑 Modal */}
      <Modal
        title={editing ? "编辑徽章" : "新建徽章"}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        confirmLoading={saving}
        okText="保存"
        cancelText="取消"
        destroyOnHidden
      >
        <Form<BadgeFormValues> form={form} layout="vertical" className="mt-4">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: "请输入徽章名称" }, { max: 50 }]}
          >
            <Input placeholder="如：杰出贡献者" />
          </Form.Item>
          <Form.Item name="description" label="描述" rules={[{ max: 500 }]}>
            <TextArea rows={3} placeholder="徽章含义说明" />
          </Form.Item>
          <Form.Item name="icon" label="图标" rules={[{ max: 20 }]}>
            <Input placeholder="emoji 或单字符，如 🏆" />
          </Form.Item>
          <Form.Item name="color" label="颜色" rules={[{ required: true, message: "请选择颜色" }]}>
            <ColorPicker showText format="hex" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 获得者管理 Modal */}
      <Modal
        title={recipientsBadge ? `「${recipientsBadge.name}」获得者` : "获得者"}
        open={!!recipientsBadge}
        onCancel={() => setRecipientsBadge(null)}
        footer={null}
        width={680}
        destroyOnHidden
      >
        {recipientsBadge && (
          <div className="space-y-4">
            <div className="rounded-lg border border-border p-4 bg-bg-layout">
              <div className="mb-2 text-sm font-medium text-text">发放徽章</div>
              <Space wrap className="w-full">
                <Select
                  showSearch
                  placeholder="搜索用户名 / 昵称"
                  style={{ minWidth: 240 }}
                  filterOption={false}
                  onSearch={handleSearchUsers}
                  loading={searching}
                  options={userOptions}
                  value={selectedUserId}
                  onChange={setSelectedUserId}
                  notFoundContent={searching ? "搜索中…" : "无匹配用户"}
                />
                <Input
                  placeholder="颁发原因（可选）"
                  style={{ width: 220 }}
                  value={awardReason}
                  onChange={(e) => setAwardReason(e.target.value)}
                  maxLength={500}
                />
                <Button type="primary" loading={awarding} disabled={!selectedUserId} onClick={handleAward}>
                  发放
                </Button>
              </Space>
            </div>

            <div>
              <div className="mb-2 text-sm font-medium text-text">当前获得者</div>
              {recipientsLoading ? (
                <LoadingState />
              ) : recipients.length === 0 ? (
                <EmptyState description="暂无获得者" />
              ) : (
                <Table
                  dataSource={recipients}
                  columns={recipientColumns}
                  rowKey="id"
                  pagination={false}
                  size="small"
                />
              )}
            </div>
          </div>
        )}
      </Modal>
    </PageContainer>
  );
}
