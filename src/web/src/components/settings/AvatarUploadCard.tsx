"use client";

import { useState } from "react";
import { Card, Upload, Button, Space, Typography } from "antd";
import { UploadOutlined, UserOutlined } from "@ant-design/icons";
import { message } from "@/lib/message";
import { useAuth } from "@/providers/AuthProvider";
import { uploadAvatar } from "@/lib/api/auth";
import type { UploadChangeParam, UploadFile, UploadProps } from "antd/es/upload/interface";

const { Text } = Typography;

export default function AvatarUploadCard() {
  const { user, refreshUser } = useAuth();
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await uploadAvatar(file);
      await refreshUser();
      message.success("头像已更新");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "上传失败"
          : "上传失败";
      message.error(msg);
    } finally {
      setUploading(false);
    }
    return false; // 阻止 Upload 默认上传行为
  };

  const uploadProps: UploadProps = {
    name: "file",
    showUploadList: false,
    accept: "image/*",
    beforeUpload: handleUpload,
    customRequest: () => {}, // 禁用默认上传
  };

  return (
    <Card title="头像" className="mb-4">
      <Space size="large" className="items-center">
        <div className="w-24 h-24 rounded-full bg-bg-layout flex items-center justify-center overflow-hidden">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
          ) : (
            <UserOutlined className="text-4xl text-text-secondary" />
          )}
        </div>
        <div className="flex flex-col gap-2">
          <Text className="text-text-secondary">上传新头像，支持 JPG、PNG 格式</Text>
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />} loading={uploading}>
              选择文件
            </Button>
          </Upload>
        </div>
      </Space>
    </Card>
  );
}
