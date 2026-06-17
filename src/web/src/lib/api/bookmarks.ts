import api from "../api";
import type { Bookmark, BookmarkListResult } from "@/types";

export async function toggleBookmark(
  targetType: string,
  targetId: string
): Promise<{ bookmark?: Bookmark; message: string }> {
  const res = await api.post<{ bookmark?: Bookmark; message: string }>("/bookmarks", {
    target_type: targetType,
    target_id: targetId,
  });
  return res.data;
}

export async function getBookmarks(params?: {
  target_type?: string;
  page?: number;
  per_page?: number;
}): Promise<BookmarkListResult> {
  const res = await api.get<BookmarkListResult>("/bookmarks", { params });
  return res.data;
}

export async function checkBookmark(
  targetType: string,
  targetId: string
): Promise<boolean> {
  const res = await api.get<{ bookmarked: boolean }>("/bookmarks/check", {
    params: { target_type: targetType, target_id: targetId },
  });
  return res.data.bookmarked;
}
