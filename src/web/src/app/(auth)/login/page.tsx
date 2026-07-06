"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, Form, Input, Button, Typography, message, Space, Divider } from "antd";
import { MailOutlined, LockOutlined, LoginOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getOAuthAuthorizeUrl } from "@/lib/api/auth";
import type { LoginInput } from "@/types/user";

const { Title, Text } = Typography;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [giteaLoading, setGiteaLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  const onFinish = async (values: LoginInput) => {
    setLoading(true);
    try {
      await login(values);
      messageApi.success("登录成功！");
      router.push("/");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "登录失败"
          : "登录失败";
      messageApi.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGiteaLogin = async () => {
    setGiteaLoading(true);
    try {
      const { authorization_url } = await getOAuthAuthorizeUrl("login");
      window.location.href = authorization_url;
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "获取 Gitea 授权链接失败"
          : "获取 Gitea 授权链接失败";
      messageApi.error(msg);
      setGiteaLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-[calc(100vh-56px)] bg-bg-layout">
      {contextHolder}
      <Card className="w-[400px] shadow-sm">
        <div className="text-center mb-6">
          <Title level={3} className="!mb-2">
            欢迎回来
          </Title>
          <Text type="secondary">登录 Codeersite 开发者社区</Text>
        </div>

        <Form layout="vertical" onFinish={onFinish} autoComplete="off">
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
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              登录
            </Button>
          </Form.Item>
        </Form>

        <Divider className="my-4">或</Divider>

        <Button
          block
          size="large"
          icon={<LoginOutlined />}
          loading={giteaLoading}
          onClick={handleGiteaLogin}
        >
          使用 Gitea 登录
        </Button>

        <div className="text-center mt-4">
          <Space>
            <Text>还没有账号？</Text>
            <Link href="/register">立即注册</Link>
          </Space>
        </div>
      </Card>
    </div>
  );
}
