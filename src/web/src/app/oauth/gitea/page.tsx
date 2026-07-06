"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, Typography } from "antd";
import { useAuth } from "@/providers/AuthProvider";
import { getAccessToken } from "@/lib/auth";
import { message } from "@/lib/message";
import PageContainer from "@/components/layout/PageContainer";
import LoadingState from "@/components/ui/LoadingState";

const { Text } = Typography;

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { oauthLogin, refreshUser } = useAuth();

  const code = searchParams.get("code");
  const state = searchParams.get("state");

  useEffect(() => {
    if (!code || !state) {
      message.error("缺少授权参数");
      router.replace("/login");
      return;
    }

    const wasLoggedIn = !!getAccessToken();

    const handle = async () => {
      try {
        await oauthLogin(code, state);
        if (wasLoggedIn) {
          await refreshUser();
          message.success("Gitea 账号绑定成功");
          router.replace("/settings/account");
        } else {
          message.success("Gitea 登录成功");
          router.replace("/");
        }
      } catch (err: unknown) {
        const msg =
          err && typeof err === "object" && "response" in err
            ? (err as { response?: { data?: { message?: string } } }).response?.data
                ?.message || "授权处理失败"
            : "授权处理失败";
        message.error(msg);
        router.replace(wasLoggedIn ? "/settings/account" : "/login");
      }
    };

    handle();
  }, [code, state, oauthLogin, refreshUser, router]);

  return (
    <PageContainer size="narrow">
      <Card className="text-center py-12">
        <LoadingState size="large" tip="正在处理 Gitea 授权回调..." />
        <Text type="secondary" className="mt-4 block">
          请稍候，正在完成身份校验
        </Text>
      </Card>
    </PageContainer>
  );
}

export default function GiteaOAuthCallbackPage() {
  return (
    <Suspense fallback={<LoadingState size="large" tip="正在加载..." />}>
      <CallbackContent />
    </Suspense>
  );
}
