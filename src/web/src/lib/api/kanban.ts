import api from "../api";
import type { KanbanColumn, KanbanCard } from "@/types";

export async function getColumns(slug: string): Promise<{ columns: KanbanColumn[] }> {
  const res = await api.get<{ columns: KanbanColumn[] }>(`/projects/${slug}/kanban/columns`);
  return res.data;
}

export async function createColumn(slug: string, title: string): Promise<{ column: KanbanColumn }> {
  const res = await api.post<{ column: KanbanColumn }>(`/projects/${slug}/kanban/columns`, { title });
  return res.data;
}

export async function deleteColumn(slug: string, columnId: string): Promise<void> {
  await api.delete(`/projects/${slug}/kanban/columns/${columnId}`);
}

export async function createCard(slug: string, columnId: string, data: {
  title: string; issue_id?: string;
}): Promise<{ card: KanbanCard }> {
  const res = await api.post<{ card: KanbanCard }>(`/projects/${slug}/kanban/columns/${columnId}/cards`, data);
  return res.data;
}

export async function deleteCard(slug: string, cardId: string): Promise<void> {
  await api.delete(`/projects/${slug}/kanban/cards/${cardId}`);
}

export async function moveCard(slug: string, cardId: string, data: {
  column_id: string; position: number;
}): Promise<{ card: KanbanCard }> {
  const res = await api.post<{ card: KanbanCard }>(`/projects/${slug}/kanban/cards/${cardId}/move`, data);
  return res.data;
}
