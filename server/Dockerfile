# ---- stage 1: build the TypeScript code ----
FROM node:24-alpine3.24 AS deps

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

FROM node:24-alpine3.24 AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY src ./src
COPY tsconfig.json ./

RUN yarn build

FROM node:24-alpine3.24 AS main
WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --production && yarn cache clean

EXPOSE 3000

CMD ["yarn", "start"]
