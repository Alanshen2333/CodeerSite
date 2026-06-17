"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import api from "@/lib/api";
import { getAccessToken, removeTokens, setTokens } from "@/lib/auth";
import type { User, AuthResponse, LoginInput, RegisterInput } from "@/types/user";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginInput) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  logout: () => void;
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
      api
        .get("/auth/me", { signal: controller.signal })
        .then((res) => {
          // Guard: only update if still mounted and still authenticated
          if (mountedRef.current && getAccessToken()) {
            setUser(res.data.user);
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
    const res = await api.post<AuthResponse>("/auth/login", data);
    setTokens(res.data.access_token, res.data.refresh_token);
    setUser(res.data.user);
  }, []);

  const register = useCallback(async (data: RegisterInput) => {
    const res = await api.post<AuthResponse>("/auth/register", data);
    setTokens(res.data.access_token, res.data.refresh_token);
    setUser(res.data.user);
  }, []);

  const logout = useCallback(() => {
    removeTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
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
