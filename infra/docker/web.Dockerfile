# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS base

WORKDIR /app

COPY apps/web/package.json apps/web/pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile || npm install

COPY apps/web ./

RUN pnpm build || npm run build

EXPOSE 3000

CMD ["pnpm", "start"]