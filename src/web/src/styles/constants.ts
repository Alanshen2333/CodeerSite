/**
 * 共享 UI 常量
 *
 * 从各处重复定义的映射中提取，统一管理。
 */

import type { ReactNode } from "react";

// ── Issue 优先级 ───────────────────────────────────────
export const priorityColor: Record<string, string> = {
  low: "default",
  medium: "blue",
  high: "orange",
  critical: "red",
} as const;

export const priorityLabel: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
  critical: "紧急",
} as const;

// ── Issue 状态 ──────────────────────────────────────────
export const issueStatusColor: Record<string, string> = {
  open: "blue",
  in_progress: "orange",
  closed: "green",
} as const;

export const issueStatusLabel: Record<string, string> = {
  open: "待处理",
  in_progress: "进行中",
  closed: "已关闭",
} as const;

// ── 项目可见性 ──────────────────────────────────────────
export const visibilityLabel: Record<string, string> = {
  public: "公开",
  private: "私有",
} as const;

// ── 用户角色 ────────────────────────────────────────────
export const roleLabel: Record<string, string> = {
  user: "用户",
  moderator: "版主",
  admin: "管理员",
} as const;

// ── 里程碑状态 ──────────────────────────────────────────
export const milestoneStatusLabel: Record<string, string> = {
  open: "进行中",
  closed: "已关闭",
} as const;

/** 里程碑完成百分比（0–100），open/closed 均为 0 时返回 0。 */
export function milestonePercent(open: number, closed: number): number {
  const total = open + closed;
  return total > 0 ? Math.round((closed / total) * 100) : 0;
}

/** 里程碑进度条 format 文案，如「3/5 已关闭」。 */
export function milestoneProgressText(open: number, closed: number): string {
  return `${closed}/${open + closed} 已关闭`;
}

// ── 时间跟踪 ────────────────────────────────────────────
/** 秒 → 人类可读时长，如 3900 → "1h 5m"，0 → "0m"。 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "0m";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0 && m > 0) return `${h}h ${m}m`;
  if (h > 0) return `${h}h`;
  return `${m}m`;
}
