"use client";

import { useState } from "react";
import { Select, Space } from "antd";
import type { Tag } from "@/types";
import { searchTags } from "@/lib/api/tags";
import TagBadge from "./TagBadge";

interface TagSelectProps {
  value?: string[];
  onChange?: (value: string[]) => void;
}

export default function TagSelect({ value = [], onChange }: TagSelectProps) {
  const [options, setOptions] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (q: string) => {
    if (!q || q.length < 1) {
      setOptions([]);
      return;
    }
    setLoading(true);
    try {
      const tags = await searchTags(q);
      setOptions(tags);
    } catch {
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Select
      mode="multiple"
      value={value}
      onChange={onChange}
      onSearch={handleSearch}
      loading={loading}
      filterOption={false}
      placeholder="搜索并选择标签（最多5个）"
      maxCount={5}
      className="w-full"
      notFoundContent={null}
      options={options.map((tag) => ({
        label: (
          <Space>
            <TagBadge tag={tag} clickable={false} />
            <span className="text-text-tertiary text-xs">
              {tag.usage_count} 个问题
            </span>
          </Space>
        ),
        value: tag.id,
      }))}
    />
  );
}
