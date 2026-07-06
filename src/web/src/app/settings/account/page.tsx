"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import ProfileFormCard from "@/components/settings/ProfileFormCard";
import AvatarUploadCard from "@/components/settings/AvatarUploadCard";
import PasswordChangeCard from "@/components/settings/PasswordChangeCard";

export default function AccountSettingsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) return <LoadingState size="large" />;
  if (!user) return null;

  return (
    <PageContainer size="narrow">
      <h2 className="text-xl font-semibold text-text mb-6">账号设置</h2>

      <ProfileFormCard />
      <AvatarUploadCard />
      <PasswordChangeCard />
    </PageContainer>
  );
}
