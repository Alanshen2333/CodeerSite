# Codeersite

面向开发者的社区平台 — 融合 **StackOverflow 问答** 与 **GitLab 项目管理**。

> 完整项目文档（架构、开发规则、API、环境变量、当前状态）见 [`CLAUDE.md`](./CLAUDE.md)。本文件仅面向开发者快速上手。

## 前置条件

- Python 3.14+、Node.js 20+、Docker
- uv（Python）、pnpm（Node）

## 快速开始

### 一键启动（推荐）

```bash
scripts/dev.sh
```

拉起 PostgreSQL + MongoDB、跑迁移、启动 Flask + Next.js。

### 分步启动

```bash
# 1. 数据库
docker compose -f docker/docker-compose.dev.yml up -d

# 2. 后端 (http://localhost:5000)
uv sync
uv run alembic upgrade head
uv run flask --app src/api/wsgi:app run --debug -p 5000

# 3. 前端 (http://localhost:3000)
cd src/web && pnpm install && pnpm dev
```

### 验证

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@test.com","password":"demo123"}'
```

### 测试

```bash
# 确保 PostgreSQL 已启动
docker compose -f docker/docker-compose.dev.yml up -d postgres

# 运行后端测试
uv run pytest src/api/tests
```

## 项目结构

```
Codeersite/
├── src/
│   ├── api/                  # Flask 后端
│   │   ├── app/{api,models,schemas,services,utils}/
│   │   ├── migrations/       # Alembic
│   │   ├── tests/            # pytest
│   │   └── wsgi.py
│   └── web/                  # Next.js 前端
│       └── src/{app,components,providers,lib,types}/
├── docker/
├── docs/                     # 含 adr/、agents/
├── scripts/
├── pyproject.toml
└── alembic.ini
```

## 文档

- [`CLAUDE.md`](./CLAUDE.md) — 唯一项目文档源
- [`.env.example`](./.env.example) — 环境变量清单
- [`docs/adr/`](./docs/adr/) — 架构决策记录