import api from "../api";
import type { Issue, IssueListResult } from "@/types";

export async function getIssues(slug: string, params?: {
  page?: number; per_page?: number; status?: string;
  priority?: string; assignee_id?: string; milestone_id?: string; sort?: string;
}): Promise<IssueListResult> {
  const res = await api.get<IssueListResult>(`/projects/${slug}/issues`, { params });
  return res.data;
}

export async function getIssue(slug: string, issueNumber: number): Promise<{ issue: Issue }> {
  const res = await api.get<{ issue: Issue }>(`/projects/${slug}/issues/${issueNumber}`);
  return res.data;
}

export async function createIssue(slug: string, data: {
  title: string; body?: string; assignee_id?: string;
  priority?: string; milestone_id?: string;
}): Promise<{ issue: Issue }> {
  const res = await api.post<{ issue: Issue }>(`/projects/${slug}/issues`, data);
  return res.data;
}

export async function updateIssue(slug: string, issueNumber: number, data: {
  title?: string; body?: string; assignee_id?: string | null;
  status?: string; priority?: string; milestone_id?: string | null;
}): Promise<{ issue: Issue }> {
  const res = await api.patch<{ issue: Issue }>(`/projects/${slug}/issues/${issueNumber}`, data);
  return res.data;
}

export async function deleteIssue(slug: string, issueNumber: number): Promise<void> {
  await api.delete(`/projects/${slug}/issues/${issueNumber}`);
}
