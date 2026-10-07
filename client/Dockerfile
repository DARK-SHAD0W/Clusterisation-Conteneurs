FROM node:24-alpine3.24

WORKDIR /app

# dependencies first so this layer stays cached until package.json / yarn.lock change
COPY package*.json yarn.lock ./
RUN yarn install --frozen-lockfile


COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY index.html ./
COPY public public
COPY src src

EXPOSE 5173

# --host makes Vite listen on 0.0.0.0 so it is reachable from outside the container
CMD ["yarn", "dev", "--host"]
