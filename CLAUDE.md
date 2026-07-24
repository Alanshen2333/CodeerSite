# CLAUDE.md — Codeersite 项目指南

> 本文件是 Codeersite 的**唯一项目文档源**。Codex 工作流通过 `AGENTS.md` 指向此处；修改文档只改本文件，勿在两处重复维护。

## 项目概述

Codeersite 融合 StackOverflow 式问答与 GitLab 式项目管理，面向开发者社区。

- 后端：Flask 3 REST API（`src/api/`）
- 前端：Next.js 16 + React 19 + Ant Design 6 + Tailwind CSS v4（`src/web/`）
- 数据库：PostgreSQL 16（主存储，含全文搜索 search_documents）、MongoDB 7（通知/JWT 吊销）
- 包管理：uv（Python）、pnpm（Node）

## 技术栈版本（以 lockfile 为准）

| 层 | 技术 | 版本 |
|---|---|---|
| 后端框架 | Flask | ≥3.1 |
| ORM | SQLAlchemy（flask-sqlalchemy） | ≥2.0 |
| 序列化 | Marshmallow + marshmallow-sqlalchemy | ≥3 / ≥1 |
| 认证 | flask-jwt-extended | ≥4 |
| 密码 | flask-bcrypt | ≥1 |
| Markdown | mistune | ≥3（服务端渲染 body→body_html） |
| 前端框架 | Next.js | 16.2 |
| UI 库 | Ant Design | 6.4（图标用 @ant-design/icons 6.x） |
| 样式 | Tailwind CSS | v4（@tailwindcss/postcss） |
| 表单 | react-hook-form + zod | — |
| 主库 | PostgreSQL | 16 |
| 辅助库 | MongoDB | 7 |

## 常用命令

```bash
# 一键启动（推荐）：拉起 PG+Mongo、跑迁移、起 Flask+Next
scripts/dev.sh

# 数据库
docker compose -f docker/docker-compose.dev.yml up -d

# 后端
uv sync
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "描述"
uv run flask --app src/api/wsgi:app run --debug -p 5000

# 前端
cd src/web && pnpm install
cd src/web && pnpm dev
cd src/web && pnpm build      # 提交前必过

# 测试
uv run pytest
```

## 后端架构

- **工厂模式**：`create_app(config_name)` 在 `src/api/app/__init__.py`；按 `FLASK_ENV` 选 development/production/test，默认 production。
- **蓝图路由**：`src/api/app/api/*.py`，每文件一蓝图，前缀在 `register_blueprints()` 集中注册。
  - 注意：issues / milestones / kanban 三个蓝图挂在 `/api`，路由内自带 `/projects/<slug>/...` 前缀，而非各自独立前缀。
- **服务层**：`src/api/app/services/`，控制器只做参数校验与响应，业务逻辑下沉到 service。
- **模型**：`src/api/app/models/`，SQLAlchemy ORM，UUID 字符串主键，时区感知时间。
- **序列化**：`src/api/app/schemas/`，Marshmallow。
- **工具**：`utils/decorators.py`（`admin_required` / `moderator_required`）、`utils/errors.py`（全局错误处理，统一返回 `{"error","message"}` + 状态码）。
- **扩展**：`extensions.py` 初始化 db / jwt / cors / bcrypt / mongo。
- **配置**：`config.py`，development / production / test；production 强制校验 `SECRET_KEY` / `JWT_SECRET_KEY` 不得为默认值。
- **迁移**：Alembic，`alembic.ini`（`script_location=src/api/migrations`，`prepend_sys_path=src/api`）；`migrations/env.py` 创建 app 以读取 Flask 配置并覆盖 `sqlalchemy.url`。

### 认证

- JWT via flask-jwt-extended；access 1h，refresh 30d。
- `user_lookup_loader` 从 `sub`（user id 字符串）加载 User。
- token 吊销（blocklist）存于 MongoDB；Mongo 不可用时 blocklist 检查返回 False（即不可吊销，降级）。
- 角色：user / moderator / admin。

### MongoDB 优雅降级

