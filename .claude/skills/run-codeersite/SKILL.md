---
name: run-codeersite
description: Build, launch, and drive the Codeersite full-stack app (Flask + Next.js + PostgreSQL + MongoDB + Gitea) on macOS. Use for run, start, screenshot, and smoke-test requests.
---

# Run Codeersite

Codeersite is a full-stack developer community app: Flask 3 REST API (`src/api/`), Next.js 16 frontend (`src/web/`), PostgreSQL 16, MongoDB 7, and Gitea for VCS. Paths below are relative to the repo root.

The primary agent path is the driver in this skill directory. It starts Docker services, runs Alembic migrations, launches the backend and frontend, and can take a screenshot with Chrome headless.

## Prerequisites

This skill is verified on macOS with:

- Docker Desktop (or Docker daemon on `unix:///var/run/docker.sock`)
- `uv` (Python package/runtime manager)
- `pnpm` (Node package manager)
- `curl`
- `lsof`
- Google Chrome or Google Chrome Beta (for screenshots)

All of the above except Chrome are also used by the project’s own `scripts/dev.sh`.

## Build / setup

Install backend dependencies and frontend dependencies:

```bash
uv sync
cd src/web && pnpm install
```

Create `.env` from `.env.example` if it does not exist:

```bash
cp .env.example .env
```

A valid `.env` is required because Alembic and Flask read `DATABASE_URL`, `MONGO_URI`, `JWT_SECRET_KEY`, etc. from it.

## Run (agent path)

Use the driver. All commands are run from the repo root.

Start everything and keep running until Ctrl-C:

```bash
./.claude/skills/run-codeersite/driver.sh
```

Run smoke checks and exit:

```bash
./.claude/skills/run-codeersite/driver.sh --smoke
```

Start, take a screenshot, and exit:

```bash
./.claude/skills/run-codeersite/driver.sh --screenshot /tmp/codeersite.png
```

If ports 5100 (Flask) or 3000 (Next.js) are already in use, the driver stops and tells you the PID. To let the driver kill those processes and continue, add `--force`:

```bash
./.claude/skills/run-codeersite/driver.sh --smoke --force
./.claude/skills/run-codeersite/driver.sh --screenshot /tmp/codeersite.png --force
```

Override ports via environment variables:

```bash
FLASK_PORT=5200 NEXT_PORT=3100 ./.claude/skills/run-codeersite/driver.sh --smoke
```

When the driver runs interactively, it prints URLs on success:

- API: http://localhost:5100/api
- Web: http://localhost:3000
- Gitea: http://localhost:23000

## Run (human path)

The project also provides `scripts/dev.sh`, which does the same thing but with colorized human-readable output:

```bash
bash scripts/dev.sh
```

Use this for day-to-day development. For agent automation (screenshots, CI smoke tests, headless runs), use the driver above.

## Test

Backend tests run with:

```bash
uv run pytest
```

Frontend static check:

```bash
cd src/web && pnpm build
```

## Driver details

The driver (`driver.sh`) performs these steps in order:

1. `docker compose -f docker/docker-compose.dev.yml up -d` — PostgreSQL, MongoDB, Gitea.
2. `uv run alembic upgrade head` — apply DB migrations.
3. Start Flask dev server on `FLASK_PORT` (default 5100).
4. Start Next.js dev server on `NEXT_PORT` (default 3000).
5. Poll `/api/docs` and `/` until both return 2xx.
6. For `--screenshot`, use Chrome headless to capture `http://127.0.0.1:3000`.
7. On exit (Ctrl-C, normal exit, or error), kill the started backend/frontend processes.

The driver assumes Chrome is at `/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta`. Set `CHROME` to override.

## Gotchas

- **macOS AirPlay receiver occupies port 5000.** The project uses 5100 for Flask and `next.config.ts` rewrites `/api/*` to `127.0.0.1:5100`. Do not change one without the other.
- **`.env` must exist before the driver runs.** Unlike the old `scripts/dev.sh`, this driver does not auto-create it.
- **Port 3000 conflicts with another Next.js dev server.** Next.js dev server detects a second instance and refuses to start; the driver treats this as a port conflict and exits unless `--force` is given.
- **Gitea first-time setup.** If the `gitea` database does not exist, run `bash scripts/init-gitea.sh` once after `docker compose up`.
- **Headless screenshot uses 127.0.0.1.** `next.config.ts` sets `allowedDevOrigins: ["127.0.0.1"]` so Chrome headless can load HMR resources without cross-origin blocking.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `port 5100 is already in use` | Kill the process (`kill <pid>`), use `--force`, or set `FLASK_PORT`. |
| `port 3000 is already in use` | Same as above, or set `NEXT_PORT`. |
| `docker compose` fails | Ensure Docker Desktop is running: `docker info`. |
| Alembic cannot connect to PostgreSQL | Check `.env` `DATABASE_URL` and that `codeersite-pg` is healthy: `docker ps`. |
| Screenshot is blank/white | Increase the sleep before screenshot in the driver, or verify Chrome path. |
| Chrome not found | Install Google Chrome / Chrome Beta, or set `CHROME` to the full binary path. |
