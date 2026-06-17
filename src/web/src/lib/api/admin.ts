import api from "../api";

export async function getAdminStats(): Promise<{
  users: number;
  active_users: number;
  questions: number;
  answers: number;
  projects: number;
  admins: number;
  moderators: number;
}> {
  const res = await api.get("/admin/stats");
  return res.data;
}

export async function getAdminUsers(params?: {
  page?: number;
  per_page?: number;
}): Promise<{ users: Record<string, unknown>[]; total: number; page: number; pages: number }> {
  const res = await api.get("/admin/users", { params });
  return res.data;
}

export async function updateUser(
  userId: string,
  data: { role?: string; is_active?: boolean }
): Promise<{ user: Record<string, unknown> }> {
  const res = await api.patch(`/admin/users/${userId}`, data);
  return res.data;
}

export async function deleteUser(userId: string): Promise<void> {
  await api.delete(`/admin/users/${userId}`);
}
