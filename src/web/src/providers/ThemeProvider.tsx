"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { createAntdTheme } from "@/styles/antd-theme";
import type { Theme } from "@/styles/tokens";
import {
  applyTheme,
  isTheme,
  readThemePreference,
  storeThemePreference,
  systemTheme,
  THEME_MEDIA_QUERY,
  THEME_STORAGE_KEY,
} from "@/lib/theme";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export default function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreference] = useState<Theme | null>(null);
  const [system, setSystem] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);
  const theme = preference ?? system;

  useEffect(() => {
    const media = window.matchMedia(THEME_MEDIA_QUERY);
    const stored = readThemePreference();
    const initialSystem = systemTheme(media.matches);

    setPreference(stored);
    setSystem(initialSystem);
    applyTheme(stored ?? initialSystem);
    setMounted(true);

    const handleSystemChange = (event: MediaQueryListEvent) => {
      setSystem(systemTheme(event.matches));
    };
    const handleStorage = (event: StorageEvent) => {
      if (event.key === THEME_STORAGE_KEY) {
        setPreference(isTheme(event.newValue) ? event.newValue : null);
      }
    };

    media.addEventListener("change", handleSystemChange);
    window.addEventListener("storage", handleStorage);
    return () => {
      media.removeEventListener("change", handleSystemChange);
      window.removeEventListener("storage", handleStorage);
    };
  }, []);

  useEffect(() => {
    if (mounted) applyTheme(theme);
  }, [mounted, theme]);

  const toggleTheme = useCallback(() => {
    const next = theme === "light" ? "dark" : "light";
    setPreference(next);
    storeThemePreference(next);
    applyTheme(next);
  }, [theme]);

  const resolvedTheme = mounted ? theme : "light";

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <ConfigProvider locale={zhCN} theme={createAntdTheme(resolvedTheme)}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
