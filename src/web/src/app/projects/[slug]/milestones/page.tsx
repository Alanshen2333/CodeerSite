import { redirect } from "next/navigation";

// 旧独立路由已并入项目主页 Tab；保留 redirect 兼容书签/外链。
export default async function MilestonesRedirect({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  redirect(`/projects/${slug}?tab=milestones`);
}