- `init_extensions` 懒连接并 ping；失败则 `mongo_db=None` 且不阻断启动。
- NotificationService 有 `_is_available()`，Mongo 不可用时返回空结果而非报错。
- 搜索已迁 PostgreSQL（`search_documents` 表，tsvector + pg_trgm），索引写入与业务数据同事务，不依赖 Mongo；存量数据用 `scripts/reindex_search.py` 回填。

### 数据模型约定

- UUID 字符串主键；`created_at` / `updated_at` 时区感知。
- `vote_count` 反范式缓存在主表（读多写少）。
- Markdown `body` 写入时服务端用 mistune 渲染为 `body_html` 缓存。
- Issue 使用项目内自增编号 `issue_number`。
- 多态关联（votes / comments / bookmarks）通过 `target_type` + `target_id`。
- 看板：KanbanColumn → KanbanCard（可关联 Issue）；Milestone 聚合 open/closed issue 计数。

### 服务层契约

- Service 为静态方法类（如 `IssueService.create_issue(...)`），方法返回 ORM 对象 / `Pagination` / `dict`，内部自行 `db.session.commit()`，不抛业务异常。
- Controller 职责：参数校验（Marshmallow `Schema().load()`，`ValidationError` → 422）、权限判断（`ProjectService.get_user_role`）、404/403 响应、`model.to_dict()` 序列化。
- 通用 404 helper：`_get_project_or_404(slug) -> (project, err)`，controller `if err: return err`。
- 错误响应统一 `jsonify(error=..., message=...), code`；`utils/errors.py` 兜底未捕获异常。

## 前端架构

- **路由**：App Router，页面在 `src/web/src/app/`；`(auth)` 路由组放 login / register。
- **组件**：`src/web/src/components/{layout,project,qa,ui}`。
- **状态**：React Context —— `AuthProvider`、`ThemeProvider`（antd darkAlgorithm + CSS 变量桥接）。
- **HTTP**：`src/lib/api.ts`（axios 实例，自动附加 token、401 自动 refresh、并发去重）；各模块 API 在 `src/lib/api/`。
- **认证 token**：`src/lib/auth.ts`（localStorage 存取 access / refresh token）。
- **类型**：`src/web/src/types/`。
- **代理**：`next.config.ts` 将 `/api/*` rewrites 到 `localhost:5000`，故前端用相对路径，无 CORS 问题。

### 数据获取

- HTTP 层：`src/lib/api.ts`（axios 实例 + 拦截器：自动附 token、401 自动 refresh 并发去重）；按模块拆分 `src/lib/api/*.ts` 导出 API 函数。
- 页面数据获取：手动 `useEffect` + API 函数（未引入 SWR / React Query）；分页走 query string。
- 表单：`react-hook-form` + `zod` 校验。

### API 概览

| 模块 | 前缀 | 主要端点 |
|---|---|---|
| 认证 | /api/auth | register, login, refresh, me(GET/PATCH) |
| 用户 | /api/users | 列表, /<username>, /<username>/{questions,answers} |
| 标签 | /api/tags | 列表, /<slug>, 创建 |
| 问答 | /api/questions | CRUD, close/reopen, pin |
| 回答 | /api/answers | CRUD, accept/unaccept |
| 投票 | /api/votes | 创建/删除（多态） |
| 评论 | /api/comments | CRUD（多态） |
| 收藏 | /api/bookmarks | 列表/创建/check（多态） |
| 项目 | /api/projects | CRUD, 成员, star |
| Issue | /api（内含 /projects/<slug>/issues） | CRUD |
| 里程碑 | /api（内含 /projects/<slug>/milestones） | CRUD |
| 看板 | /api（内含 /projects/<slug>/kanban） | columns CRUD/reorder, cards CRUD/move |
| 搜索 | /api/search | 全文搜索 |
| 通知 | /api/notifications | 列表, unread-count, read, read-all |
| 管理 | /api/admin | stats, 用户管理（admin_required） |
| 文档 | /api/docs | API 文档 |

## 前端开发守则

参考 Linear / Notion / Vercel Dashboard —— 现代、简洁、专业。

