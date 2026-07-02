import api from "../api";
import type {
  Badge,
  BadgeCreateInput,
  BadgeUpdateInput,
  UserBadge,
} from "@/types";

// ── 公开 ───────────────────────────────────────────────

export async function getBadges(): Promise<Badge[]> {
  const res = await api.get<{ badges: Badge[] }>("/badges");
  return res.data.badges;
}

export async function getBadge(slug: string): Promise<Badge> {
  const res = await api.get<{ badge: Badge }>(`/badges/${slug}`);
  return res.data.badge;
}

export async function getUserBadges(username: string): Promise<UserBadge[]> {
  const res = await api.get<{ badges: UserBadge[] }>(`/users/${username}/badges`);
  return res.data.badges;
}

// ── 管理 ───────────────────────────────────────────────

export async function getAdminBadges(): Promise<Badge[]> {
  const res = await api.get<{ badges: Badge[] }>("/admin/badges");
  return res.data.badges;
}

export async function createBadge(input: BadgeCreateInput): Promise<Badge> {
  const res = await api.post<{ badge: Badge }>("/admin/badges", input);
  return res.data.badge;
}

export async function updateBadge(
  badgeId: string,
  input: BadgeUpdateInput,
): Promise<Badge> {
  const res = await api.patch<{ badge: Badge }>(`/admin/badges/${badgeId}`, input);
  return res.data.badge;
}

export async function deleteBadge(badgeId: string): Promise<void> {
  await api.delete(`/admin/badges/${badgeId}`);
}

export async function getBadgeRecipients(badgeId: string): Promise<UserBadge[]> {
  const res = await api.get<{ recipients: UserBadge[] }>(
    `/admin/badges/${badgeId}/recipients`,
  );
  return res.data.recipients;
}

export async function awardBadge(
  badgeId: string,
  userId: string,
  reason?: string,
): Promise<UserBadge> {
  const res = await api.post<{ award: UserBadge }>(
    `/admin/badges/${badgeId}/award`,
    { user_id: userId, reason },
  );
  return res.data.award;
}

export async function revokeBadge(badgeId: string, userId: string): Promise<void> {
  await api.delete(`/admin/badges/${badgeId}/award`, { data: { user_id: userId } });
}
