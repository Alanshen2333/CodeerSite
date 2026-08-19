# 阶段 1 前后端结构规划

> 配合 [`docs/adr/0001-gitea-vcs-integration.md`](../adr/0001-gitea-vcs-integration.md) 使用：ADR 记架构决策（为什么），本文件记实施结构（怎么做）。
> 状态：规划中（2026-07-03）。1.1（Gitea 部署）见 GitHub Issue #8。

## 范围

阶段 1（地基）步骤 1.2–1.7 的后端/前端结构。1.1 由 teammate 执行。

## 设计原则

1. **优雅降级**——GiteaClient 通过 `_is_available()` 检查配置+连通性，Gitea 挂了不阻断 Codeersite 核心（Q&A/项目/Issue 照常工作），只记 warning。
2. **token 不出后端**——用户 Gitea token 用 Fernet 加密存 `User.gitea_token_encrypted`，永不返回前端；前端永远走 Codeersite BFF。
3. **Project:Repo = 1:1 可选关联**——Project 可无 repo；有则 `gitea_full_name` 如 `codeersite/my-repo`。
4. **仓库归 `codeersite` org**——org 全局唯一，所有 repo 在 org 下。

## 后端文件清单

| 文件 | 动作 | 职责 |
|---|---|---|
| `pyproject.toml` | 改 | +`httpx`、`cryptography` |
| `src/api/app/config.py` | 改 | Config 加 `GITEA_URL`/`GITEA_ADMIN_TOKEN`/`GITEA_ORG`/`GITEA_TOKEN_ENCRYPTION_KEY`；TestConfig 关闭 Gitea |
| `.env.example` | 改 | 同步配置项（1.1 已加基础段，这里补 `GITEA_TOKEN_ENCRYPTION_KEY`） |
| `src/api/app/utils/crypto.py` | 新 | `encrypt_token`/`decrypt_token`（Fernet，key 从 config 读） |
| `src/api/app/services/gitea_client.py` | 新 | Gitea HTTP 客户端，静态方法类 |
| `src/api/app/models/user.py` | 改 | +`gitea_user_id`(str,index,nullable)、`gitea_token_encrypted`(text,nullable) |
| `src/api/app/models/project.py` | 改 | +`gitea_repo_id`(str,index,nullable)、`gitea_full_name`(str,nullable) |
| `src/api/migrations/versions/xxx_gitea_fields.py` | 新 | Alembic autogenerate |
| `src/api/app/services/auth_service.py` | 改 | `register_user` 末尾桥接 Gitea |
| `src/api/app/api/repos.py` | 新 | repos 蓝图（POST/GET `/projects/<slug>/repo`） |
| `src/api/app/schemas/repo.py` | 新 | `RepoCreateSchema` |
| `src/api/app/__init__.py` | 改 | 注册 `repos_bp`（挂 `/api`，路由内含 `/projects/<slug>/repo`，与 issues 一致） |
| `src/api/tests/test_gitea_integration.py` | 新 | mock GiteaClient 的集成测试 |

## GiteaClient 设计（`services/gitea_client.py`）

```python
class GiteaClient:
    """Gitea API 客户端。Gitea 不可用时降级，不抛异常。"""

    @staticmethod
    def _is_available() -> bool: ...        # 检查 GITEA_URL + ADMIN_TOKEN 已配置且连通

    # —— admin 操作（用 ADMIN_TOKEN）——
    @staticmethod
    def admin_create_user(username, email, password) -> dict | None: ...
    @staticmethod
    def admin_create_org(name) -> dict | None: ...      # 幂等，codeersite org
    @staticmethod
    def admin_create_user_token(username, token_name) -> str | None: ...
    @staticmethod
    def admin_create_repo(org, name, private) -> dict | None: ...
    @staticmethod
    def get_repo(org, name) -> dict | None: ...

    # —— 用户代理（阶段2+ 用，阶段1只占位）——
    @staticmethod
    def for_user(user_token: str) -> "UserGiteaClient": ...
```

- 模块级 `httpx.Client` 单例（连接池），timeout 短（3s）避免拖慢请求。
- 所有方法 Gitea 不可用时返回 `None`，调用方自行降级。

## 认证桥接（`auth_service.py` 的 `register_user`）

```
register_user(...) 现有逻辑
  → 创建 User 入库
  → if GiteaClient._is_available():
       gitea_user = admin_create_user(...)           # 失败则 gitea_user_id=None，记 warning
       if gitea_user:
           token = admin_create_user_token(...)
           user.gitea_user_id = gitea_user["id"]
           user.gitea_token_encrypted = encrypt_token(token)
           db.session.commit()
  → 返回 user（gitea 字段为 None 不影响注册成功）
```

## repos 蓝图（`api/repos.py`）

| 方法 | 路由 | 权限 | 行为 |
|---|---|---|---|
| POST | `/api/projects/<slug>/repo` | owner/admin | 在 `codeersite` org 下创建 repo（名 = project slug），写 `project.gitea_repo_id`/`gitea_full_name`；Gitea 不可用→503 |
| GET | `/api/projects/<slug>/repo` | 项目可见 | 返回 repo 元信息（name/description/default_branch/web_url）；无 repo→404 |

- 复用 `_get_project_or_404(slug)` helper、`ProjectService.get_user_role` 权限检查。
- 遵循 controller 契约：Schema 校验→422、权限→403、404 helper、`jsonify(error,message),code`。

## 前端（阶段 1 轻量，重头在阶段 2）

| 文件 | 动作 | 职责 |
|---|---|---|
| `src/web/src/types/repo.ts` | 新 | `Repo` 类型 |
| `src/web/src/lib/api/repos.ts` | 新 | `createRepo(slug, payload)` / `getRepo(slug)` |
| `src/web/src/app/projects/[slug]/settings/...` | 改 | 设置页加"仓库"区块（创建按钮 + repo 信息展示） |

前端阶段 1 就这些——把 repo 创建入口接到项目设置页，让 e2e 能跑通"建项目→建仓库"。浏览/diff/PR UI 全留阶段 2-3。

## 测试策略（`test_gitea_integration.py`）

参照 `conftest.py` 内存 SQLite + 现有 `_login`/`_create_project` helper，**mock GiteaClient**（不打真实 Gitea）：

- `test_register_creates_gitea_user` — mock `admin_create_user` 返回 dict，断言 `user.gitea_user_id` 已存、`gitea_token_encrypted` 非空。
- `test_register_degrades_when_gitea_down` — mock `_is_available=False`，注册仍 201，gitea 字段为 None。
- `test_create_repo` — owner 建仓库 201，非 owner 403。
- `test_get_repo` — 有 repo 200，无 repo 404。

## 数据流总览

```
用户注册 → AuthService → GiteaClient.admin_create_user → token 加密存 User
建项目   → 现有 ProjectService（不动）
建仓库   → repos 蓝图 → GiteaClient.admin_create_repo（admin token）→ 写 Project.gitea_*
前端     → /api/projects/<slug>/repo → BFF 转发 Gitea（用户不直连 Gitea）
```