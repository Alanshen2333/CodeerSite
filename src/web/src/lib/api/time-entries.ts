import api from "../api";
import type { Issue, TimeEntry, TimeEntryListResult } from "@/types";

/** 列出某 Issue 的全部耗时条目（倒序，最新在前）。需项目成员。 */
export async function getTimeEntries(
  slug: string,
  issueNumber: number,
): Promise<TimeEntryListResult> {
  const res = await api.get<TimeEntryListResult>(
    `/projects/${slug}/issues/${issueNumber}/time-entries`,
  );
  return res.data;
}

/** 记录一段耗时。返回新建条目与聚合后的 issue（time_spent 已更新）。 */
export async function createTimeEntry(
  slug: string,
  issueNumber: number,
  data: { seconds: number; note?: string },
): Promise<{ entry: TimeEntry; issue: Issue }> {
  const res = await api.post<{ entry: TimeEntry; issue: Issue }>(
    `/projects/${slug}/issues/${issueNumber}/time-entries`,
    data,
  );
  return res.data;
}
