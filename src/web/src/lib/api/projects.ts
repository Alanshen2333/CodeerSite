import api from "../api";
import type { Project, ProjectListResult, ProjectMember } from "@/types";

export async function getProjects(params?: {
  page?: number; per_page?: number; sort?: string; visibility?: string;
}): Promise<ProjectListResult> {
  const res = await api.get<ProjectListResult>("/projects", { params });
  return res.data;
}

export async function getProject(slug: string): Promise<{ project: Project }> {
  const res = await api.get<{ project: Project }>(`/projects/${slug}`);
  return res.data;
}

export async function createProject(data: {
  name: string; description?: string; visibility?: string;
}): Promise<{ project: Project }> {
  const res = await api.post<{ project: Project }>("/projects", data);
  return res.data;
}

export async function updateProject(slug: string, data: {
  name?: string; description?: string; visibility?: string;
}): Promise<{ project: Project }> {
  const res = await api.patch<{ project: Project }>(`/projects/${slug}`, data);
  return res.data;
}

export async function deleteProject(slug: string): Promise<void> {
  await api.delete(`/projects/${slug}`);
}

export async function getMembers(slug: string): Promise<{ members: ProjectMember[] }> {
  const res = await api.get<{ members: ProjectMember[] }>(`/projects/${slug}/members`);
  return res.data;
}

export async function addMember(slug: string, userId: string, role?: string): Promise<{ member: ProjectMember }> {
  const res = await api.post<{ member: ProjectMember }>(`/projects/${slug}/members`, { user_id: userId, role });
  return res.data;
}

export async function removeMember(slug: string, userId: string): Promise<void> {
  await api.delete(`/projects/${slug}/members/${userId}`);
}
