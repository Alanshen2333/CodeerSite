"use client";

import { useState } from "react";
import { Card, Form, Input, Button, Row, Col } from "antd";
import { message } from "@/lib/message";
import { changePassword, sendEmailCode } from "@/lib/api/auth";
import type { ChangePasswordInput } from "@/types/user";

interface PasswordFormValues {
  new_password: string;
  confirm_password: string;
  verification_code: string;
}

export default function PasswordChangeCard() {
  const [form] = Form.useForm<PasswordFormValues>();
  const [saving, setSaving] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const handleSendCode = async () => {
    setSendingCode(true);
    try {
      await sendEmailCode("change_password");
      message.success("验证码已发送到您的邮箱");
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "发送失败"
          : "发送失败";
      message.error(msg);
    } finally {
      setSendingCode(false);
    }
  };

  const onFinish = async (values: PasswordFormValues) => {
    setSaving(true);
    try {
      const data: ChangePasswordInput = {
        verification_code: values.verification_code,
        new_password: values.new_password,
      };
      await changePassword(data);
      message.success("密码已修改");
      form.resetFields();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "修改失败"
          : "修改失败";
      message.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card title="账号安全" className="mb-4">
      <Form<PasswordFormValues>
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Form.Item
          name="new_password"
          label="新密码"
          rules={[
            { required: true, message: "请输入新密码" },
            { min: 6, message: "密码至少 6 个字符" },
          ]}
        >
          <Input.Password placeholder="请输入新密码" size="large" />
        </Form.Item>
        <Form.Item
          name="confirm_password"
          label="确认新密码"
          dependencies={["new_password"]}
          rules={[
            { required: true, message: "请确认新密码" },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue("new_password") === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error("两次输入的密码不一致"));
              },
            }),
          ]}
        >
          <Input.Password placeholder="请再次输入新密码" size="large" />
        </Form.Item>
        <Form.Item
          name="verification_code"
          label="验证码"
          rules={[{ required: true, message: "请输入验证码" }]}
        >
          <Row gutter={16}>
            <Col flex={1}>
              <Input placeholder="请输入邮箱验证码" size="large" />
            </Col>
            <Col>
              <Button
                size="large"
                onClick={handleSendCode}
                loading={sendingCode}
                disabled={countdown > 0}
              >
                {countdown > 0 ? `${countdown}s` : "发送验证码"}
              </Button>
            </Col>
          </Row>
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={saving} size="large">
            修改密码
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}
