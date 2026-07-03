import api from "../api";
import type {
  Repo,
  RepoCreateInput,
  Branch,
  TreeEntry,
  Blob,
  Commit,
} from "@/types";

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

export async function listBranches(slug: string): Promise<{ branches: Branch[] }> {
  const res = await api.get<{ branches: Branch[] }>(`/projects/${slug}/repo/branches`);
  return res.data;
}

export async function getTree(
  slug: string,
  params: { ref?: string; path?: string } = {},
): Promise<{ tree: TreeEntry[]; ref: string; path: string }> {
  const res = await api.get<{ tree: TreeEntry[]; ref: string; path: string }>(
    `/projects/${slug}/repo/tree`,
    { params },
  );
  return res.data;
}

export async function getBlob(
  slug: string,
  params: { ref?: string; path: string },
): Promise<{ blob: Blob }> {
  const res = await api.get<{ blob: Blob }>(`/projects/${slug}/repo/blob`, {
    params,
  });
  return res.data;
}

export async function listCommits(
  slug: string,
  params: { ref?: string; page?: number; per_page?: number } = {},
): Promise<{ commits: Commit[]; page: number; per_page: number; ref: string }> {
  const res = await api.get<{
    commits: Commit[];
    page: number;
    per_page: number;
    ref: string;
  }>(`/projects/${slug}/repo/commits`, { params });
  return res.data;
}
