import api from "../api";
import type { Milestone } from "@/types";

export async function getMilestones(slug: string): Promise<{ milestones: Milestone[] }> {
  const res = await api.get<{ milestones: Milestone[] }>(`/projects/${slug}/milestones`);
  return res.data;
}

export async function createMilestone(slug: string, data: {
  title: string; description?: string; due_date?: string;
}): Promise<{ milestone: Milestone }> {
  const res = await api.post<{ milestone: Milestone }>(`/projects/${slug}/milestones`, data);
  return res.data;
}

export async function updateMilestone(slug: string, id: string, data: {
  title?: string; description?: string; due_date?: string | null; status?: string;
}): Promise<{ milestone: Milestone }> {
  const res = await api.patch<{ milestone: Milestone }>(`/projects/${slug}/milestones/${id}`, data);
  return res.data;
}

export async function deleteMilestone(slug: string, id: string): Promise<void> {
  await api.delete(`/projects/${slug}/milestones/${id}`);
}
