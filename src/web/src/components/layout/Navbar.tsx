"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Layout, Menu, Button, Space, Avatar, Dropdown, Spin, Tooltip } from "antd";
import {
  HomeOutlined,
  QuestionCircleOutlined,
  ProjectOutlined,
  TagsOutlined,
  SearchOutlined,
  BellOutlined,
  UserOutlined,
  LoginOutlined,
  LogoutOutlined,
  PlusOutlined,
  SunOutlined,
  MoonOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/providers/AuthProvider";
import { useTheme } from "@/providers/ThemeProvider";
import { layout } from "@/styles/tokens";

const { Header } = Layout;

export default function Navbar() {
  const { user, loading, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const router = useRouter();
  const [themeReady, setThemeReady] = useState(false);

  useEffect(() => setThemeReady(true), []);

  const userMenu = {
    items: [
      {
        key: "profile",
        icon: <UserOutlined />,
        label: "个人主页",
        onClick: () => router.push(`/users/${user?.username}`),
      },
      {
        key: "notifications",
        icon: <BellOutlined />,
        label: "通知",
        onClick: () => router.push("/notifications"),
      },
      {
        key: "settings",
        icon: <SettingOutlined />,
        label: "账号设置",
        onClick: () => router.push("/settings/account"),
      },
      { type: "divider" as const },
      {
        key: "logout",
        icon: <LogoutOutlined />,
        label: "退出登录",
        onClick: () => {
          logout();
          router.push("/");
        },
      },
    ],
  };

  return (
    <Header
      className="bg-bg-container/80 backdrop-blur-md border-b border-border sticky top-0 z-[100] !p-0"
      style={{
        // iOS 安全区域：顶栏不被状态栏/刘海遮挡；高度自适应 = safe-area + 56px 内容区
        paddingTop: "env(safe-area-inset-top)",
        height: "auto",
      }}
    >
      <div
        // 与 PageContainer 对齐：max-width 居中 + 响应式水平安全边距
        className="mx-auto flex w-full items-center justify-between px-4 sm:px-6 lg:px-8"
        style={{ maxWidth: layout.contentWide, height: layout.navHeight }}
      >
        {/* Logo */}
        <Link
          href="/"
          className="mr-2 shrink-0 text-xl font-bold text-primary no-underline sm:mr-8"
        >
          Codeersite
        </Link>

        {/* Navigation */}
        <Menu
          mode="horizontal"
          className="hidden min-w-0 flex-1 !border-none !bg-transparent md:block"
          items={[
            {
              key: "questions",
              icon: <QuestionCircleOutlined />,
              label: <Link href="/questions">问答</Link>,
            },
            {
              key: "projects",
              icon: <ProjectOutlined />,
              label: <Link href="/projects">项目</Link>,
            },
            {
              key: "tags",
              icon: <TagsOutlined />,
              label: <Link href="/tags">标签</Link>,
            },
          ]}
        />

        {/* Right actions */}
        <Space align="center" className="items-center">
        <Tooltip title="搜索">
          <Button
            aria-label="搜索"
            className="!hidden sm:!inline-flex"
            icon={<SearchOutlined />}
            type="text"
            onClick={() => router.push("/search")}
          />
        </Tooltip>

        {/* 主题切换 */}
        <Tooltip title={theme === "light" ? "深色模式" : "浅色模式"}>
          <Button
            aria-label={theme === "light" ? "切换到深色模式" : "切换到浅色模式"}
            icon={
              themeReady
                ? theme === "light"
                  ? <MoonOutlined />
                  : <SunOutlined />
                : <span aria-hidden className="inline-block size-4" />
            }
            type="text"
            onClick={toggleTheme}
          />
        </Tooltip>

        {loading ? (
          <Spin size="small" />
        ) : user ? (
          <>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => router.push("/questions/ask")}>
              <span className="hidden sm:inline">提问</span>
            </Button>
            <Button icon={<BellOutlined />} type="text" onClick={() => router.push("/notifications")} />
            <Dropdown menu={userMenu} placement="bottomRight">
              <Space className="cursor-pointer">
                <Avatar size="small" icon={<UserOutlined />} />
                <span className="hidden sm:inline">{user.display_name || user.username}</span>
              </Space>
            </Dropdown>
          </>
        ) : (
          <>
            <Button
              className="!inline-flex !h-9 !items-center"
              aria-label="登录"
              icon={<LoginOutlined />}
              onClick={() => router.push("/login")}
            >
              <span className="hidden sm:inline">登录</span>
            </Button>
            <Button
              className="!inline-flex !h-9 !items-center"
              type="primary"
              onClick={() => router.push("/register")}
            >
              注册
            </Button>
          </>
        )}
      </Space>
      </div>
    </Header>
  );
}
