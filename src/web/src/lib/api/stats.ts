import api from "../api";

export interface SiteStats {
  questions: number;
  answers: number;
  projects: number;
  users: number;
}

export async function getStats(): Promise<SiteStats> {
  const res = await api.get<SiteStats>("/stats");
  return res.data;
}
