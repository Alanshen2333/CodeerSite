"use client";

import { Tag as AntTag, type TagProps } from "antd";
import Link from "next/link";

const defaultTagColor = "var(--tw-color-primary)";

interface TagBadgeProps extends TagProps {
  tag: { name: string; slug: string; color?: string };
  clickable?: boolean;
}

export default function TagBadge({ tag, clickable = true, ...props }: TagBadgeProps) {
  if (clickable) {
    return (
      <Link href={`/tags/${tag.slug}`} className="no-underline">
        <AntTag color={tag.color || defaultTagColor} {...props}>
          {tag.name}
        </AntTag>
      </Link>
    );
  }
  return (
    <AntTag color={tag.color || defaultTagColor} {...props}>
      {tag.name}
    </AntTag>
  );
}
