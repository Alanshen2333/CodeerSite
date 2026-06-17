import api from "../api";
import type {
  Answer,
  AnswerListResult,
  AnswerCreateInput,
} from "@/types";

export async function getAnswers(params: {
  question_id: string;
  page?: number;
  per_page?: number;
}): Promise<AnswerListResult> {
  const res = await api.get<AnswerListResult>("/answers", { params });
  return res.data;
}

export async function createAnswer(
  data: AnswerCreateInput
): Promise<{ answer: Answer }> {
  const res = await api.post<{ answer: Answer }>("/answers", data);
  return res.data;
}

export async function updateAnswer(
  id: string,
  body: string
): Promise<{ answer: Answer }> {
  const res = await api.patch<{ answer: Answer }>(`/answers/${id}`, { body });
  return res.data;
}

export async function deleteAnswer(id: string): Promise<void> {
  await api.delete(`/answers/${id}`);
}

export async function acceptAnswer(id: string): Promise<{ answer: Answer }> {
  const res = await api.post<{ answer: Answer }>(`/answers/${id}/accept`);
  return res.data;
}

export async function unacceptAnswer(id: string): Promise<void> {
  await api.delete(`/answers/${id}/accept`);
}
