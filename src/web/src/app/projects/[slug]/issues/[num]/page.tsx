import { redirect } from "next/navigation";

// 旧独立详情页已改为项目主页内的 Issue 抽屉；保留 redirect 兼容书签/外链。
export default async function IssueDetailRedirect({
  params,
}: {
  params: Promise<{ slug: string; num: string }>;
}) {
  const { slug, num } = await params;
  redirect(`/projects/${slug}?tab=issues&issue=${num}`);
}
