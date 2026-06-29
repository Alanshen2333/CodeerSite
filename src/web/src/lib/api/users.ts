import api from "../api";
import type { UserProfile, PublicUser, QuestionListResult } from "@/types";

export async function getUser(username: string): Promise<{
  user: UserProfile;
  stats: {
    question_count: number;
    answer_count: number;
    accepted_count: number;
    project_count: number;
  };
}> {
  const res = await api.get(`/users/${username}`);
  return res.data;
}

export async function getUserQuestions(
  username: string,
  params?: { page?: number; per_page?: number }
): Promise<QuestionListResult> {
  const res = await api.get<QuestionListResult>(`/users/${username}/questions`, { params });
  return res.data;
}

export async function getUserAnswers(
  username: string,
  params?: { page?: number; per_page?: number }
): Promise<{ answers: { id: string; question_id: string; body: string; body_html?: string; is_accepted: boolean; created_at: string }[]; total: number; page: number; pages: number }> {
  const res = await api.get(`/users/${username}/answers`, { params });
  return res.data;
}

export async function searchUsers(
  q: string,
  per_page = 10,
): Promise<{ users: PublicUser[]; total: number; page: number; pages: number }> {
  const res = await api.get<{
    users: PublicUser[];
    total: number;
    page: number;
    pages: number;
  }>("/users", { params: { q, per_page } });
  return res.data;
}
