# CLAUDE.md — Codeersite 项目指南

## 项目概述

Codeersite 是一个融合 StackOverflow Q&A 与 GitLab 项目管理的开发者社区平台。

- **后端**: Flask 3 REST API (`src/api/`)
- **前端**: Next.js 16 + Ant Design 6 + Tailwind CSS v4 (`src/web/`)
- **数据库**: PostgreSQL 16（主存储）、MongoDB 7（搜索/通知/日志）
- **包管理**: uv (Python)、pnpm (Node)

## 常用命令

```bash
# 数据库
docker compose -f docker/docker-compose.dev.yml up -d   # 启动 PG + Mongo

# 后端
uv sync                                                   # 安装 Python 依赖
uv run alembic upgrade head                               # 运行迁移
uv run alembic revision --autogenerate -m "描述"          # 生成迁移
uv run flask --app src/api/wsgi:app run --debug -p 5000   # 开发服务器

# 前端
cd src/web && pnpm install                                # 安装依赖
cd src/web && pnpm dev                                    # 开发服务器
cd src/web && pnpm build                                  # 生产构建

# 测试
uv run pytest                                             # 后端测试
```

## 架构约定

### 后端 (Flask)

- **工厂模式**: `create_app()` 在 `src/api/app/__init__.py`
- **蓝图路由**: 所有 API 在 `src/api/app/api/` 下，每个模块一个文件
- **服务层**: 业务逻辑在 `src/api/app/services/`，控制器只做参数校验和响应
- **模型**: SQLAlchemy ORM 在 `src/api/app/models/`，使用 UUID 主键
- **序列化**: Marshmallow Schema 在 `src/api/app/schemas/`
- **认证**: JWT via `flask-jwt-extended`，`get_current_user()` 返回 User 或 None
- **迁移**: Alembic，配置文件 `alembic.ini` + `src/api/migrations/env.py`

### 前端 (Next.js)

- **路由**: App Router，页面在 `src/web/src/app/`
- **组件库**: Ant Design 6 + Tailwind CSS v4，中文 locale
- **状态**: React Context (`AuthProvider`、`ThemeProvider`)
- **HTTP**: Axios 实例在 `src/lib/api.ts`，自动附加 token、刷新、错误处理

### 数据库设计原则

- PostgreSQL 存核心关系数据（ACID 事务）
- MongoDB 存搜索索引、通知、活动日志（非结构化/高写入）
- `vote_count` 反范式缓存在主表（读多写少）
- Markdown `body` 写入时服务端渲染为 `body_html` 缓存
- Issue 使用项目内自增编号 `issue_number`
- 多态关联（votes/comments/bookmarks）通过 `target_type` + `target_id`

## 代码风格

- Python: 类型注解，`User | None` 语法
- TypeScript: 严格模式，`types/` 下定义接口
- 错误处理: 后端返回 `{"error": "...", "message": "..."}` + HTTP 状态码
- 中文注释和文档

---

## 前端开发守则

### 设计理念

参考 Linear / Notion / Vercel Dashboard — **现代、简洁、专业、商业 SaaS 质感**。
- 避免花哨渐变、过度动画、复杂装饰
- 强调信息层级、留白、可读性
- 克制的主色，大量中性色，1px 细边框，微阴影

### 样式规范（最高优先级）

1. **禁止硬编码样式**：不得在组件/页面中写 `style={{ color: "#xxx", fontSize: 14, ... }}`。所有颜色、间距、字号必须来自设计 Token。
2. **Tailwind 优先**：所有布局、间距、排版、背景、边框使用 Tailwind 工具类。仅动态值（如 `useToken()` 获取的 antd 主题色）允许 `style`。
3. **设计 Token 唯一源**：
   - TypeScript 侧：`src/web/src/styles/tokens.ts`
   - CSS 侧：`src/web/src/app/globals.css` 中的 `@theme` 块
   - 两者必须保持同步。新增/修改 Token 时同时改两个文件。
4. **语义色通过 CSS 变量桥接**：`globals.css` 中的 `@theme` 使用 `var(--tw-color-*)` 引用，`:root` / `.dark` 分别定义浅色/深色值。这样所有 `bg-bg-layout`、`text-text` 等类名自动跟随主题切换，无需手动写 `dark:` 变体。

### 布局规范

5. **必须使用 PageContainer**：每个页面最外层用 `<PageContainer size="wide|default|narrow">` 包裹，禁止手写 `maxWidth` + `margin` 容器。
   - `wide` = 960px（列表页）
   - `default` = 800px（详情页/表单页）
   - `narrow` = 640px（窄表单）
   - 全宽页面（如看板）可用 `className="p-6"` 替代
6. **页面标题用 PageHeader**：列表页的标题行统一用 `<PageHeader title="..." actions={...} />`，禁止手写 flex 标题栏。

### 组件复用

7. **使用 UI 原语**：
   - 加载态 → `<LoadingState />`
   - 空态 → `<EmptyState description="..." action={...} />`
   - 分页 → `<ListPagination current={...} total={...} onChange={...} />`
8. **共享常量**：Issue 的 `priorityColor`/`priorityLabel`/`issueStatusColor`/`issueStatusLabel` 统一从 `src/web/src/styles/constants.ts` 导入，禁止在组件中重复定义。
9. **Ant Design 职责边界**：antd 只用于复杂交互组件（Form、Table、Modal、Select、Dropdown、Menu、Pagination、DatePicker 等）。卡片、按钮、排版等简单场景优先 Tailwind。
10. **TagBadge 颜色**：使用 `tokens.ts` 中的 `colors.primary` 作为默认色，不再硬编码 `#1677ff`。

### 深色模式

11. 所有页面和组件在浅色模式下必须视觉正确。深色模式适配（CSS 变量桥接 + antd darkAlgorithm）基础设施已完成，但具体页面的深色视觉效果尚未精细打磨，标记为待完善。

### 响应式

12. 桌面端优先，PageContainer 的 padding 已内置响应式（`px-4 sm:px-6 lg:px-8`）。新增页面无需额外处理。

### 构建

13. 提交前必须 `pnpm build` 通过（零 TypeScript 错误）。允许的 warning：`ReferenceError: location is not defined`（来自 `layout.tsx` 中的防闪烁 script，SSR 期间无害）。

---

## 当前状态

- [x] 阶段一：基础骨架 + 认证（已完成）
- [x] 阶段二：Q&A 核心（已完成）
- [x] 阶段三：前端设计大规模重构与统一（已完成）
  - 设计 Token 系统 + 深色模式基础设施
  - 布局原语（PageContainer / PageHeader）
  - UI 原语（LoadingState / EmptyState / ListPagination）
  - 18 个页面 + 10 个组件 Tailwind 迁移
  - 内联样式从 178 处降至 5 处（仅合法动态样式）
  - 深色模式基础切换已生效，具体页面的暗色视觉细节待完善
- [ ] 阶段四：搜索 + 通知 + 用户主页
- [ ] 阶段五：优化增强
