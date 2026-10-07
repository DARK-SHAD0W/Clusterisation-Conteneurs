# ---- stage 1: install all dependencies ----
FROM node:24-alpine3.24 AS deps

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# ---- stage 2: build the React app into static files (dist) ----
FROM node:24-alpine3.24 AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY tsconfig*.json vite.config.ts index.html ./
COPY public ./public
COPY src ./src

RUN yarn build

# ---- stage 3: production image, nginx serves the static files ----
FROM nginx:1.29-alpine AS main

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 5173
