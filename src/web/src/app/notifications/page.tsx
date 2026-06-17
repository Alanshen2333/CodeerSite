"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { Button, Switch, Badge, Card, Space } from "antd";
import { CheckOutlined } from "@ant-design/icons";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import {
  getNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from "@/lib/api/notifications";
import type { Notification } from "@/types";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import EmptyState from "@/components/ui/EmptyState";
import ListPagination from "@/components/ui/ListPagination";

function timeAgo(dateStr: string): string {
  const d = new Date(dateStr);
  const now = Date.now();
  const diff = now - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins} 分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} 小时前`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} 天前`;
  return d.toLocaleDateString("zh-CN");
}

function NotificationsContent() {
  const { user } = useAuth();
  const router = useRouter();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getNotifications({
        unread: unreadOnly || undefined,
        page,
        per_page: perPage,
      });
      setNotifications(result.items);
      setTotal(result.total);
      const count = await getUnreadCount();
      setUnreadCount(count.unread_count);
    } catch {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, unreadOnly]);

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    fetchNotifications();
  }, [fetchNotifications, user, router]);

  const handleMarkRead = async (id: string) => {
    await markNotificationRead(id);
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
    setUnreadCount((c) => Math.max(0, c - 1));
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  };

  if (!user) return null;

  return (
    <PageContainer size="default">
      <div className="flex justify-between items-center flex-wrap gap-3 mb-6">
        <Space align="center">
          <h2 className="text-xl font-semibold text-text m-0">通知</h2>
          {unreadCount > 0 && (
            <Badge count={unreadCount} overflowCount={99} />
          )}
        </Space>
        <Space>
          <Switch
            checked={unreadOnly}
            onChange={(v) => {
              setUnreadOnly(v);
              setPage(1);
            }}
            checkedChildren="未读"
            unCheckedChildren="全部"
          />
          {unreadCount > 0 && (
            <Button size="small" icon={<CheckOutlined />} onClick={handleMarkAllRead}>
              全部已读
            </Button>
          )}
        </Space>
      </div>

      {loading ? (
        <LoadingState />
      ) : notifications.length === 0 ? (
        <EmptyState description={unreadOnly ? "没有未读通知" : "暂无通知"} />
      ) : (
        <>
          <div className="flex flex-col gap-2">
            {notifications.map((n) => (
              <Card
                key={n.id}
                className={`cursor-pointer border-border transition-colors ${
                  n.is_read ? "opacity-60" : "bg-bg-container"
                }`}
                onClick={() => {
                  if (!n.is_read) handleMarkRead(n.id);
                  if (n.link) router.push(n.link);
                }}
              >
                <div className="flex justify-between items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {!n.is_read && (
                        <span className="w-2 h-2 rounded-full bg-primary inline-block" />
                      )}
                      <span className="font-medium text-text text-sm">{n.title}</span>
                    </div>
                    {n.body && (
                      <p className="text-text-secondary text-sm m-0 line-clamp-1">{n.body}</p>
                    )}
                  </div>
                  <span className="text-text-tertiary text-xs whitespace-nowrap">
                    {timeAgo(n.created_at)}
                  </span>
                </div>
              </Card>
            ))}
          </div>
          <ListPagination
            current={page}
            total={total}
            pageSize={perPage}
            onChange={(p) => setPage(p)}
          />
        </>
      )}
    </PageContainer>
  );
}

export default function NotificationsPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <NotificationsContent />
    </Suspense>
  );
}
