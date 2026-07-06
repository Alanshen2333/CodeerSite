"use client";

import { Card, List, Button, Popconfirm, Typography, Tag } from "antd";
import { DeleteOutlined, KeyOutlined } from "@ant-design/icons";
import type { SshKey } from "@/types/user";

const { Text } = Typography;

interface SshKeyListProps {
  keys: SshKey[];
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export default function SshKeyList({ keys, onDelete, deletingId }: SshKeyListProps) {
  return (
    <Card title="SSH 公钥" className="mb-4">
      <List
        dataSource={keys}
        locale={{ emptyText: "尚未添加 SSH 公钥。" }}
        renderItem={(key) => (
          <List.Item
            actions={[
              <Popconfirm
                key="delete"
                title="删除公钥"
                description="删除后无法通过该公钥访问 Gitea 仓库，确认删除？"
                onConfirm={() => onDelete(key.id)}
                okText="删除"
                cancelText="取消"
              >
                <Button
                  danger
                  type="text"
                  icon={<DeleteOutlined />}
                  loading={deletingId === key.id}
                >
                  删除
                </Button>
              </Popconfirm>,
            ]}
          >
            <List.Item.Meta
              avatar={<KeyOutlined className="text-text-secondary text-lg" />}
              title={
                <div className="flex items-center gap-2">
                  <span className="font-medium">{key.title}</span>
                  <Tag className="text-xs">{key.key_type}</Tag>
                </div>
              }
              description={
                <div className="flex flex-col gap-1">
                  <Text className="text-text-secondary" copyable>
                    {key.fingerprint}
                  </Text>
                  <Text className="text-xs text-text-tertiary">
                    添加于 {key.created_at ? new Date(key.created_at).toLocaleString() : "-"}
                  </Text>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );
}
