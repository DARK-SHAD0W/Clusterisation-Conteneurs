FROM node:22

WORKDIR /app

# dependencies first so this layer stays cached until package.json / yarn.lock change
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY tsconfig.json ./
COPY src src
RUN yarn build

EXPOSE 3000

CMD ["yarn", "start"]
