import api from "../api";
import type {
  Comment,
  CommentListResult,
  CommentCreateInput,
} from "@/types";

export async function getComments(params: {
  target_type: string;
  target_id: string;
  page?: number;
  per_page?: number;
}): Promise<CommentListResult> {
  const res = await api.get<CommentListResult>("/comments", { params });
  return res.data;
}

export async function createComment(
  data: CommentCreateInput
): Promise<{ comment: Comment }> {
  const res = await api.post<{ comment: Comment }>("/comments", data);
  return res.data;
}

export async function updateComment(
  id: string,
  body: string
): Promise<{ comment: Comment }> {
  const res = await api.patch<{ comment: Comment }>(`/comments/${id}`, { body });
  return res.data;
}

export async function deleteComment(id: string): Promise<void> {
  await api.delete(`/comments/${id}`);
}
