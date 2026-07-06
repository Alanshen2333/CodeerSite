export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  website: string | null;
  location: string | null;
  reputation: number;
  role: "user" | "moderator" | "admin";
  is_active: boolean;
  last_login_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PublicUser {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  website: string | null;
  location: string | null;
  reputation: number;
  role: "user" | "moderator" | "admin";
  created_at: string | null;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}

export interface UpdateProfileInput {
  display_name?: string;
  bio?: string;
  website?: string;
  location?: string;
  avatar_url?: string;
}

export interface ChangePasswordInput {
  verification_code: string;
  new_password: string;
}

export type EmailCodePurpose = "change_password" | "disable_2fa" | "recover_2fa";
