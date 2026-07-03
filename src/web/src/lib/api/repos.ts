import api from "../api";
import type { Repo, RepoCreateInput } from "@/types";

export async function getRepo(slug: string): Promise<{ repo: Repo }> {
  const res = await api.get<{ repo: Repo }>(`/projects/${slug}/repo`);
  return res.data;
}

export async function createRepo(
  slug: string,
  data: RepoCreateInput = {},
): Promise<{ repo: Repo }> {
  const res = await api.post<{ repo: Repo }>(`/projects/${slug}/repo`, data);
  return res.data;
}

export async function deleteRepo(slug: string): Promise<void> {
  await api.delete(`/projects/${slug}/repo`);
}
