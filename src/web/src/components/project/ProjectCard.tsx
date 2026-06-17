"use client";

import { Card, Typography, Space, Tag } from "antd";
import { TeamOutlined, BugOutlined, StarOutlined } from "@ant-design/icons";
import Link from "next/link";
import type { Project } from "@/types";

const { Text, Paragraph } = Typography;

interface Props {
  project: Project;
}

export default function ProjectCard({ project }: Props) {
  return (
    <Link href={`/projects/${project.slug}`} className="no-underline">
      <Card hoverable className="mb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1 min-w-0">
            <Space size={8} className="mb-1">
              <Text strong className="!text-base">{project.name}</Text>
              <Tag color={project.visibility === "public" ? "green" : "orange"}>
                {project.visibility === "public" ? "公开" : "私有"}
              </Tag>
            </Space>
            {project.description && (
              <Paragraph
                type="secondary"
                ellipsis={{ rows: 2 }}
                className="!mb-2 !text-xs"
              >
                {project.description}
              </Paragraph>
            )}
            <Space size={16}>
              <Text type="secondary" className="!text-xs">
                <TeamOutlined /> {project.members_count} 成员
              </Text>
              <Text type="secondary" className="!text-xs">
                <BugOutlined /> {project.issues_count} Issue
              </Text>
              <Text type="secondary" className="!text-xs">
                <StarOutlined /> {project.star_count}
              </Text>
              {project.owner && (
                <Text type="secondary" className="!text-xs">
                  {project.owner.display_name || project.owner.username}
                </Text>
              )}
            </Space>
          </div>
        </div>
      </Card>
    </Link>
  );
}
