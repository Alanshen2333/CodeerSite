# Codeersite

面向开发者的社区平台 — 融合 **StackOverflow 问答** 与 **GitLab 项目管理**。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 API | Flask 3 + SQLAlchemy 2.0 + Marshmallow |
| 前端 | Next.js 14 (App Router) + Ant Design 5 + Tailwind CSS |
| 主数据库 | PostgreSQL 16 |
| 辅助存储 | MongoDB 7（搜索索引、通知、活动日志） |
| 认证 | JWT (Flask-JWT-Extended) |
| 包管理 | uv (Python) + pnpm (Node.js) |

## 项目结构

```
Codeersite/
├── src/
│   ├── api/                  # Flask 后端
│   │   ├── app/
│   │   │   ├── api/          # 蓝图路由
│   │   │   ├── models/       # SQLAlchemy 数据模型
│   │   │   ├── schemas/      # Marshmallow 序列化
│   │   │   ├── services/     # 业务逻辑
│   │   │   └── utils/        # 工具函数
│   │   ├── migrations/       # Alembic 迁移
│   │   └── wsgi.py           # 入口
│   └── web/                  # Next.js 前端
│       └── src/
│           ├── app/          # App Router 页面
│           ├── components/   # 可复用组件
│           ├── providers/    # React Context
│           ├── lib/          # Axios/Auth 工具
│           └── types/        # TypeScript 类型
├── docker/
│   └── docker-compose.dev.yml
├── pyproject.toml
└── alembic.ini
```

## 快速开始

### 前置条件

- Python 3.14+
- Node.js 20+
- Docker（运行数据库）
- uv、pnpm

### 1. 启动数据库

```bash
docker compose -f docker/docker-compose.dev.yml up -d
```

### 2. 后端

```bash
# 安装依赖
uv sync

# 运行数据库迁移
uv run alembic upgrade head

# 启动开发服务器 (http://localhost:5000)
uv run flask --app src/api/wsgi:app run --debug -p 5000
```

### 3. 前端

```bash
cd src/web

# 安装依赖
pnpm install

# 启动开发服务器 (http://localhost:3000)
pnpm dev
```

### 4. 验证

```bash
# 测试注册
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@test.com","password":"demo123"}'

# 测试登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@test.com","password":"demo123"}'
```

## API 概览

| 模块 | 前缀 | 主要端点 |
|------|------|----------|
| 认证 | `/api/auth` | register, login, refresh, me |
| 用户 | `/api/users` | 列表, 详情, 活动 |
| 问答 | `/api/questions` | CRUD, 投票, 采纳 |
| 项目 | `/api/projects` | CRUD, 成员, Issue, 看板, 里程碑 |
| 搜索 | `/api/search` | 全局全文搜索 |
| 通知 | `/api/notifications` | 列表, 已读 |

## 环境变量

复制 `.env.example` 为 `.env` 并修改：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FLASK_ENV` | 运行环境 | `production` |
| `SECRET_KEY` | Flask 密钥 | — |
| `DATABASE_URL` | PostgreSQL 连接 | `postgresql+psycopg://...` |
| `MONGO_URI` | MongoDB 连接 | `mongodb://localhost:27017/codeersite` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | — |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:3000` |

## 开发阶段

- [x] 阶段一：基础骨架 + 认证
- [ ] 阶段二：Q&A 核心（进行中）
- [ ] 阶段三：项目管理
- [ ] 阶段四：搜索 + 通知 + 用户主页
- [ ] 阶段五：优化增强
