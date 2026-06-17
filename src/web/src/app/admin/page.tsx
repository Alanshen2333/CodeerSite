"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { Card, Table, Button, Tag, Space, Statistic, Row, Col, Popconfirm, message, Select } from "antd";
import { UserOutlined, QuestionCircleOutlined, ProjectOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import { getAdminStats, getAdminUsers, updateUser, deleteUser } from "@/lib/api/admin";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import ListPagination from "@/components/ui/ListPagination";

function AdminContent() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<Record<string, number>>({});
  const [users, setUsers] = useState<Record<string, unknown>[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const [s, u] = await Promise.all([
        getAdminStats(),
        getAdminUsers({ page, per_page: 20 }),
      ]);
      setStats(s);
      setUsers(u.users);
      setTotal(u.total);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    if (!user || user.role !== "admin") {
      router.push("/");
      return;
    }
    fetch();
  }, [fetch, user, router]);

  const handleRoleChange = async (userId: string, role: string) => {
    await updateUser(userId, { role });
    message.success("角色已更新");
    fetch();
  };

  const handleToggleActive = async (userId: string, isActive: boolean) => {
    await updateUser(userId, { is_active: !isActive });
    message.success(isActive ? "用户已禁用" : "用户已启用");
    fetch();
  };

  const handleDelete = async (userId: string) => {
    await deleteUser(userId);
    message.success("用户已删除");
    fetch();
  };

  if (!user || user.role !== "admin") return null;

  const columns = [
    { title: "用户名", dataIndex: "username", key: "username" },
    { title: "邮箱", dataIndex: "email", key: "email" },
    {
      title: "角色",
      dataIndex: "role",
      key: "role",
      render: (role: string, record: Record<string, unknown>) => (
        <Select
          value={role}
          size="small"
          style={{ width: 100 }}
          onChange={(v) => handleRoleChange(record.id as string, v)}
        >
          <Select.Option value="user">用户</Select.Option>
          <Select.Option value="moderator">版主</Select.Option>
          <Select.Option value="admin">管理员</Select.Option>
        </Select>
      ),
    },
    { title: "声望", dataIndex: "reputation", key: "reputation" },
    {
      title: "状态",
      dataIndex: "is_active",
      key: "is_active",
      render: (active: boolean) => (
        <Tag color={active ? "green" : "red"}>{active ? "正常" : "禁用"}</Tag>
      ),
    },
    {
      title: "操作",
      key: "actions",
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space>
          <Button
            size="small"
            danger={!!record.is_active}
            onClick={() => handleToggleActive(record.id as string, record.is_active as boolean)}
          >
            {record.is_active ? "禁用" : "启用"}
          </Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id as string)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <PageContainer size="wide">
      <h2 className="text-xl font-semibold text-text mb-6">管理面板</h2>

      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card>
            <Statistic title="用户" value={stats.users} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="问题" value={stats.questions} prefix={<QuestionCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="回答" value={stats.answers} prefix={<ProjectOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="项目" value={stats.projects} prefix={<ProjectOutlined />} />
          </Card>
        </Col>
      </Row>

      <Card title="用户管理" className="mb-6">
        {loading ? (
          <LoadingState />
        ) : (
          <>
            <Table
              dataSource={users}
              columns={columns}
              rowKey="id"
              pagination={false}
              size="middle"
            />
            <ListPagination current={page} total={total} pageSize={20} onChange={setPage} />
          </>
        )}
      </Card>
    </PageContainer>
  );
}

export default function AdminPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <AdminContent />
    </Suspense>
  );
}
