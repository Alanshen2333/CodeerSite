import api from "../api";
import type { NotificationListResult } from "@/types";

export async function getNotifications(params?: {
  unread?: boolean;
  page?: number;
  per_page?: number;
}): Promise<NotificationListResult> {
  const res = await api.get<NotificationListResult>("/notifications", { params });
  return res.data;
}

export async function getUnreadCount(): Promise<{ unread_count: number }> {
  const res = await api.get<{ unread_count: number }>("/notifications/unread-count");
  return res.data;
}

export async function markNotificationRead(id: string): Promise<void> {
  await api.patch(`/notifications/${id}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.patch("/notifications/read-all");
}
