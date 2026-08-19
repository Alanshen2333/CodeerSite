FROM --platform=$BUILDPLATFORM node:24-alpine AS deps
WORKDIR /app
RUN corepack enable
COPY src/web/package.json src/web/pnpm-lock.yaml src/web/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM --platform=$BUILDPLATFORM node:24-alpine AS builder
WORKDIR /app
RUN corepack enable
COPY --from=deps /app/node_modules ./node_modules
COPY src/web ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build
# 图片优化已关闭；删除构建机架构的原生 sharp，保证产物可跨架构运行。
RUN rm -rf .next/standalone/node_modules/.pnpm/sharp@* \
    .next/standalone/node_modules/.pnpm/@img+sharp-* \
    .next/standalone/node_modules/.pnpm/@img+sharp-libvips-*

FROM --platform=$TARGETPLATFORM node:24-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
