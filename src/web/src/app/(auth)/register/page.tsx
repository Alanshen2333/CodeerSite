"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, Form, Input, Button, Typography, message, Space } from "antd";
import { UserOutlined, MailOutlined, LockOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import type { RegisterInput } from "@/types/user";

const { Title, Text } = Typography;

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  const onFinish = async (values: RegisterInput) => {
    setLoading(true);
    try {
      await register(values);
      messageApi.success("注册成功！欢迎加入 Codeersite！");
      router.push("/");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "注册失败"
          : "注册失败";
      messageApi.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-[calc(100vh-56px)] bg-bg-layout">
      {contextHolder}
      <Card className="w-[420px] shadow-sm">
        <div className="text-center mb-6">
          <Title level={3} className="!mb-2">
            加入 Codeersite
          </Title>
          <Text type="secondary">创建账号，开始你的开发者社区之旅</Text>
        </div>

        <Form layout="vertical" onFinish={onFinish} autoComplete="off">
          <Form.Item
            name="username"
            rules={[
              { required: true, message: "请输入用户名" },
              { min: 3, message: "用户名至少 3 个字符" },
              { max: 50, message: "用户名不能超过 50 个字符" },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" size="large" />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: "请输入邮箱" },
              { type: "email", message: "请输入有效的邮箱地址" },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: "请输入密码" },
              { min: 6, message: "密码至少 6 个字符" },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
          </Form.Item>

          <Form.Item name="display_name">
            <Input prefix={<UserOutlined />} placeholder="显示名称（选填）" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              注册
            </Button>
          </Form.Item>
        </Form>

        <div className="text-center">
          <Space>
            <Text>已有账号？</Text>
            <Link href="/login">立即登录</Link>
          </Space>
        </div>
      </Card>
    </div>
  );
}
