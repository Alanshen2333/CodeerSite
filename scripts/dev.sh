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
echo -e "\n${YELLOW}[1/3] Docker 服务...${NC}"
if docker compose -f "$ROOT/docker/docker-compose.dev.yml" ps --status running 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}  ✓ PostgreSQL + MongoDB 已在运行${NC}"
else
    echo "  启动中..."
    docker compose -f "$ROOT/docker/docker-compose.dev.yml" up -d
    echo -e "${GREEN}  ✓ 已启动${NC}"
    sleep 2
fi

# 2. DB Migration
echo -e "\n${YELLOW}[2/3] 数据库迁移...${NC}"
cd "$ROOT"
uv run alembic upgrade head
echo -e "${GREEN}  ✓ 迁移完成${NC}"

# 3. Start Flask + Next.js
echo -e "\n${YELLOW}[3/3] 启动服务...${NC}"

# Flask (background)
cd "$ROOT/src/api"
uv run flask run --debug --port 5000 &
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
echo -e "  ${BLUE}后端 API :${NC} http://localhost:5000/api"
echo -e "  ${BLUE}前端页面 :${NC} http://localhost:3000"
echo -e "  ${RED}按 Ctrl+C 停止${NC}"
echo -e "${BLUE}========================================${NC}"

wait