1. **禁止硬编码样式**：不得写 `style={{ color:"#xxx", fontSize:14, ... }}`；颜色/间距/字号来自设计 Token，仅 antd 主题动态值允许 `style`。
2. **Tailwind 优先**：布局/间距/排版/背景/边框用 Tailwind 工具类。
3. **设计 Token 唯一源（两处必须同步）**：
   - TS 侧：`src/web/src/styles/tokens.ts`（同时供给 antd ConfigProvider）。
   - CSS 侧：`src/web/src/app/globals.css` 的 `@theme` 块。
   - 语义色通过 CSS 变量 `var(--tw-color-*)` 桥接，`:root` / `.dark` 分别定义浅/深色，类名自动跟随主题切换，无需手写 `dark:` 变体。
4. **页面容器**：每页最外层用 `<PageContainer size="wide|default|narrow">`（960/800/640px），禁止手写 maxWidth+margin；全宽页用 `className="p-6"`。
5. **页面标题**：列表页用 `<PageHeader title actions breadcrumb/>`。
6. **UI 原语**：加载 `<LoadingState/>`、空态 `<EmptyState/>`、分页 `<ListPagination/>`。
7. **共享常量**：priorityColor/Label、issueStatusColor/Label、visibilityLabel、roleLabel、milestoneStatusLabel 从 `src/web/src/styles/constants.ts` 导入。
8. **antd 职责边界**：只用于复杂交互（Form/Table/Modal/Select/Dropdown/Menu/Pagination/DatePicker）；卡片/按钮/排版优先 Tailwind。
9. **图标**：用 `@ant-design/icons`（非 lucide）。
10. **TagBadge**：默认色用 `tokens.ts` 的 `colors.primary`，不硬编码。
11. **深色模式**：浅色必须正确；深色基础设施已就绪（CSS 变量桥接 + antd darkAlgorithm），具体页面暗色细节待打磨。
12. **响应式**：桌面优先，PageContainer 已内置响应式 padding。
13. **构建**：提交前 `pnpm build` 零 TS 错误；允许 `ReferenceError: location is not defined` 警告（layout.tsx 防闪烁脚本，SSR 无害）。

## 代码风格

- Python：类型注解，`User | None` 语法。
- TypeScript：接口在 `types/`。
- 错误处理：后端 `{"error","message"}` + HTTP 状态码。
- 中文注释与文档。

## 测试约定

- 测试位于 `src/api/tests/`；`conftest.py` 提供 `app`（test 配置 + PostgreSQL `codeersite_test` 数据库，每个测试自动重建 schema）、`client`、`auth_headers` fixtures。
- 本地运行测试前需先启动 PostgreSQL：`docker compose -f docker/docker-compose.dev.yml up -d postgres`。
- 可通过环境变量 `DATABASE_URL` 覆盖测试数据库地址。
- 集成测试为主：通过 test client 打真实 HTTP，用 `_login` / `_create_project` 等辅助函数构造前置数据，断言响应状态码与 JSON；相关用例聚合为 `class TestXxx:`。
- 不连真实 PG / Mongo；外部依赖（如 Gitea）用 mock，勿打真实服务。
- 运行：`uv run pytest`。

## 环境变量

见 `.env.example`（唯一源，含说明与默认值）。

## 当前状态

- [x] 阶段一：基础骨架 + 认证
- [x] 阶段二：Q&A 核心
- [x] 阶段三：前端设计重构与统一
- [x] 阶段四：搜索 + 通知 + 用户主页
- [ ] 阶段五：优化增强
  - [x] 看板拖拽收尾 + issues/new 与 settings 表单页
  - [x] 优先闭环四项（均带后端测试）：Star 真实化、加成员、Issue 评论流、Labels 关联 Issue
  - [x] 徽章管理面板（已起步）

## Agent skills

### Issue tracker

GitHub Issues，使用 `gh` CLI 操作；外部 PR 不作为 triage 来源。详见 `docs/agents/issue-tracker.md`。

### Triage labels

使用默认标签名：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。详见 `docs/agents/triage-labels.md`。

### Domain docs

单上下文布局：根目录 `CONTEXT.md` + `docs/adr/`。详见 `docs/agents/domain.md`。
