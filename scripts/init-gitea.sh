#!/usr/bin/env bash
# 幂等初始化 Gitea：确保 gitea database、admin 用户、bot token 就绪。
# 用法：bash scripts/init-gitea.sh
#
# 可被反复执行；已存在的资源会跳过。bot token 的 sha1 仅创建时返回一次，
# 若已存在则无法再次获取（需删除后重建）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$ROOT/docker/docker-compose.dev.yml"

# 默认值与 .env.example 保持一致；允许环境变量覆盖。
GITEA_URL="${GITEA_URL:-http://localhost:23000}"
GITEA_ADMIN_USER="${GITEA_ADMIN_USER:-codeersite-admin}"
GITEA_ADMIN_PASS="${GITEA_ADMIN_PASS:-codeersite-admin-dev}"
GITEA_ORG="${GITEA_ORG:-codeersite}"
TOKEN_NAME="codeersite-bot"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

info() { echo -e "${BLUE}[i]${NC} $*"; }
ok()   { echo -e "${GREEN}  ✓${NC} $*"; }
warn() { echo -e "${YELLOW}  !${NC} $*"; }
die()  { echo -e "${RED}  ✗${NC} $*" >&2; exit 1; }

# --- 0. 兜底创建 gitea database ---------------------------------------------
# postgres 的 init 脚本只在 pgdata 首次初始化时跑；若 pgdata 已存在则需这里补建。
info "确保 gitea database 存在..."
if docker exec codeersite-pg psql -U codeersite -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='gitea'" 2>/dev/null | grep -q 1; then
  ok "gitea database 已存在"
else
  docker exec codeersite-pg psql -U codeersite -d postgres -c \
    "CREATE DATABASE gitea OWNER codeersite" >/dev/null
  ok "已创建 gitea database"
fi

# --- 1. 启动 / 拉起 gitea 容器 ----------------------------------------------
# 若 gitea 之前因 database 缺失而 crash，此处 up 会重新拉起。
info "确保 gitea 容器运行..."
docker compose -f "$COMPOSE" up -d gitea >/dev/null

# --- 2. 等待 Gitea API 就绪 -------------------------------------------------
info "等待 Gitea API 就绪（首次启动需做 DB 迁移，可能耗时十余秒）..."
ready=0
for _ in $(seq 1 60); do
  if curl -sf "$GITEA_URL/api/v1/version" >/dev/null 2>&1; then
    ready=1; break
  fi
  sleep 2
done
[[ $ready -eq 1 ]] || die "Gitea 未就绪，请检查：docker logs codeersite-gitea"
ok "Gitea API 就绪"

# --- 3. 创建 admin 用户（已存在则跳过）--------------------------------------
info "确保 admin 用户 $GITEA_ADMIN_USER ..."
set +e
create_out=$(docker exec -u git codeersite-gitea gitea admin user create \
    --admin --username "$GITEA_ADMIN_USER" --password "$GITEA_ADMIN_PASS" \
    --email "codeersite-admin@local" --must-change-password=false 2>&1)
rc=$?
set -e
if echo "$create_out" | grep -qi "already exists"; then
  ok "admin 用户已存在，跳过"
elif [[ $rc -eq 0 ]]; then
  ok "已创建 admin 用户 $GITEA_ADMIN_USER"
else
  die "创建 admin 用户失败：$create_out"
fi

# --- 4. 创建 bot token（已存在则跳过）---------------------------------------
info "确保 token $TOKEN_NAME ..."
existing=$(curl -sf -u "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASS" \
    "$GITEA_URL/api/v1/users/$GITEA_ADMIN_USER/tokens" 2>/dev/null || echo "[]")
if echo "$existing" | grep -q "\"name\":\"$TOKEN_NAME\""; then
  warn "token $TOKEN_NAME 已存在（sha1 仅创建时返回一次，无法再次获取）"
  warn "如需重置：在 Gitea Web 删除该 token 后重新运行本脚本"
else
  resp=$(curl -sf -u "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASS" \
      -X POST "$GITEA_URL/api/v1/users/$GITEA_ADMIN_USER/tokens" \
      -H "Content-Type: application/json" \
      -d "{\"name\":\"$TOKEN_NAME\",\"scopes\":[\"all\"]}")
  token=$(echo "$resp" | sed -n 's/.*"sha1":"\([^"]*\)".*/\1/p')
  [[ -n "$token" ]] || die "token 创建失败：$resp"
  ok "已创建 token $TOKEN_NAME"
  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  Gitea bot token（仅此一次显示）：${NC}"
  echo -e "  ${YELLOW}${token}${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo "  请将其填入 .env 的 GITEA_ADMIN_TOKEN="
fi

echo ""
ok "Gitea 初始化完成：$GITEA_URL"
