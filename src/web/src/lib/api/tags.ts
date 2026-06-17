import api from "../api";
import type { Tag, TagListResult } from "@/types";

export async function getTags(params?: {
  sort?: string;
  page?: number;
  per_page?: number;
  q?: string;
}): Promise<TagListResult> {
  const res = await api.get<TagListResult>("/tags", { params });
  return res.data;
}

export async function getTag(slug: string): Promise<{ tag: Tag }> {
  const res = await api.get<{ tag: Tag }>(`/tags/${slug}`);
  return res.data;
}

export async function searchTags(q: string, limit: number = 10): Promise<Tag[]> {
  // Search via tags endpoint with q parameter returns a plain array
  const res = await api.get<TagListResult>("/tags", {
    params: { q, per_page: limit },
  });
  return res.data.tags;
}
