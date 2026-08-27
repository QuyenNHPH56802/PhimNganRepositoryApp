# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS base

WORKDIR /app

# Install web app deps in isolation (no monorepo hoisting needed for Next)
WORKDIR /web
COPY apps/web/package.json ./
RUN npm install --no-audit --no-fund

# Copy the rest of the web app + tsconfig.base.json it extends from
COPY apps/web ./
COPY tsconfig.base.json ../../tsconfig.base.json

RUN npm run build

# Runtime image
FROM node:20-alpine AS runtime
WORKDIR /app
COPY --from=base /web ./

EXPOSE 3000

CMD ["npm", "start"]