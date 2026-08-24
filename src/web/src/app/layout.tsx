import type { Metadata, Viewport } from "next";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { App } from "antd";
import ThemeProvider from "@/providers/ThemeProvider";
import { AuthProvider } from "@/providers/AuthProvider";
import Navbar from "@/components/layout/Navbar";
import SiteFooter from "@/components/layout/SiteFooter";
import MessageBridge from "@/components/MessageBridge";
import { themeBootstrapScript } from "@/lib/theme-bootstrap";
import "./globals.css";

export const metadata: Metadata = {
  title: "Codeersite — 开发者社区",
  description: "融合 GitLab 项目管理与 StackOverflow Q&A 的开发者社区平台",
};

// viewport-fit=cover 让 iOS 安全区 env(safe-area-inset-*) 生效
export const viewport: Viewport = {
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        {/* React hydrate 前解析用户偏好或系统主题，避免页面外壳闪烁。 */}
        <script
          dangerouslySetInnerHTML={{
            __html: themeBootstrapScript,
          }}
        />
      </head>
      <body className="flex min-h-screen flex-col bg-bg-layout text-text antialiased">
        <AntdRegistry>
          <ThemeProvider>
            <App className="flex min-h-screen flex-col">
              <MessageBridge />
              <AuthProvider>
                <Navbar />
                <main className="flex-1">{children}</main>
                <SiteFooter />
              </AuthProvider>
            </App>
          </ThemeProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
