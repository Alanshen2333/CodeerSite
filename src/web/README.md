# Codeersite 前端

基于 Next.js 14 + Ant Design 5 的开发者社区前端。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **UI 库**: Ant Design 5 + @ant-design/icons
- **样式**: Tailwind CSS 4
- **HTTP**: Axios（自动 token 刷新）
- **语言**: TypeScript

## 开发

```bash
pnpm install
pnpm dev          # http://localhost:3000
pnpm build        # 生产构建
```

## 目录结构

```
src/
├── app/                    # App Router 页面
│   ├── layout.tsx          # 根布局（AuthProvider + Ant Design）
│   ├── page.tsx            # 首页
│   ├── (auth)/             # 认证页面（路由组）
│   │   ├── login/
│   │   └── register/
│   ├── questions/          # 问答
│   ├── projects/           # 项目
│   ├── tags/               # 标签
│   ├── search/             # 搜索
│   └── notifications/      # 通知
├── components/
│   ├── layout/Navbar.tsx   # 导航栏
│   └── ui/                 # 基础 UI 组件
├── providers/
│   └── AuthProvider.tsx    # 认证上下文
├── lib/
│   ├── api.ts              # Axios 实例 + 拦截器
│   └── auth.ts             # Token 管理
└── types/
    └── user.ts             # 用户相关类型
```

## API 代理

开发时 Next.js 通过 `rewrites` 将 `/api/*` 代理到 Flask 后端 (`localhost:5000`)，前端使用相对路径即可，无需处理 CORS。

配置在 `next.config.ts`。
