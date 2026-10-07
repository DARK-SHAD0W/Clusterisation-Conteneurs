FROM node:22

WORKDIR /app

# dependencies first so this layer stays cached until package.json / yarn.lock change
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY index.html vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY public public
COPY src src

EXPOSE 5173

# --host makes Vite listen on 0.0.0.0 so it is reachable from outside the container
CMD ["yarn", "dev", "--host"]
