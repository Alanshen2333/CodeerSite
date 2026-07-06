"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { getAccessToken, removeTokens, setTokens } from "@/lib/auth";
import {
  getMe,
  login as apiLogin,
  register as apiRegister,
  oauthCallback,
} from "@/lib/api/auth";
import type { User, LoginInput, RegisterInput, UpdateProfileInput } from "@/types/user";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginInput) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  logout: () => void;
  updateUser: (data: UpdateProfileInput) => Promise<User>;
  refreshUser: () => Promise<User>;
  oauthLogin: (code: string, state: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const mountedRef = useRef(true);

  // Check if user is already logged in on mount
  useEffect(() => {
    mountedRef.current = true;
    const controller = new AbortController();

    const token = getAccessToken();
    if (token) {
      getMe()
        .then((data) => {
          // Guard: only update if still mounted and still authenticated
          if (mountedRef.current && getAccessToken()) {
            setUser(data.user);
          }
        })
        .catch((err) => {
          if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
            removeTokens();
          }
        })
        .finally(() => {
          if (mountedRef.current) setLoading(false);
        });
    } else {
      setLoading(false);
    }

    return () => {
      mountedRef.current = false;
      controller.abort();
    };
  }, []);

  const login = useCallback(async (data: LoginInput) => {
    const res = await apiLogin(data);
    setTokens(res.access_token, res.refresh_token);
    setUser(res.user);
  }, []);

  const register = useCallback(async (data: RegisterInput) => {
    const res = await apiRegister(data);
    setTokens(res.access_token, res.refresh_token);
    setUser(res.user);
  }, []);

  const logout = useCallback(() => {
    removeTokens();
    setUser(null);
  }, []);

  const updateUser = useCallback(async (data: UpdateProfileInput) => {
    const { user: updated } = await import("@/lib/api/auth").then((m) => m.updateMe(data));
    setUser(updated);
    return updated;
  }, []);

  const refreshUser = useCallback(async () => {
    const { user: refreshed } = await getMe();
    setUser(refreshed);
    return refreshed;
  }, []);

  const oauthLogin = useCallback(async (code: string, state: string) => {
    const res = await oauthCallback(code, state);
    if (res.access_token && res.refresh_token) {
      setTokens(res.access_token, res.refresh_token);
    }
    setUser(res.user);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, updateUser, refreshUser, oauthLogin }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
