"use client";

import { useState } from "react";
import { Card, Button, Tag, Typography, Space } from "antd";
import { LinkOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { getOAuthAuthorizeUrl } from "@/lib/api/auth";
import { message } from "@/lib/message";

const { Text } = Typography;

export default function GiteaBindCard() {
  const { user } = useAuth();
  const [binding, setBinding] = useState(false);

  const handleBind = async () => {
    setBinding(true);
    try {
      const { authorization_url } = await getOAuthAuthorizeUrl("bind");
      window.location.href = authorization_url;
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data
              ?.message || "获取绑定链接失败"
          : "获取绑定链接失败";
      message.error(msg);
      setBinding(false);
    }
  };

  const bound = user?.gitea_bound;

  return (
    <Card title="Gitea 账号绑定" className="mb-4">
      <Space direction="vertical" className="w-full">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <Text className="text-text font-medium">
              {bound ? "已绑定 Gitea 账号" : "未绑定 Gitea 账号"}
            </Text>
            <p className="text-text-secondary text-sm m-0 mt-1">
              {bound
                ? "你的 Codeersite 账号已关联 Gitea，可通过 Gitea 登录并使用 HTTPS 凭据克隆仓库。"
                : "绑定后可通过 Gitea 登录，并在项目设置中复制带凭据的 HTTPS clone 地址。"}
            </p>
          </div>
          {bound ? (
            <Tag icon={<CheckCircleOutlined />} color="success">
              已绑定
            </Tag>
          ) : (
            <Button
              type="primary"
              icon={<LinkOutlined />}
              loading={binding}
              onClick={handleBind}
            >
              绑定 Gitea
            </Button>
          )}
        </div>
      </Space>
    </Card>
  );
}
