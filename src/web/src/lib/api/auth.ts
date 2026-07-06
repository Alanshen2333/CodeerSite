import api from "../api";
import type {
  AuthResponse,
  ChangePasswordInput,
  EmailCodePurpose,
  UpdateProfileInput,
  User,
  OAuthAuthorizeResponse,
  OAuthCallbackResponse,
  GitCredentialsResponse,
} from "@/types/user";

export async function updateMe(data: UpdateProfileInput): Promise<{ user: User }> {
  const res = await api.patch<{ user: User }>("/auth/me", data);
  return res.data;
}

export async function changePassword(data: ChangePasswordInput): Promise<void> {
  await api.post("/auth/change-password", data);
}

export async function uploadAvatar(file: File): Promise<{ avatar_url: string; user: User }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post<{ avatar_url: string; user: User }>("/auth/avatar", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function sendEmailCode(purpose: EmailCodePurpose): Promise<void> {
  await api.post("/auth/email-code", { purpose });
}

export async function login(data: { email: string; password: string }): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>("/auth/login", data);
  return res.data;
}

export async function register(data: {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>("/auth/register", data);
  return res.data;
}

export async function getMe(): Promise<{ user: User }> {
  const res = await api.get<{ user: User }>("/auth/me");
  return res.data;
}

export async function getOAuthAuthorizeUrl(
  intent: "login" | "bind",
): Promise<OAuthAuthorizeResponse> {
  const res = await api.get<OAuthAuthorizeResponse>("/auth/oauth/gitea/authorize", {
    params: { intent },
  });
  return res.data;
}

export async function oauthCallback(
  code: string,
  state: string,
): Promise<OAuthCallbackResponse> {
  const res = await api.get<OAuthCallbackResponse>("/auth/oauth/gitea/callback", {
    params: { code, state },
  });
  return res.data;
}

export async function getGitCredentials(
  repo: string,
): Promise<GitCredentialsResponse> {
  const res = await api.get<GitCredentialsResponse>("/auth/git-credentials", {
    params: { repo },
  });
  return res.data;
}
