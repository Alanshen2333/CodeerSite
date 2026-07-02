"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button, Input, Space, Typography } from "antd";
import { message } from "@/lib/message";
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
} from "@ant-design/icons";
import { getTimeEntries, createTimeEntry } from "@/lib/api/time-entries";
import type { Issue, TimeEntry } from "@/types";
import { formatDuration } from "@/styles/constants";

const { Text } = Typography;

interface Props {
  slug: string;
  issue: Issue;
  /** 耗时记录提交成功后回调，父级可刷新 issue（time_spent 已聚合更新）。 */
  onChanged?: (issue: Issue) => void;
}

/**
 * Issue 时间跟踪面板：
 * - 展示预估工时 / 已耗时
 * - 计时器：开始/暂停/停止并提交（本地 state，提交时 POST time-entries）
 * - 手动输入耗时（小时 + 分钟）+ 备注
 * - 耗时条目列表（倒序）
 */
export default function TimeTracker({ slug, issue, onChanged }: Props) {
  const [entries, setEntries] = useState<TimeEntry[]>([]);
  const [loadingEntries, setLoadingEntries] = useState(false);
  // 计时器：累计已运行秒数（未提交）。running 表示正在计时。
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 手动输入
  const [manualHours, setManualHours] = useState<string>("");
  const [manualMinutes, setManualMinutes] = useState<string>("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadEntries = useCallback(async () => {
    setLoadingEntries(true);
    try {
      const r = await getTimeEntries(slug, issue.issue_number);
      setEntries(r.time_entries);
    } catch {
      // 权限或网络错误：静默，条目列表留空
    } finally {
      setLoadingEntries(false);
    }
  }, [slug, issue.issue_number]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  // 计时器循环
  useEffect(() => {
    if (running) {
      timerRef.current = setInterval(() => {
        setElapsed((s) => s + 1);
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [running]);

  const submitEntry = async (seconds: number, entryNote?: string) => {
    if (seconds <= 0) {
      message.warning("耗时必须大于 0");
      return false;
    }
    setSubmitting(true);
    try {
      const r = await createTimeEntry(slug, issue.issue_number, {
        seconds,
        note: entryNote?.trim() || undefined,
      });
      setEntries((prev) => [r.entry, ...prev]);
      onChanged?.(r.issue);
      return true;
    } catch {
      message.error("记录耗时失败");
      return false;
    } finally {
      setSubmitting(false);
    }
  };

  const handleStopAndSubmit = async () => {
    if (elapsed <= 0) {
      setRunning(false);
      return;
    }
    const ok = await submitEntry(elapsed, note);
    if (ok) {
      setElapsed(0);
      setRunning(false);
      setNote("");
      message.success(`已记录 ${formatDuration(elapsed)}`);
    }
  };

  const handleCancelTimer = () => {
    setRunning(false);
    setElapsed(0);
  };

  const handleManualSubmit = async () => {
    const h = parseInt(manualHours || "0", 10);
    const m = parseInt(manualMinutes || "0", 10);
    const seconds = (isFinite(h) ? h : 0) * 3600 + (isFinite(m) ? m : 0) * 60;
    if (seconds <= 0) {
      message.warning("请输入有效的耗时");
      return;
    }
    const ok = await submitEntry(seconds, note);
    if (ok) {
      setManualHours("");
      setManualMinutes("");
      setNote("");
      message.success(`已记录 ${formatDuration(seconds)}`);
    }
  };

  const estimate = issue.time_estimate;
  const spent = issue.time_spent || 0;
  // 进度：已耗时 / 预估（无预估时不显示百分比）
  const progressPct =
    estimate && estimate > 0
      ? Math.min(Math.round((spent / estimate) * 100), 999)
      : null;

  return (
    <div className="space-y-4">
      {/* 概览：预估 / 已耗时 / 进度 */}
      <div className="flex items-center gap-4 flex-wrap">
        <div>
          <Text type="secondary" className="!text-xs">预估</Text>
          <div className="text-text font-medium">
            {estimate != null ? formatDuration(estimate) : "未估时"}
          </div>
        </div>
        <div>
          <Text type="secondary" className="!text-xs">已耗时</Text>
          <div className="text-text font-medium">{formatDuration(spent)}</div>
        </div>
        {progressPct != null && (
          <div>
            <Text type="secondary" className="!text-xs">进度</Text>
            <div
              className={
                progressPct > 100
                  ? "font-medium text-error"
                  : "font-medium text-text"
              }
            >
              {progressPct}%
            </div>
          </div>
        )}
      </div>

      {/* 计时器 */}
      <div className="rounded-md border border-border p-3">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="text-text">
            <Text type="secondary" className="!text-xs mr-2">计时器</Text>
            <span className="font-mono text-lg tabular-nums">
              {formatDuration(elapsed)}
            </span>
          </div>
          <Space>
            {!running ? (
              <Button
                icon={<PlayCircleOutlined />}
                onClick={() => setRunning(true)}
                disabled={submitting}
              >
                开始
              </Button>
            ) : (
              <Button
                icon={<PauseCircleOutlined />}
                onClick={() => setRunning(false)}
              >
                暂停
              </Button>
            )}
            <Button
              icon={<StopOutlined />}
              onClick={handleStopAndSubmit}
              loading={submitting}
              disabled={elapsed <= 0 && !running}
            >
              停止并提交
            </Button>
            {(running || elapsed > 0) && (
              <Button type="text" onClick={handleCancelTimer} disabled={submitting}>
                丢弃
              </Button>
            )}
          </Space>
        </div>
      </div>

      {/* 手动输入 + 备注 */}
      <div className="rounded-md border border-border p-3 space-y-2">
        <Text type="secondary" className="!text-xs">手动记录耗时</Text>
        <div className="flex items-center gap-2 flex-wrap">
          <Space.Compact>
            <Input
              prefix="h"
              inputMode="numeric"
              placeholder="0"
              value={manualHours}
              onChange={(e) => setManualHours(e.target.value.replace(/[^0-9]/g, ""))}
              className="w-[88px]"
            />
            <Input
              prefix="m"
              inputMode="numeric"
              placeholder="0"
              value={manualMinutes}
              onChange={(e) => setManualMinutes(e.target.value.replace(/[^0-9]/g, ""))}
              className="w-[88px]"
            />
          </Space.Compact>
          <Input
            placeholder="备注（可选，最多 500 字）"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={500}
            className="flex-1 min-w-[160px]"
          />
          <Button
            type="primary"
            onClick={handleManualSubmit}
            loading={submitting}
            disabled={submitting}
          >
            记录
          </Button>
        </div>
      </div>

      {/* 耗时条目列表 */}
      <div>
        <Text type="secondary" className="!text-xs">
          耗时记录（{entries.length}）
        </Text>
        {loadingEntries ? null : entries.length === 0 ? (
          <Text type="secondary" className="!text-xs block mt-2">
            暂无记录
          </Text>
        ) : (
          <div className="mt-1">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="py-2 border-b border-border-secondary last:border-b-0"
              >
                <div className="flex items-center justify-between gap-2">
                  <Text className="!text-sm font-medium">
                    {formatDuration(entry.seconds)}
                  </Text>
                  <Text type="secondary" className="!text-xs">
                    {new Date(entry.created_at).toLocaleDateString("zh-CN", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </Text>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <Text type="secondary" className="!text-xs">
                    {entry.user?.display_name || entry.user?.username || "匿名"}
                  </Text>
                  {entry.note && (
                    <Text type="secondary" className="!text-xs">
                      · {entry.note}
                    </Text>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
