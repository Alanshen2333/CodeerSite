import type { Metadata } from "next";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { App } from "antd";
import ThemeProvider from "@/providers/ThemeProvider";
import { AuthProvider } from "@/providers/AuthProvider";
import Navbar from "@/components/layout/Navbar";
import MessageBridge from "@/components/MessageBridge";
import "./globals.css";

export const metadata: Metadata = {
  title: "Codeersite — 开发者社区",
  description: "融合 GitLab 项目管理与 StackOverflow Q&A 的开发者社区平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        {/* 防深色模式闪烁：React hydrate 之前从 localStorage 读取主题 */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen bg-bg-layout text-text antialiased">
        <AntdRegistry>
          <ThemeProvider>
            <App>
              <MessageBridge />
              <AuthProvider>
                <Navbar />
                <main className="min-h-[calc(100vh-56px)]">{children}</main>
              </AuthProvider>
            </App>
          </ThemeProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
