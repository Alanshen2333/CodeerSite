"use client";

import { createContext, useContext, useEffect, type ReactNode } from "react";
import { ConfigProvider, theme as antdTheme } from "antd";
import zhCN from "antd/locale/zh_CN";
import { antdThemeTokens } from "@/styles/tokens";

type Theme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export default function ThemeProvider({ children }: { children: ReactNode }) {
  // 夜间模式暂时禁用：清理旧偏好和残留 class，始终使用浅色主题。
  useEffect(() => {
    localStorage.removeItem("theme");
    document.documentElement.classList.remove("dark");
  }, []);

  return (
    <ThemeContext.Provider value={{ theme: "light" }}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: antdTheme.defaultAlgorithm,
          token: antdThemeTokens,
        }}
      >
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
