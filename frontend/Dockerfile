# syntax=docker/dockerfile:1.7

FROM node:22-alpine AS base

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable

WORKDIR /app

FROM base AS deps

COPY package.json pnpm-lock.yaml ./

RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

FROM deps AS builder

COPY . .

RUN pnpm build

FROM node:22-alpine AS runner

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

WORKDIR /app

COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "const http=require('http'); const req=http.get('http://127.0.0.1:3000/', (res) => process.exit(res.statusCode < 500 ? 0 : 1)); req.on('error', () => process.exit(1)); req.setTimeout(5000, () => { req.destroy(); process.exit(1); });"

CMD ["node", "server.js"]
