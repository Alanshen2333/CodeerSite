# ADR-0001: Gitea 集成实现版本控制与 PR 流程

- 状态：Accepted
- 日期：2026-07-03
- 决策者：alan

## 背景

Codeersite 已具备项目管理能力（Project / Issue / Milestone / 看板 / 成员 / 角色），但缺少代码托管与变更审查能力。路线图曾将 MR / 代码审查列为「缓做」（理由：依赖 git 集成 + diff + 行级评论）。2026-07-03 决策正式推进，目标是补齐仓库浏览、commit 历史、PR（含 review / 行级评论 / merge）的完整流程。

自研 Git 托管（Git 协议、对象存储、权限）成本过高；iframe 嵌入第三方 UI 体验割裂。选用 Gitea 作为 Git 存储后端，前端定制以保持 Codeersite UI 一致性。

## 决策

采用 **Gitea + BFF + Codeersite IdP** 架构：

1. **Gitea 作 Git 存储后端**：仓库、Git 对象、Git 协议交给 Gitea，不自研。
2. **Codeersite 后端做 BFF**：新增 `repos` / `pulls` 蓝图封装 Gitea API；前端只对接 Codeersite API，不直连 Gitea（统一认证 / CORS / 错误格式 `{"error","message"}`）。
3. **Codeersite 作 IdP**：Gitea 不对终端用户暴露 Web UI；用户在 Codeersite 登录后，后端代为管理 Gitea 用户与 token，token 加密缓存于 User 表，请求时以**该用户的** Gitea token 转发——权限隔离天然正确。
4. **单一事实源**：Issue / Milestone / 看板 继续用 Codeersite；Git 仓库 / 分支 / commit / PR 用 Gitea。关闭 Gitea 自带的 Issue / Milestone / 看板，避免双轨。
5. **Project ↔ Repo 严格 1:1**：一个 Project 关联一个 Gitea 仓库。
6. **Gitea 数据库**：复用现有 PostgreSQL 实例，新建独立 `gitea` database，避免与 Codeersite 的 schema 命名空间冲突；Gitea 迁移由 Gitea 自管，不进 Codeersite 的 Alembic。

## 部署与认证桥接

### 部署

`docker/docker-compose.dev.yml` 增加 `gitea` service，与 `postgres` 并列。Gitea 连接同一个 PostgreSQL 实例的 `gitea` database。Gitea Web 端口仅对内部 / 调试暴露，不对终端用户发布。

### 认证与 token 流转

- **注册**：Codeersite 注册用户成功后，后端调 Gitea admin API 同步创建 Gitea 用户。
- **登录**：Codeersite 登录成功后，后端用 Gitea API 为该用户生成 personal access token，加密缓存到 `User.gitea_token_encrypted`。
- **请求转发**：前端调 Codeersite API → 后端取当前用户的 Gitea token → 以该 token 调 Gitea API → 透传 / 聚合结果。权限隔离由 Gitea 按 token 所属用户裁决。
- **token 失效**：Gitea 返回 401 时，后端用 service token 重新为该用户签发并重试一次。

## 后端设计

### 新增

- `src/api/app/services/gitea_client.py`：封装 Gitea API（httpx），含 service token 管理、用户 token 缓存与重签发、统一错误转换。
- `src/api/app/api/repos.py` 蓝图（前缀 `/api`，路由内含 `/projects/<slug>/repos/...`）：仓库 CRUD、文件树、文件内容、commit 历史、分支列表、diff。
- `src/api/app/api/pulls.py` 蓝图：PR 列表 / 详情 / 创建 / 评论 / review / merge。
- Webhook 端点：接收 Gitea push / PR 事件，更新 commit 活动、PR 状态。

### 模型扩展

- `User`：加 `gitea_user_id`（int）、`gitea_token_encrypted`（加密字符串，可空）。
- `Project`：加 `gitea_repo_id`（int）、`gitea_full_name`（如 `owner/repo`，可空；1:1 下唯一约束）。
- 行级评论：复用现有 Comment 多态（`target_type="pull"` + `target_id`），新增可选字段 `file_path` / `line` / `commit_sha` / `side`（LEFT / RIGHT）。量小，先加字段而非新建模型。

### 迁移

User / Project 字段扩展走 Alembic autogenerate。Gitea 自身 schema 在 `gitea` database 内由 Gitea 启动时自动迁移，不进 Alembic。

## 前端设计

### 页面

- `src/web/src/app/projects/[slug]/repos/`：仓库入口（1:1 下即该 Project 的唯一仓库）。
- 仓库详情：文件树 + 文件内容 + 分支切换 + commit 历史。
- PR 列表 / 详情：diff 视图 + 行级评论 + review 状态 + merge。
- 新建 PR 表单：源 / 目标分支选择。

### 组件与选型

- 语法高亮：shiki（SSR 友好）。
- diff 渲染：`react-diff-viewer-continued` 或自研轻量版（待步骤计划定）。
- API 模块：`src/lib/api/repos.ts`。
- 遵循现有设计 Token / PageContainer / PageHeader / LoadingState / EmptyState 约定。

## 分阶段计划

每个阶段实施前单独写详细计划交 alan 审核。

| 阶段 | 内容 | 产出 |
|---|---|---|
| 1 地基 | docker-compose 加 gitea + `gitea_client` + User/Project 字段扩展 + 认证桥接 + 仓库 CRUD + Project↔Repo 关联 | 后端可代理 Gitea，能创建仓库并关联 Project |
| 2 只读浏览 | 文件树 + 文件内容（shiki）+ commit 历史 + 分支切换 | **MVP**：前端可浏览代码 |
| 3 PR 核心 | PR 列表 / 详情 / 创建 + diff 视图 + merge | 可走通 PR 流程 |
| 4 协作 | 行级评论 + review + webhook 同步 | 完整审查体验 |

## 后果

- **新增依赖**：Gitea service（docker-compose）、`httpx`（后端，如未装）、`shiki` + diff 组件（前端）。
- **数据模型变更**：User / Project 加字段；Comment 加可选行级评论字段。需迁移。
- **部署变更**：dev / prod compose 都要加 gitea service 与 `gitea` database。
- **运维**：Gitea 需备份 `gitea` database + 仓库存储卷。
- **未覆盖**：Releases / Tag、CI/CD Pipeline 仍为缓做，不在本 ADR 范围。

## 待办

- [ ] 阶段 1 详细计划（交审核）
- [ ] 阶段 2 详细计划
- [ ] 阶段 3 详细计划
- [ ] 阶段 4 详细计划
