"use client";

import { useState } from "react";
import { Card, Form, Input, Button } from "antd";
import { message } from "@/lib/message";
import { useAuth } from "@/providers/AuthProvider";
import type { UpdateProfileInput } from "@/types/user";

const { TextArea } = Input;

interface ProfileFormValues {
  display_name?: string;
  bio?: string;
  website?: string;
  location?: string;
}

export default function ProfileFormCard() {
  const { user, updateUser } = useAuth();
  const [form] = Form.useForm<ProfileFormValues>();
  const [saving, setSaving] = useState(false);

  const onFinish = async (values: ProfileFormValues) => {
    setSaving(true);
    try {
      const data: UpdateProfileInput = {
        display_name: values.display_name ?? undefined,
        bio: values.bio ?? undefined,
        website: values.website ?? undefined,
        location: values.location ?? undefined,
      };
      await updateUser(data);
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

  return (
    <Card title="个人资料" className="mb-4">
      <Form<ProfileFormValues>
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          display_name: user?.display_name || "",
          bio: user?.bio || "",
          website: user?.website || "",
          location: user?.location || "",
        }}
      >
        <Form.Item
          name="display_name"
          label="昵称"
          rules={[{ max: 100, message: "昵称不能超过 100 个字符" }]}
        >
          <Input placeholder="显示昵称" size="large" />
        </Form.Item>
        <Form.Item
          name="bio"
          label="个人简介"
          rules={[{ max: 500, message: "简介不能超过 500 个字符" }]}
        >
          <TextArea rows={4} placeholder="简单介绍一下自己..." />
        </Form.Item>
        <Form.Item
          name="website"
          label="个人网站"
          rules={[{ type: "url", message: "请输入有效的 URL" }]}
        >
          <Input placeholder="https://example.com" size="large" />
        </Form.Item>
        <Form.Item
          name="location"
          label="所在地"
          rules={[{ max: 100, message: "所在地不能超过 100 个字符" }]}
        >
          <Input placeholder="城市或地区" size="large" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={saving} size="large">
            保存
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}
