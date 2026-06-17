import api from "../api";
import type { SearchResult } from "@/types";

export async function search(params: {
  q: string;
  type?: string;
  page?: number;
  per_page?: number;
}): Promise<SearchResult> {
  const res = await api.get<SearchResult>("/search", { params });
  return res.data;
}
