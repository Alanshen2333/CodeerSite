"use client";

import { Card, Tag, Space, Typography } from "antd";
import {
  BugOutlined,
  UserOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import Link from "next/link";
import type { Issue } from "@/types";
import { priorityColor, priorityLabel, issueStatusColor, issueStatusLabel } from "@/styles/constants";
import TagBadge from "@/components/qa/TagBadge";

const { Text } = Typography;

interface Props {
  issue: Issue;
  slug: string;
}

export default function IssueCard({ issue, slug }: Props) {
  return (
    <Link
      href={`/projects/${slug}/issues/${issue.issue_number}`}
      className="no-underline text-inherit"
    >
      <Card hoverable size="small" className="mb-2">
        <div className="flex justify-between items-center gap-2 flex-wrap">
          <div className="flex-1 min-w-0">
            <Space size={8}>
              <BugOutlined className="!text-text-tertiary" />
              <Text strong>#{issue.issue_number}</Text>
              <Text className="!text-sm">{issue.title}</Text>
            </Space>
          </div>
          <Space size={4} wrap>
            <Tag color={issueStatusColor[issue.status]}>
              {issueStatusLabel[issue.status]}
            </Tag>
            <Tag color={priorityColor[issue.priority]}>
              {priorityLabel[issue.priority]}
            </Tag>
            {issue.tags?.map((t) => (
              <TagBadge key={t.id} tag={t} clickable={false} />
            ))}
            {issue.assignee && (
              <Text type="secondary" className="!text-xs">
                <UserOutlined /> {issue.assignee.display_name || issue.assignee.username}
              </Text>
            )}
            <Text type="secondary" className="!text-xs">
              <ClockCircleOutlined />{" "}
              {new Date(issue.created_at).toLocaleDateString("zh-CN")}
            </Text>
          </Space>
        </div>
      </Card>
    </Link>
  );
}
