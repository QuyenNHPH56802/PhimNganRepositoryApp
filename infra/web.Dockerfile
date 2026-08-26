FROM node:20-alpine

ENV PNPM_HOME=/usr/local/share/pnpm \
    PATH=/usr/local/share/pnpm:$PATH
RUN corepack enable

WORKDIR /app
COPY package.json pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/web ./apps/web
COPY packages/shared ./packages/shared

RUN pnpm install --frozen-lockfile || pnpm install

WORKDIR /app/apps/web
RUN pnpm build || true

EXPOSE 3000
CMD ["pnpm", "dev"]