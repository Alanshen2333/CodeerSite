import { redirect } from "next/navigation";

// 旧独立新建页已改为项目主页内的 Issue 新建抽屉；保留 redirect 兼容书签/外链。
export default async function NewIssueRedirect({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  redirect(`/projects/${slug}?tab=issues&new_issue=1`);
}
