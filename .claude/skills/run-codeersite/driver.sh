#!/usr/bin/env bash
set -euo pipefail

# Codeersite run driver
# Usage:
#   ./.claude/skills/run-codeersite/driver.sh           # start backend + frontend, wait for Ctrl-C
#   ./.claude/skills/run-codeersite/driver.sh --smoke   # start, run smoke checks, exit
#   ./.claude/skills/run-codeersite/driver.sh --screenshot /path/to/ss.png
#   ./.claude/skills/run-codeersite/driver.sh --force   # kill existing processes on expected ports

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
FLASK_PORT="${FLASK_PORT:-5100}"
NEXT_PORT="${NEXT_PORT:-3000}"
GITEA_PORT="${GITEA_PORT:-23000}"
CHROME="/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta"

MODE="run"
FORCE=0
SCREENSHOT_PATH=""

while [ $# -gt 0 ]; do
    case "$1" in
        --smoke)
            MODE="smoke"
            shift
            ;;
        --screenshot)
            MODE="screenshot"
            SCREENSHOT_PATH="${2:-$ROOT/screenshot.png}"
            shift 2
            ;;
        --force)
            FORCE=1
            shift
            ;;
        *)
            err "unknown option: $1"
            exit 1
            ;;
    esac
done

log() { echo -e "\033[0;34m[driver]\033[0m $*"; }
ok() { echo -e "\033[0;32m[driver]\033[0m $*"; }
warn() { echo -e "\033[1;33m[driver]\033[0m $*" >&2; }
err() { echo -e "\033[0;31m[driver]\033[0m $*" >&2; }

cleanup_pids=()
register_pid() { cleanup_pids+=("$1"); }
cleanup() {
    log "shutting down..."
    for pid in "${cleanup_pids[@]:-}"; do
        [ -n "$pid" ] || continue
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    done
    log "stopped"
}
trap cleanup EXIT INT TERM

check_prereq() {
    local missing=()
    for cmd in docker uv pnpm curl lsof; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done
    if [ ${#missing[@]} -ne 0 ]; then
        err "missing dependencies: ${missing[*]}"
        exit 1
    fi

    if [ "$MODE" = "screenshot" ] && [ ! -x "$CHROME" ]; then
        err "Chrome not found at $CHROME; install Google Chrome or set CHROME path"
        exit 1
    fi
}

ensure_port_free() {
    local port="$1"
    local pids
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
        if [ "$FORCE" -eq 1 ]; then
            warn "port $port is already in use; --force set, killing: $pids"
            echo "$pids" | xargs kill -9 2>/dev/null || true
            sleep 1
        else
            err "port $port is already in use by PID: $pids"
            err "run 'kill $pids' first, pass --force to let the driver kill it,"
            err "or set FLASK_PORT/NEXT_PORT to different ports"
            exit 1
        fi
    fi
}

wait_for_url() {
    local url="$1"
    local label="$2"
    local tries=30
    log "waiting for $label at $url..."
    for i in $(seq 1 $tries); do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -qE '^2'; then
            ok "$label is ready"
            return 0
        fi
        sleep 1
    done
    err "$label did not become ready"
    return 1
}

start_services() {
    cd "$ROOT"
    log "starting docker services..."
    docker compose -f "$ROOT/docker/docker-compose.dev.yml" up -d
}

run_migrations() {
    cd "$ROOT"
    log "running alembic migrations..."
    uv run alembic upgrade head
}

start_backend() {
    ensure_port_free "$FLASK_PORT"
    cd "$ROOT"
    log "starting Flask backend on port $FLASK_PORT..."
    uv run flask --app src/api/wsgi:app run --debug --port "$FLASK_PORT" &
    register_pid $!
}

start_frontend() {
    ensure_port_free "$NEXT_PORT"
    cd "$ROOT/src/web"
    log "starting Next.js frontend on port $NEXT_PORT..."
    pnpm dev &
    register_pid $!
}

smoke() {
    wait_for_url "http://127.0.0.1:$FLASK_PORT/api/docs" "backend"
    wait_for_url "http://127.0.0.1:$NEXT_PORT" "frontend"
    ok "smoke checks passed"
}

take_screenshot() {
    local path="$1"
    log "taking screenshot -> $path"
    "$CHROME" --headless --disable-gpu \
        --window-size=1280,720 \
        --screenshot="$path" \
        --hide-scrollbars \
        "http://127.0.0.1:$NEXT_PORT" 2>/dev/null
    ok "screenshot saved to $path"
}

main() {
    check_prereq
    start_services
    run_migrations
    start_backend
    start_frontend

    sleep 3
    smoke

    if [ "$MODE" = "smoke" ]; then
        ok "smoke mode complete"
        exit 0
    fi

    if [ "$MODE" = "screenshot" ]; then
        sleep 3
        take_screenshot "$SCREENSHOT_PATH"
        ok "screenshot mode complete"
        exit 0
    fi

    ok "Codeersite is running"
    echo "  API    : http://localhost:$FLASK_PORT/api"
    echo "  Web    : http://localhost:$NEXT_PORT"
    echo "  Gitea  : http://localhost:$GITEA_PORT"
    echo "  press Ctrl-C to stop"
    wait
}

main "$@"
