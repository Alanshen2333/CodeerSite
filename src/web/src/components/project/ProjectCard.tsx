"use client";

import { useState, type MouseEvent } from "react";
import { Card, Typography, Space, Tag, message } from "antd";
import { TeamOutlined, BugOutlined, StarOutlined, StarFilled } from "@ant-design/icons";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import { toggleProjectStar } from "@/lib/api/projects";
import type { Project } from "@/types";

const { Text, Paragraph } = Typography;

interface Props {
  project: Project;
}

export default function ProjectCard({ project }: Props) {
  const router = useRouter();
  const { user } = useAuth();
  const [starred, setStarred] = useState<boolean>(project.starred ?? false);
  const [count, setCount] = useState<number>(project.star_count);
  const [toggling, setToggling] = useState(false);

  const handleToggleStar = async (e: MouseEvent) => {
    // 卡片整体是 Link，需阻断跳转
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      router.push("/login");
      return;
    }
    const prev = { starred, count };
    // 乐观更新：旧值 starred 决定本次是 +1 还是 -1
    setStarred(!starred);
    setCount((c) => c + (starred ? -1 : 1));
    setToggling(true);
    try {
      const r = await toggleProjectStar(project.slug);
      setStarred(r.starred);
      setCount(r.star_count);
    } catch (err: unknown) {
      setStarred(prev.starred);
      setCount(prev.count);
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "操作失败"
          : "操作失败";
      message.error(msg);
    } finally {
      setToggling(false);
    }
  };

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
              <button
                type="button"
                onClick={handleToggleStar}
                disabled={toggling}
                className="inline-flex items-center gap-1 text-xs text-text-secondary hover:text-primary disabled:opacity-50 cursor-pointer"
                aria-label={starred ? "取消 Star" : "Star"}
                title={user ? (starred ? "取消 Star" : "Star") : "登录后可 Star"}
              >
                {starred ? <StarFilled className="text-primary" /> : <StarOutlined />}
                {count}
              </button>
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
