#!/bin/bash
# postgres 官方镜像启动时执行的初始化脚本（仅 pgdata 首次创建时运行一次）。
# 创建 Gitea 使用的独立 database，复用 codeersite 账号（superuser）。
#
# 注意：PostgreSQL 的 CREATE DATABASE 不支持 IF NOT EXISTS 语法，
#       故用 SELECT ... WHERE NOT EXISTS(...) \gexec 实现幂等创建。
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE gitea OWNER codeersite'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'gitea')\gexec
EOSQL
