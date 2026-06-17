import api from "../api";
import type {
  Question,
  QuestionListResult,
  QuestionCreateInput,
} from "@/types";

export async function getQuestions(params?: {
  page?: number;
  per_page?: number;
  sort?: string;
  tag?: string;
  filter?: string;
}): Promise<QuestionListResult> {
  const res = await api.get<QuestionListResult>("/questions", { params });
  return res.data;
}

export async function getQuestion(id: string): Promise<{ question: Question }> {
  const res = await api.get<{ question: Question }>(`/questions/${id}`);
  return res.data;
}

export async function createQuestion(
  data: QuestionCreateInput
): Promise<{ question: Question }> {
  const res = await api.post<{ question: Question }>("/questions", data);
  return res.data;
}

export async function updateQuestion(
  id: string,
  data: { title?: string; body?: string; tag_ids?: string[] }
): Promise<{ question: Question }> {
  const res = await api.patch<{ question: Question }>(`/questions/${id}`, data);
  return res.data;
}

export async function deleteQuestion(id: string): Promise<void> {
  await api.delete(`/questions/${id}`);
}

export async function closeQuestion(id: string): Promise<{ question: Question }> {
  const res = await api.post<{ question: Question }>(`/questions/${id}/close`);
  return res.data;
}

export async function reopenQuestion(id: string): Promise<{ question: Question }> {
  const res = await api.post<{ question: Question }>(`/questions/${id}/reopen`);
  return res.data;
}

export async function togglePinQuestion(id: string): Promise<{ question: Question }> {
  const res = await api.post<{ question: Question }>(`/questions/${id}/pin`);
  return res.data;
}
