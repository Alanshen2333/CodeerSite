"use client";

import { useState } from "react";
import { Input, Button, Space } from "antd";

interface CommentFormProps {
  targetType: string;
  targetId: string;
  onSubmit: (body: string) => Promise<void>;
}

export default function CommentForm({ targetType, targetId, onSubmit }: CommentFormProps) {
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!body.trim()) return;
    setLoading(true);
    try {
      await onSubmit(body.trim());
      setBody("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space.Compact className="w-full mt-2">
      <Input
        placeholder="添加评论..."
        value={body}
        onChange={(e) => setBody(e.target.value)}
        onPressEnter={handleSubmit}
        maxLength={1000}
      />
      <Button
        type="primary"
        loading={loading}
        onClick={handleSubmit}
        disabled={!body.trim()}
      >
        评论
      </Button>
    </Space.Compact>
  );
}
