"use client";

import { useState } from "react";
import { Form, Input, Button } from "antd";
import { message } from "@/lib/message";
import { createSshKey } from "@/lib/api/ssh-keys";
import type { CreateSshKeyInput } from "@/types/user";

const { TextArea } = Input;

interface AddSshKeyFormProps {
  onSuccess: () => void;
}

export default function AddSshKeyForm({ onSuccess }: AddSshKeyFormProps) {
  const [form] = Form.useForm<CreateSshKeyInput>();
  const [submitting, setSubmitting] = useState(false);

  const onFinish = async (values: CreateSshKeyInput) => {
    setSubmitting(true);
    try {
      await createSshKey({
        title: values.title.trim(),
        public_key: values.public_key.trim(),
      });
      message.success("SSH 公钥已添加并同步到 Gitea");
      form.resetFields();
      onSuccess();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "添加失败"
          : "添加失败";
      message.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Form<CreateSshKeyInput>
      form={form}
      layout="vertical"
      onFinish={onFinish}
    >
      <Form.Item
        name="title"
        label="标题"
        rules={[{ required: true, message: "请输入公钥标题（如 MacBook Pro）" }]}
      >
        <Input placeholder="用于识别这把密钥的设备名称" size="large" />
      </Form.Item>
      <Form.Item
        name="public_key"
        label="公钥内容"
        rules={[{ required: true, message: "请粘贴 OpenSSH 格式公钥" }]}
      >
        <TextArea
          rows={5}
          placeholder="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID..."
        />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" loading={submitting} size="large">
          添加公钥
        </Button>
      </Form.Item>
    </Form>
  );
}
