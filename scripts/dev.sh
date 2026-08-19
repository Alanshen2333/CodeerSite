#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Codeersite 开发环境${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. Docker
echo -e "\n${YELLOW}[1/3] Docker 服务（PostgreSQL + Gitea）...${NC}"
docker compose -f "$ROOT/docker/docker-compose.dev.yml" up -d
echo -e "${GREEN}  ✓ PostgreSQL + Gitea 已就绪${NC}"
sleep 2

# 2. DB Migration
echo -e "\n${YELLOW}[2/3] 数据库迁移...${NC}"
cd "$ROOT"
uv run alembic upgrade head
echo -e "${GREEN}  ✓ 迁移完成${NC}"

# 3. Load environment
echo -e "\n${YELLOW}[3/3] 加载环境变量...${NC}"
if [ -f "$ROOT/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$ROOT/.env"
    set +a
    echo -e "${GREEN}  ✓ 已加载 .env${NC}"
else
    echo -e "${YELLOW}  ⚠ 未找到 $ROOT/.env，将使用默认配置${NC}"
fi

# 4. Start Flask + Next.js
echo -e "\n${YELLOW}[4/4] 启动服务...${NC}"

# Flask (background)
# 注意：macOS 的"隔空播放接收器"(ControlCenter) 默认占用 5000 端口（IPv6 ::1），
# 用 localhost:5000 会被它拦截并返回 403，故后端改用 5100。
# 前端 next.config.ts 的 rewrite 需同步指向同一端口。
cd "$ROOT"
uv run flask --app src/api/wsgi:app run --debug --port 5100 &
FLASK_PID=$!

# Next.js (background)
cd "$ROOT/src/web"
pnpm dev &
NEXT_PID=$!

cleanup() {
    echo -e "\n${YELLOW}正在停止...${NC}"
    kill $FLASK_PID 2>/dev/null
    kill $NEXT_PID 2>/dev/null
    echo -e "${GREEN}已停止${NC}"
}
trap cleanup EXIT INT TERM

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  开发环境已就绪！${NC}"
echo -e "  ${BLUE}后端 API :${NC} http://localhost:5100/api"
echo -e "  ${BLUE}前端页面 :${NC} http://localhost:3000"
echo -e "  ${BLUE}Gitea    :${NC} http://localhost:23000"
echo -e "  ${YELLOW}首次使用 Gitea 需运行：bash scripts/init-gitea.sh${NC}"
echo -e "  ${RED}按 Ctrl+C 停止${NC}"
echo -e "${BLUE}========================================${NC}"

wait
