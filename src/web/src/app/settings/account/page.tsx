"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card } from "antd";
import { useAuth } from "@/providers/AuthProvider";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";
import ProfileFormCard from "@/components/settings/ProfileFormCard";
import AvatarUploadCard from "@/components/settings/AvatarUploadCard";
import PasswordChangeCard from "@/components/settings/PasswordChangeCard";
import SshKeyList from "@/components/settings/SshKeyList";
import AddSshKeyForm from "@/components/settings/AddSshKeyForm";
import { getSshKeys, deleteSshKey } from "@/lib/api/ssh-keys";
import { message } from "@/lib/message";
import type { SshKey } from "@/types/user";

export default function AccountSettingsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [keys, setKeys] = useState<SshKey[]>([]);
  const [keysLoading, setKeysLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const loadKeys = useCallback(async () => {
    if (!user) return;
    setKeysLoading(true);
    try {
      const data = await getSshKeys();
      setKeys(data.keys);
    } catch {
      message.error("加载 SSH 公钥失败");
    } finally {
      setKeysLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadKeys();
  }, [loadKeys]);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteSshKey(id);
      message.success("公钥已删除");
      await loadKeys();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { message?: string } } }).response?.data?.message || "删除失败"
          : "删除失败";
      message.error(msg);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <LoadingState size="large" />;
  if (!user) return null;

  return (
    <PageContainer size="narrow">
      <h2 className="text-xl font-semibold text-text mb-6">账号设置</h2>

      <ProfileFormCard />
      <AvatarUploadCard />
      <PasswordChangeCard />

      <Card title="SSH 公钥" className="mb-4" loading={keysLoading}>
        <AddSshKeyForm onSuccess={loadKeys} />
        <div className="mt-6">
          <SshKeyList keys={keys} onDelete={handleDelete} deletingId={deletingId} />
        </div>
      </Card>
    </PageContainer>
  );
}
