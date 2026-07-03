"use client";

import { Select } from "antd";
import { BranchesOutlined } from "@ant-design/icons";
import type { Branch } from "@/types";

interface BranchSelectorProps {
  branches: Branch[];
  value: string;
  onChange: (value: string) => void;
  loading?: boolean;
}

export default function BranchSelector({ branches, value, onChange, loading }: BranchSelectorProps) {
  return (
    <Select
      showSearch
      loading={loading}
      value={value}
      onChange={onChange}
      prefix={<BranchesOutlined />}
      placeholder="选择分支"
      optionFilterProp="children"
      className="min-w-[180px]"
      options={branches.map((b) => ({ label: b.name, value: b.name }))}
    />
  );
}
