"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, Row, Col } from "antd";
import { getTags } from "@/lib/api/tags";
import type { Tag } from "@/types";
import TagBadge from "@/components/qa/TagBadge";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";

export default function TagsPage() {
  const router = useRouter();
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const result = await getTags({ sort: "popular", per_page: 100 });
        setTags(result.tags);
      } catch {
        setTags([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <PageContainer size="wide">
        <LoadingState />
      </PageContainer>
    );
  }

  return (
    <PageContainer size="wide">
      <h2 className="text-xl font-semibold text-text mb-6">标签</h2>

      {tags.length === 0 ? (
        <EmptyState description="暂无标签" />
      ) : (
        <Row gutter={[12, 12]}>
          {tags.map((tag) => (
            <Col key={tag.id}>
              <Card
                hoverable
                size="small"
                className="min-w-[160px] text-center cursor-pointer"
                onClick={() => router.push(`/tags/${tag.slug}`)}
              >
                <TagBadge tag={tag} clickable={false} className="mb-2" />
                <div className="text-xs text-text-tertiary">
                  {tag.usage_count} 个问题
                </div>
                {tag.description && (
                  <div className="text-xs text-text-secondary mt-1">
                    {tag.description}
                  </div>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </PageContainer>
  );
}
