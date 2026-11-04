# My Favorite Places : Clusterisation de conteneurs

Projet du module **Clusterisation de conteneurs** (ESGI Lyon, 5ESGI AL + IABD).
<br/>Le but : prendre l'application **My Favorite Places** (un client React et une API Node.js/Express qui enregistre ses données dans PostgreSQL), la mettre dans des conteneurs, l'orchestrer, puis la faire tenir la charge.

Ce document raconte la démarche, étape par étape (retour au [sommaire général](../README.md)).
<br/>À chaque nouvelle étape du module, une section vient s'ajouter à la suite.

## Sommaire

**TD1**

1. [Test initial avec Bruno](#1-test-initial-avec-bruno)
2. [Dockerisation du serveur](#2-dockerisation-du-serveur)
3. [Dockerisation du client](#3-dockerisation-du-client)
4. [Orchestration avec Docker Compose](#4-orchestration-avec-docker-compose)
5. [Communication entre les services](#5-communication-entre-les-services)
6. [Démarrage, redémarrage et images légères](#6-démarrage-redémarrage-et-images-légères)

**TD2**

- [Prérequis : images publiées sur un registry](#prérequis--images-publiées-sur-un-registry)
- [Exercice 2 : création du cluster Docker Swarm](#exercice-2--création-du-cluster-docker-swarm)
- [Exercice 3 : tests du cluster](#exercice-3--tests-du-cluster)

**TD3**

- [Exercice 1 : déployer Traefik](#exercice-1--déployer-traefik)
- [Exercice 2 : déployer une autre application](../voting-app/TD3.md#exercice-2--déployer-une-autre-application) (dans le dossier `voting-app/`)
- [Exercice 3 : déployer Portainer](#exercice-3--déployer-portainer)
- [Exercice 4 : déployer l'API de MFP depuis Portainer](#exercice-4--déployer-lapi-de-mfp-depuis-portainer)

## Structure du dossier

```
mfp/
├── client/                          # application React (Vite)
├── server/                          # API Node.js / Express / TypeORM
├── compose.yml                      # lance la base, le serveur et le client ensemble
├── mfp-bruno-api-test-collection/   # collection Bruno pour tester l'API
├── swarm/                           # cluster Docker Swarm (DinD) et stacks (TD2 à TD4)
└── screenshots/                     # captures d'écran
```

Les workflows GitHub Actions qui publient les images restent à la racine du dépôt, dans [`.github/workflows/`](../.github/workflows/) : GitHub ne les lit qu'à cet endroit.

## Environnement de travail

| Outil | Version | Remarque |
|---|---|---|
| Docker Engine | 29.7.2 | installé dans WSL2 (Ubuntu 24.04), sans Docker Desktop |
| Docker Compose | v5.5.0 | plugin `docker compose` |
| Node.js / Yarn | 22.23.2 / 1.22.22 | installés dans WSL via nvm |
| Bruno | 4.2.1 | client API installé sous Windows |

Toutes les commandes se lancent dans un terminal **WSL (Ubuntu)**, depuis ce dossier `mfp/`.

---

# TD1

## 1. Test initial avec Bruno

**Objectif (TD1, étape 1) :** avant de toucher à Docker, on vérifie que l'API fonctionne en la lançant en local avec `yarn dev`.

### 1.1 Prérequis : lancer d'abord une base PostgreSQL

Première chose à savoir : le serveur refuse de démarrer **tant qu'il ne trouve pas PostgreSQL**.
<br/>Sans base, il affiche `🚨 unable to connect to db` et ne se met jamais à écouter sur le port 3000.

Il va chercher la base avec les paramètres écrits dans `server/src/datasource.ts` :

| Paramètre | Valeur |
|---|---|
| host | `localhost` |
| port | `5432` (port par défaut) |
| username | `postgres` |
| password | `supersecret` |
| database | `postgres` |

Bonne nouvelle : il crée lui-même les tables `user` et `address` au démarrage (`synchronize: true`).
<br/>Une base vide lui suffit donc.

On démarre alors une base PostgreSQL dans un conteneur, avec les identifiants qu'il attend :

```bash
docker run -d --name mfp-db \
  -e POSTGRES_PASSWORD=supersecret \
  -p 5432:5432 \
  postgres:17
```

- `-e POSTGRES_PASSWORD=supersecret` : le mot de passe que le serveur va utiliser.
- `-p 5432:5432` : rend la base joignable sur `localhost`, puisque le serveur tourne pour l'instant en dehors de Docker.

Un petit `docker ps` confirme que `mfp-db` tourne bien (`Up`, port `5432`) :

<p align="center">
  <img src="screenshots/td1-00-postgres-db.png" alt="Lancement de la base PostgreSQL">
</p>

### 1.2 Lancer l'API en mode développement

```bash
cd server
yarn install
yarn dev
```

`yarn dev` lance `nodemon src/index.ts`.
<br/>On sait que tout va bien quand la console affiche :

```
✅ connected to PgSQL db
🚀 server started on port 3000
```

<p align="center">
  <img src="screenshots/td1-00-yarn-dev.png" alt="Démarrage du serveur avec yarn dev">
</p>

### 1.3 Routes de l'API

L'API répond sur `http://localhost:3000`, et toutes ses routes commencent par `/api` :

| Méthode | Route | Authentification | Rôle |
|---|---|---|---|
| POST | `/api/users` | non | créer un utilisateur (`email`, `password`) |
| POST | `/api/users/tokens` | non | se connecter et obtenir un token |
| GET | `/api/users/me` | oui | profil de l'utilisateur connecté |
| POST | `/api/addresses` | oui | ajouter une adresse |
| GET | `/api/addresses` | oui | lister ses adresses |
| POST | `/api/addresses/searches` | oui | rechercher ses adresses autour d'un point (rayon en km) |

Pour les routes protégées, il faut joindre son token dans le header `Authorization: Bearer <token>`.

### 1.4 Collection Bruno

Les requêtes de test sont rangées dans `mfp-bruno-api-test-collection/` : il suffit d'ouvrir ce dossier dans Bruno. On les lance dans l'ordre :

| # | Requête | Résultat attendu |
|---|---|---|
| 01 | Create user | `200`, l'utilisateur créé |
| 02 | Login (get token) | `200`, `{ "token": "..." }` |
| 03 | My profile | `200`, l'utilisateur connecté |

Notre utilisateur de test : **ahmed test 1**, email `ahmedtest@gmail.com`, mot de passe `azerty123`.

### 1.5 Résultats des tests

#### 01 — Créer un utilisateur

`POST http://localhost:3000/api/users`

```json
{
  "email": "ahmedtest@gmail.com",
  "password": "azerty123"
}
```

<p align="center">
  <img src="screenshots/td1-01-create-user.png" alt="01 - Create user">
</p>

#### 02 — Se connecter (obtenir un token)

`POST http://localhost:3000/api/users/tokens` (même corps que la requête 01)

<p align="center">
  <img src="screenshots/td1-02-login.png" alt="02 - Login">
</p>

#### 03 — Mon profil

`GET http://localhost:3000/api/users/me` (header `Authorization: Bearer {{token}}`)

<p align="center">
  <img src="screenshots/td1-03-my-profile.png" alt="03 - My profile">
</p>

---

## 2. Dockerisation du serveur

**Objectif (TD1, étape 2) :** faire tourner l'API dans un conteneur, à côté de la base, puis refaire les tests avec Bruno.

### 2.1 Le Dockerfile du serveur

Fichier `server/Dockerfile` :

```dockerfile
FROM node:24-alpine3.24

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY tsconfig.json ./
COPY src src
RUN yarn build

EXPOSE 3000

CMD ["yarn", "start"]
```

- On installe les dépendances en premier. Tant que `package.json` et `yarn.lock` ne bougent pas, Docker garde cette étape en cache, et les reconstructions suivantes vont beaucoup plus vite.
- On ne copie que ce qui sert vraiment (`src` et `tsconfig.json`), pas tout le dossier.
- `yarn build` traduit le TypeScript en JavaScript pendant la construction de l'image. Au démarrage, `yarn start` n'a plus qu'à lancer ce JavaScript.

Au passage, `server/.dockerignore` évite d'envoyer `node_modules` et `dist` à Docker.

> Les captures de cette étape ont été prises avec l'image `node:22`, qu'on a ensuite remplacée par `node:24-alpine3.24` (plus récente et plus légère).
> <br/>Plus tard, ce Dockerfile a été découpé en 3 étapes pour alléger l'image : voir [6.3](#63-alléger-les-images).

### 2.2 Adapter la connexion à la base

Premier piège : dans un conteneur, `localhost` veut dire **le conteneur lui-même**. Le serveur cherchait donc la base chez lui… et forcément, il ne la trouvait pas.

Pour s'en sortir, `server/src/datasource.ts` lit maintenant ses paramètres dans des **variables d'environnement**, en gardant les anciennes valeurs par défaut :

```ts
host: process.env.DB_HOST || "localhost",
username: process.env.DB_USER || "postgres",
password: process.env.DB_PASSWORD || "supersecret",
database: process.env.DB_NAME || "postgres",
```

Dans Docker, il suffit alors de donner au serveur le nom du conteneur de la base avec `DB_HOST`.

> Ces variables ont disparu par la suite, avec Docker Compose : voir [4.4](#44-simplification-de-la-connexion-à-la-base).

### 2.3 Lancer la base et le serveur

Pour que deux conteneurs puissent s'appeler par leur nom, ils doivent partager le même **réseau Docker**. On en crée donc un :

```bash
# 1. créer un réseau commun
docker network create mfp-net

# 2. lancer la base sur ce réseau
docker run -d --name mfp-db --network mfp-net \
  -e POSTGRES_PASSWORD=supersecret \
  postgres:17

# 3. construire l'image du serveur
docker build -t mfp-server ./server

# 4. lancer le serveur sur le même réseau
docker run -d --name mfp-server --network mfp-net \
  -e DB_HOST=mfp-db \
  -p 3000:3000 \
  mfp-server

# 5. vérifier
docker ps
docker logs mfp-server
```

- `--network mfp-net` : sur ce réseau, le serveur trouve la base sous le nom `mfp-db`.
- `-e DB_HOST=mfp-db` : c'est ce nom qu'on lui donne pour la base.
- `-p 3000:3000` : l'API reste accessible sur `http://localhost:3000`, pour Bruno.
- La base n'a plus besoin de `-p 5432:5432` : seul le serveur lui parle, et il passe par le réseau Docker.

<p align="center">
  <img src="screenshots/td1-04-server-docker-build.png" alt="Création du réseau, de la base et de l'image du serveur">
</p>

> **Problème rencontré :** au premier essai, `docker run` a refusé de démarrer avec `address already in use` sur le port 3000.
> <br/>On avait tout simplement oublié le `yarn dev` de l'étape 1, qui tournait encore sur ce port.
> <br/>**Solution :** arrêter `yarn dev` (Ctrl+C), supprimer le conteneur raté (`docker rm -f mfp-server`), puis relancer la commande 4.

Cette fois, les logs du serveur affichent bien :

```
✅ connected to PgSQL db
🚀 server started on port 3000
```

On le voit même créer les tables `user` et `address` dans la base toute neuve.

<p align="center">
  <img src="screenshots/td1-05-server-docker-logs.png" alt="Base et serveur lancés dans Docker">
</p>

### 2.4 Test avec Bruno

Rien à changer côté Bruno : grâce à `-p 3000:3000`, le conteneur répond à la même adresse que `yarn dev`.

Comme la base est neuve, on recrée l'utilisateur avec **01 - Create user**, puis on se connecte avec **02 - Login (get token)**. On récupère un `200` et un token : le serveur, depuis son conteneur, retrouve bien l'utilisateur dans `mfp-db`.

<p align="center">
  <img src="screenshots/td1-06-login-docker.png" alt="02 - Login avec le serveur dans Docker">
</p>

---

## 3. Dockerisation du client

**Objectif (TD1, étape 4) :** mettre aussi le client React dans un conteneur, et vérifier qu'il arrive à parler au serveur.

### 3.1 Le Dockerfile du client

Fichier `client/Dockerfile` :

```dockerfile
FROM node:24-alpine3.24

WORKDIR /app

COPY package*.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY index.html ./
COPY public public
COPY src src

EXPOSE 5173

CMD ["yarn", "dev", "--host"]
```

- On reprend la même recette que pour le serveur : les dépendances d'abord, puis uniquement les fichiers utiles.
- Le client tourne avec le serveur de développement de Vite, sur le port `5173`.
- `--host` : sans cette option, Vite n'accepte que les visites venant de l'intérieur du conteneur, et notre navigateur resterait à la porte.

`client/.dockerignore` écarte lui aussi `node_modules` et `dist`.

> Les captures de cette étape ont été prises avec `node:22`, remplacée ensuite par `node:24-alpine3.24`.
> <br/>Plus tard, ce Dockerfile a été remplacé par une version en 3 étapes, où c'est **nginx** qui sert le client : voir [6.3](#63-alléger-les-images).

### 3.2 Adapter l'adresse de l'API

Le client appelle l'API sur `/api/...`, et Vite fait suivre ces appels au serveur (`client/vite.config.ts`). Problème : l'adresse visée était `http://localhost:3000`, et dans le conteneur du client, `localhost`… c'est le client lui-même. Même piège que pour le serveur.

On lit donc cette adresse dans une variable d'environnement :

```ts
target: process.env.API_URL || "http://localhost:3000",
```

> Cette variable a disparu par la suite : dans Docker, c'est maintenant nginx qui fait suivre les appels `/api` au serveur (voir [6.3](#63-alléger-les-images)). `vite.config.ts` pointe désormais vers `http://server:3000`, le nom du service du serveur, exactement comme `db` pour la base.

### 3.3 Lancer le client

La base et le serveur de l'étape 2 doivent toujours tourner.

```bash
# 1. construire l'image du client
docker build -t mfp-client ./client

# 2. lancer le client sur le même réseau que le serveur
docker run -d --name mfp-client --network mfp-net \
  -e API_URL=http://mfp-server:3000 \
  -p 5173:5173 \
  mfp-client

# 3. vérifier
docker ps
docker logs mfp-client
```

- `-e API_URL=http://mfp-server:3000` : Vite sait maintenant où envoyer les appels `/api`.
- `-p 5173:5173` : le site est accessible sur `http://localhost:5173`.

`docker ps` affiche nos 3 conteneurs (`mfp-db`, `mfp-server`, `mfp-client`), tous `Up`.

<p align="center">
  <img src="screenshots/td1-07-client-docker.png" alt="Construction et lancement du client">
</p>

### 3.4 Test dans le navigateur

On ouvre `http://localhost:5173`, on se connecte avec `ahmedtest@gmail.com` / `azerty123`… et on arrive bien sur le tableau de bord.

<p align="center">
  <img src="screenshots/td1-08-client-browser.png" alt="Client dans le navigateur">
</p>

---

## 4. Orchestration avec Docker Compose

**Objectif (TD1, étape 3) :** en finir avec la longue liste de `docker network` et `docker run`, et tout lancer en une seule commande grâce à un fichier.

### 4.1 Le fichier `compose.yml`

Le fichier `compose.yml`, à la racine du dossier `mfp/`, décrit nos 3 services. Chacun remplace une commande `docker run` qu'on tapait à la main :

| Service | Remplace | Points clés |
|---|---|---|
| `db` | `docker run ... postgres:17` | même utilisateur (`POSTGRES_USER`) et mot de passe que ceux attendus par le serveur ; port `5432` publié |
| `server` | `docker build` + `docker run ... mfp-server` | trouve la base grâce au **nom du service** `db` (voir [4.4](#44-simplification-de-la-connexion-à-la-base)) |
| `client` | `docker build` + `docker run ... mfp-client` | port `5173` publié ; fait suivre les appels `/api` au service `server` (voir [5](#5-communication-entre-les-services)) |

- **Réseau :** plus besoin de le créer, Compose s'en charge. Chaque service y est joignable par son nom (`db`, `server`, `client`).
- **Volume `db-data` :** les données de la base survivent, même si on recrée le conteneur `db`.
- **`depends_on` :** les services démarrent dans l'ordre `db` → `server` → `client`.
- **`healthcheck` sur `db` :** toutes les 2 secondes, `pg_isready` vérifie si PostgreSQL accepte les connexions. Grâce à `condition: service_healthy`, le serveur attend patiemment que la base soit **prête** avant de démarrer.

### 4.2 Lancer l'application

On fait d'abord le ménage : les conteneurs et le réseau créés à la main occupent encore les ports 3000 et 5173.

```bash
docker rm -f mfp-client mfp-server mfp-db
docker network rm mfp-net
```

Puis on lance tout d'un coup :

```bash
docker compose up -d --build
docker compose ps
docker compose logs server
```

- `up` : crée le réseau, le volume et les 3 conteneurs, puis les démarre.
- `-d` : en arrière-plan, pour garder la main sur le terminal.
- `--build` : construit les images du serveur et du client au passage.

> **Problème rencontré :** au départ, avec un simple `depends_on: - db`, le serveur s'arrêtait aussitôt (`unable to connect to db: connect ECONNREFUSED`).
> <br/>En fait, `depends_on` attend seulement que le conteneur de la base soit **démarré**, pas que PostgreSQL soit **prêt** à répondre : le serveur arrivait trop tôt.
> <br/>**Solution :** le `healthcheck` sur `db` et `condition: service_healthy` sur `server` (voir 4.1). On voit alors `mfp-db-1 Waiting` puis `Healthy` avant que le serveur ne démarre.

`docker compose ps` montre les 3 services `Up` (`healthy` pour `db`), et les logs du serveur affichent `connected to PgSQL db` puis `server started on port 3000`.

<p align="center">
  <img src="screenshots/td1-09-compose-up.png" alt="Lancement avec docker compose">
</p>

### 4.3 Test

Nouveau volume, donc base vide : on recrée l'utilisateur avec Bruno (**01 - Create user**), puis on se connecte sur `http://localhost:5173` avec `ahmedtest@gmail.com` / `azerty123`.

<p align="center">
  <img src="screenshots/td1-10-compose-browser.png" alt="Client lancé avec Compose">
</p>

Pour tout arrêter : `docker compose down`. Le volume `db-data`, et donc les données, restent en place.

### 4.4 Simplification de la connexion à la base

Avec Compose, la base porte toujours le même nom : `db`, celui de son service. Les variables d'environnement de l'étape 2 n'ont donc plus d'intérêt, et on écrit l'adresse directement dans `server/src/datasource.ts` :

```ts
host: "db",
username: "postgres",
password: "supersecret",
database: "postgres",
```

Le revers de la médaille : le serveur ne fonctionne plus que **dans Compose**, là où le nom `db` existe. Les commandes manuelles de l'étape 2 et le `yarn dev` de l'étape 1 ne trouvent plus la base sans retouche.

---

## 5. Communication entre les services

**Question (TD1, étape 5) :** comment la base et le serveur se parlent-ils ? Et le serveur et le front ?

```
 Machine (Windows / WSL)                 Réseau Docker « mfp_default »
 ┌──────────────────────┐              ┌───────────────────────────────────────────────┐
 │ Navigateur ──────────┼─ :5173 ─────►│ client (nginx) ── /api ──► server ──► db       │
 │                      │              │                           :3000      :5432    │
 │ Bruno ───────────────┼─ :3000 ─────►│                           server              │
 └──────────────────────┘              └───────────────────────────────────────────────┘
```

**Base ↔ serveur**
- Les deux conteneurs vivent sur le même réseau, créé par Compose.
- Le serveur appelle la base par son **nom de service**, `db`, sur le port `5432`. Docker se charge de traduire ce nom en adresse.
- Le port `5432` n'est publié que pour pouvoir jeter un œil à la base depuis la machine : le serveur, lui, n'en a pas besoin.

**Front ↔ serveur**
- Le code React tourne **dans le navigateur**, c'est-à-dire sur notre machine, en dehors du réseau Docker : il n'a aucune idée de ce qu'est `server`.
- Le navigateur appelle donc l'API à la même adresse que le site : `http://localhost:5173/api/...`.
- C'est le conteneur `client` qui fait le relais vers le service `server`, par le réseau Docker (d'abord avec Vite, puis avec nginx).
- Bruno, de son côté, va directement voir le serveur sur `http://localhost:3000`, grâce au port `3000` publié.

---

## 6. Démarrage, redémarrage et images légères

**Objectif (TD2) :** rendre le démarrage fiable, faire redémarrer les services tout seuls, et alléger les images.

### 6.1 Démarrer le serveur seulement quand la base est prête

C'est déjà réglé depuis l'étape 4 : `healthcheck` sur `db` et `condition: service_healthy` sur `server` (voir [4.1](#41-le-fichier-composeyml) et [4.2](#42-lancer-lapplication)).

### 6.2 Redémarrage automatique

Dans `compose.yml`, chaque service a maintenant :

```yaml
restart: unless-stopped
```

- Si un service plante et s'arrête tout seul, Docker le **relance automatiquement**.
- Si c'est nous qui l'arrêtons **à la main** (`docker compose stop`), il reste arrêté.

Pour le vérifier, on simule un plantage en tuant le processus Node du serveur, puis on compte combien de fois Docker l'a relancé :

```bash
docker compose exec server pkill -f "node dist/index.js"
docker inspect mfp-server-1 --format 'status={{.State.Status}} restarts={{.RestartCount}}'
# status=running restarts=1

docker compose stop server
docker inspect mfp-server-1 --format 'status={{.State.Status}} restarts={{.RestartCount}}'
# status=exited restarts=1   (arrêt manuel : pas de redémarrage)

docker compose start server
```

### 6.3 Alléger les images

On découpe chaque Dockerfile en **3 étapes** (*multi-stage build*). Seule la dernière devient l'image finale : les outils de construction et le code source restent derrière, dans les étapes précédentes.

| Étape | Rôle |
|---|---|
| `deps` | installe toutes les dépendances |
| `builder` | construit l'application (`yarn build`) |
| `main` | image finale : seulement ce qui sert à lancer l'application |

**Serveur** (`server/Dockerfile`) : l'image finale ne garde que le JavaScript compilé (`dist`) et les dépendances de production (`--production`).

**Client** (`client/Dockerfile`) : `yarn build` transforme l'application React en simples fichiers HTML, CSS et JavaScript. Plus besoin de Node.js pour les servir : un petit serveur web **nginx** fait très bien l'affaire.

Sa configuration se trouve dans `client/nginx.conf`, copié dans l'image :

```nginx
server {
    listen 5173;
    root /usr/share/nginx/html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://server:3000;
    }
}
```

- `listen 5173` : on garde le même port, l'adresse du site ne change pas.
- `location /` : envoie les fichiers du site. Pour une page comme `/dashboard`, qui n'existe pas vraiment en tant que fichier, nginx renvoie `index.html` et React affiche la bonne page.
- `location /api/` : fait suivre les appels à l'API vers le service `server`. C'est le rôle que tenait Vite avant.

**Résultat :**

| Image | Avant | Après |
|---|---|---|
| `mfp-server` | 477 Mo | **337 Mo** (−140 Mo) |
| `mfp-client` | 1,49 Go | **93 Mo** |

```bash
docker compose up -d --build
docker images
```

---

# TD2

**Objectif :** monter un cluster Docker Swarm sur notre propre PC. Chaque « machine » du cluster est en fait un conteneur **Docker-in-Docker** (DinD), qui embarque son propre Docker.

## Prérequis : images publiées sur un registry

Swarm ne sait pas construire d'images (`build:` n'est pas pris en charge) : les machines du cluster doivent pouvoir les **télécharger** depuis un registry.

Pour ça, deux workflows GitHub Actions (`.github/workflows/build.server.yml` et `build.client.yml`, à la racine du dépôt) construisent les images du serveur et du client à chaque push sur `main`, puis les publient sur le registry de GitHub (**GHCR**) :

```
ghcr.io/dark-shad0w/clusterisation-conteneurs/server:latest
ghcr.io/dark-shad0w/clusterisation-conteneurs/client:latest
```

Les deux images sont publiques : n'importe qui peut les télécharger, sans se connecter.

<p align="center">
  <img src="screenshots/td2-00-ghcr-packages.png" alt="Images publiées sur GHCR">
</p>

## Exercice 2 : création du cluster Docker Swarm

### 2.1 Lancer les 4 machines

Le fichier `swarm/compose.yml` crée 1 conteneur `manager` et 3 conteneurs `node1`, `node2`, `node3`, tous avec l'image `docker:dind`.

- `privileged: true` : indispensable pour faire tourner Docker dans un conteneur. En contrepartie, le conteneur n'est plus isolé du système.
- `hostname` : donne à chaque machine un nom lisible, qu'on retrouvera dans la liste des nœuds.

```bash
cd swarm
docker compose up -d
docker ps
```

<p align="center">
  <img src="screenshots/td2-01-dind-up.png" alt="Lancement des 4 conteneurs DinD">
</p>

Nos 4 machines `swarm-manager-1`, `swarm-node1-1`, `swarm-node2-1` et `swarm-node3-1` sont `Up`, à côté des conteneurs de l'application du TD1.

Reste à vérifier que Docker fonctionne bien **à l'intérieur** :

```bash
docker compose exec manager docker ps
docker compose exec node1 docker ps
```

<p align="center">
  <img src="screenshots/td2-02-dind-docker-ps.png" alt="docker ps dans le manager et dans node1">
</p>

`docker ps` répond, avec une liste **vide** : chaque conteneur a bien son propre Docker, indépendant de celui du PC.
<br/>Les conteneurs de l'application, pourtant bien présents sur le PC, n'y apparaissent pas.

### 2.2 Initialiser le cluster

```bash
docker compose exec manager docker swarm init
```

<p align="center">
  <img src="screenshots/td2-03-swarm-init.png" alt="Initialisation du cluster Swarm">
</p>

Le conteneur `manager` devient le **manager**, autrement dit le chef du cluster.
<br/>Docker nous donne au passage la commande `docker swarm join` et son **token** (`SWMTKN-1-…`) : c'est le sésame dont les nœuds auront besoin pour rejoindre le cluster.

### 2.3 Faire rejoindre les nœuds

```bash
TOKEN=$(docker compose exec manager docker swarm join-token -q worker)
docker compose exec node1 docker swarm join --token $TOKEN manager:2377
docker compose exec node2 docker swarm join --token $TOKEN manager:2377
docker compose exec node3 docker swarm join --token $TOKEN manager:2377
```

- `join-token -q worker` : range le token dans la variable `TOKEN`, ce qui évite de le recopier à la main.
- `manager:2377` : les nœuds retrouvent le manager par le **nom de son service**, pas par son adresse IP.

<p align="center">
  <img src="screenshots/td2-04-swarm-join.png" alt="Les 3 nœuds rejoignent le cluster">
</p>

Chaque nœud répond `This node joined a swarm as a worker.` : `node1`, `node2` et `node3` font désormais partie du cluster, comme **workers**.

### 2.4 Lister les nœuds du cluster

On entre dans le conteneur `manager`, et on lui demande la liste des nœuds :

```bash
docker compose exec manager ash
docker node ls
exit
```

<p align="center">
  <img src="screenshots/td2-05-node-ls.png" alt="Liste des nœuds du cluster">
</p>

Le cluster compte bien **4 nœuds**, tous `Ready` et `Active` :
- `manager` est le **Leader** : c'est lui qui pilote le cluster (l'étoile `*` signale le nœud sur lequel on a tapé la commande).
- `node1`, `node2` et `node3` sont des **workers** : ce sont eux qui font tourner les conteneurs.

## Exercice 3 : tests du cluster

### 3.1 Créer une stack `hello-world`

Fichier `swarm/hello-world.compose.yml` :

```yaml
services:
  hello:
    image: hello-world
    deploy:
      replicas: 2
```

- Une **stack**, c'est un fichier au format Docker Compose qu'on déploie sur le cluster avec `docker stack deploy`.
- La partie `deploy` n'existe que pour Swarm : `replicas: 2` lui demande de faire tourner **2 copies** du conteneur, réparties sur les nœuds.

### 3.2 Copier la stack dans le manager

D'abord, on ajoute un **volume anonyme** sur `/home/manager` au service `manager` (`swarm/compose.yml`). Comme ça, les fichiers rangés dans ce dossier ne disparaissent pas si le conteneur est recréé :

```yaml
  manager:
    image: docker:dind
    hostname: manager
    privileged: true
    volumes:
      - /home/manager
```

Ensuite, on recrée le manager, on s'assure que le cluster n'a pas bougé, et on y dépose la stack :

```bash
docker compose up -d manager
docker compose exec manager docker node ls
docker compose exec manager mkdir -p /home/manager
docker compose cp hello-world.compose.yml manager:/home/manager/
docker compose exec manager ls /home/manager
```

<p align="center">
  <img src="screenshots/td2-06-stack-copy.png" alt="Copie de la stack dans le manager">
</p>

- Même après sa recréation, le manager voit toujours ses 4 nœuds `Ready` : le cluster a tenu le coup.
- `docker compose cp` copie le fichier du PC vers le conteneur, et `ls` confirme qu'il est bien arrivé dans `/home/manager`.

### Redémarrage du cluster

Après un redémarrage du PC, on retrouve nos 4 conteneurs arrêtés. On les relance :

```bash
docker compose start
docker compose exec manager docker node ls
```

<p align="center">
  <img src="screenshots/td2-07-restart-nodes-unknown.png" alt="Nœuds injoignables après le redémarrage">
</p>

> **Problème rencontré :** `node1`, `node2` et `node3` restent bloqués en `Unknown`, puis passent à `Down`.
> <br/>En redémarrant, les conteneurs ont changé d'**adresse IP** (le manager est passé de `172.19.0.5` à `172.19.0.2`). Or Swarm retient l'adresse IP du manager, pas son nom : les nœuds frappaient donc à la mauvaise porte.
> <br/>**Solution :** quitter l'ancien cluster et en recréer un, avec les mêmes commandes qu'aux questions 2.2 et 2.3.

```bash
docker compose exec node1 docker swarm leave --force
docker compose exec node2 docker swarm leave --force
docker compose exec node3 docker swarm leave --force
docker compose exec manager docker swarm leave --force

docker compose exec manager docker swarm init
TOKEN=$(docker compose exec manager docker swarm join-token -q worker)
docker compose exec node1 docker swarm join --token $TOKEN manager:2377
docker compose exec node2 docker swarm join --token $TOKEN manager:2377
docker compose exec node3 docker swarm join --token $TOKEN manager:2377

docker compose exec manager docker node ls
```

<p align="center">
  <img src="screenshots/td2-08-swarm-rebuild.png" alt="Cluster recréé">
</p>

Tout est rentré dans l'ordre : les 4 nœuds sont de nouveau `Ready`, et `manager` a repris sa place de `Leader`.

### 3.3 Déployer la stack et observer le cluster

Depuis le manager, on déploie la stack sous le nom `hello`, puis on regarde ce que devient le service :

```bash
docker compose exec manager docker stack deploy -c /home/manager/hello-world.compose.yml hello
docker compose exec manager docker service ls
docker compose exec manager docker service ps hello_hello
```

<p align="center">
  <img src="screenshots/td2-09-stack-deploy.png" alt="Déploiement de la stack hello">
</p>

- `stack deploy` crée le réseau `hello_default` et le service `hello_hello` (le nom de la stack, suivi du nom du service).
- `service ls` : la colonne **REPLICAS** se lit « copies en cours / copies demandées ». Ici, `0/2` : on en a demandé 2, mais aucune ne tourne à cet instant précis.
- `service ps` raconte l'histoire des 2 copies : chaque conteneur se termine (`Complete`) au bout de quelques secondes, puis Swarm en relance un autre, à chaque fois sur un nœud différent, `manager` compris.

Pour voir la colonne REPLICAS « au complet », on lance à côté un service qui, lui, reste allumé : 3 copies de **nginx**.

```bash
docker compose exec manager docker service create --name web --replicas 3 nginx:alpine
docker compose exec manager docker service ls
```

<p align="center">
  <img src="screenshots/td2-13-replicas.png" alt="Colonne REPLICAS : hello-world à 0/2, nginx à 3/3">
</p>

La différence saute aux yeux :
- `hello_hello` reste à `0/2` : ses conteneurs s'arrêtent dès qu'ils ont affiché leur message.
- `web` affiche `3/3` : les 3 copies de nginx demandées tournent toutes, et Swarm les garde allumées.

Une fois la démonstration faite, on supprime ce service avec `docker compose exec manager docker service rm web`.

On va ensuite voir ce qui s'est passé sur chaque machine :

```bash
docker compose exec manager docker ps -a
docker compose exec node1 docker ps -a
docker compose exec node2 docker ps -a
docker compose exec node3 docker ps -a
```

On ajoute `-a` pour voir aussi les conteneurs arrêtés : `hello-world` s'éteint presque aussitôt, un simple `docker ps` serait donc vide la plupart du temps.

<p align="center">
  <img src="screenshots/td2-10-docker-ps-nodes.png" alt="docker ps -a sur chaque nœud">
</p>

**Ce qu'on en déduit :**
- Les conteneurs sont **éparpillés sur toutes les machines**, y compris le `manager` : par défaut, le chef du cluster met lui aussi la main à la pâte.
- Chaque machine ne voit **que ses propres conteneurs** : c'est Swarm, depuis le manager, qui décide où va chaque copie.
- `hello-world` s'arrête de lui-même (`Exited (0)`, donc sans erreur). Mais `replicas: 2` réclame 2 copies **en permanence** : Swarm les relance donc sans arrêt. D'où le `0/2`, et tous ces conteneurs terminés qui s'empilent.

### 3.4 Faire varier la clause `deploy`

Pour chaque essai, on suit la même routine : on supprime la stack (`docker stack rm hello`), on copie le nouveau fichier dans le manager, et on redéploie.

#### Sur le manager uniquement (par rôle)

Fichier `swarm/hello-world-manager.compose.yml` :

```yaml
services:
  hello:
    image: hello-world
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == manager
```

```bash
docker compose exec manager docker stack rm hello
docker compose cp hello-world-manager.compose.yml manager:/home/manager/
docker compose exec manager docker stack deploy -c /home/manager/hello-world-manager.compose.yml hello
docker compose exec manager docker service ps hello_hello
```

<p align="center">
  <img src="screenshots/td2-11-stack-manager.png" alt="Stack sur le manager uniquement">
</p>

- `node.role == manager` : on interdit à Swarm de placer les conteneurs ailleurs que sur un nœud **manager**.
- `service ps` le confirme : toutes les copies tournent sur `manager`, et aucune sur `node1`, `node2` ou `node3`.

#### Sur tous les nœuds (`global`)

Fichier `swarm/hello-world-global.compose.yml` :

```yaml
services:
  hello:
    image: hello-world
    deploy:
      mode: global
```

```bash
docker compose exec manager docker stack rm hello
docker compose cp hello-world-global.compose.yml manager:/home/manager/
docker compose exec manager docker stack deploy -c /home/manager/hello-world-global.compose.yml hello
docker compose exec manager docker service ls
docker compose exec manager docker service ps hello_hello
```

<p align="center">
  <img src="screenshots/td2-12-stack-global.png" alt="Stack en mode global">
</p>

- `service ls` affiche le mode `global` : on ne choisit plus de nombre de copies, Swarm en place une par nœud.
- `service ps` le montre bien : **une copie par nœud**, sur `manager`, `node1`, `node2` et `node3`. Chaque copie porte d'ailleurs l'identifiant de son nœud dans son nom.
- Et si un nouveau nœud rejoint le cluster, Swarm y lance automatiquement sa copie.

---

# TD3

**Objectif :** placer un **reverse proxy**, Traefik, devant notre cluster Swarm.
<br/>Au lieu de retenir un port par application (`:8080`, `:8081`…), on tape une simple adresse comme `whoami.swarm.localhost` : Traefik lit le nom demandé par le navigateur et envoie la requête vers la bonne application.

## Exercice 1 : déployer Traefik

### 1.1 Relancer le cluster

On repart du cluster du TD2 (1 manager et 3 nœuds).
<br/>Seule nouveauté : le navigateur du PC doit pouvoir joindre Traefik, qui tournera dans le manager. On publie donc le port **80** du manager dans `swarm/compose.yml` :

```yaml
  manager:
    image: docker:dind
    hostname: manager
    privileged: true
    ports:
      - "80:80" # Traefik, reachable from the host browser
    volumes:
      - /home/manager
```

```bash
docker compose up -d
docker compose exec manager docker node ls
```

<p align="center">
  <img src="screenshots/td3-01-swarm-relaunch.png" alt="Relance du cluster avec le port 80 sur le manager">
</p>

- `up -d` ne touche pas aux 3 nœuds (`Running`) et recrée seulement le manager (`Recreated`), pour lui ajouter le port 80.
- Après quelques secondes, `node ls` montre les **4 nœuds `Ready`**, avec `manager` toujours `Leader` : le cluster est prêt.

### 1.2 Déployer Traefik sur le manager

La stack de Traefik est rangée dans `swarm/traefik.compose.yml`. Elle contient 2 services :

```yaml
services:
  traefik:
    image: traefik:v3.6
    networks:
      # Connect to the 'web' overlay network for inter-container communication across nodes
      - web
    ports:
      - 80:80 # HTTP
      # - 443:443   # HTTPS - Would work only on a server
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro # Swarm API socket
    command:
      # HTTP EntryPoint
      - "--entrypoints.web.address=:80"
      # Enable the Docker Swarm provider (instead of Docker provider)
      - "--providers.swarm.endpoint=unix:///var/run/docker.sock"
      # Watch for Swarm service changes (requires socket access)
      - "--providers.swarm.watch=true"
      # Recommended: Don't expose services by default; require explicit labels
      - "--providers.swarm.exposedbydefault=false"
      # Specify the default network for Traefik to connect to services
      - "--providers.swarm.network=web"
      # API & Dashboard
      - "--api.dashboard=true" # Enable the dashboard
      - "--api.insecure=true" # Explicitly disable insecure API mod
      # Observability
      - "--log.level=INFO" # Set the Log Level e.g INFO, DEBUG
      - "--accesslog=true" # Enable Access Logs
      # - "--metrics.prometheus=true" # Enable Prometheus
    deploy:
      mode: replicated
      replicas: 1
      placement:
        # Placement constraints restrict where Traefik tasks can run.
        # Running on manager nodes is common for accessing the Swarm API via the socket.
        constraints:
          - node.role == manager
      # Traefik Dynamic configuration via labels
      # In Swarm, labels on the service definition configure Traefik routing for that service.
      labels:
        - "traefik.enable=true"
        # Dashboard router
        - "traefik.http.routers.dashboard.rule=Host(`traefik.swarm.localhost`)"
        - "traefik.http.routers.dashboard.entrypoints=web"
        - "traefik.http.routers.dashboard.service=api@internal"
        - "traefik.http.services.dashboard.loadbalancer.server.port=8080"

  # Deploy the Whoami application
  whoami:
    image: traefik/whoami
    networks:
      - web
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.whoami.rule=Host(`whoami.swarm.localhost`)"
        - "traefik.http.routers.whoami.entrypoints=web"
        - "traefik.http.services.whoami.loadbalancer.server.port=80"

# Define the overlay network for Swarm
networks:
  web:
    external: true
```

**Le service `traefik`**, notre reverse proxy :
- il écoute sur le port **80** (`entrypoints.web.address=:80`) ;
- il lit le socket Docker (`/var/run/docker.sock`) pour découvrir tout seul les services du cluster (`providers.swarm`) ;
- `exposedbydefault=false` : un service n'est publié que s'il le demande lui-même, avec le label `traefik.enable=true` ;
- `node.role == manager` : il tourne forcément sur le manager, le seul nœud qui connaît tout le cluster (et le seul dont on a publié le port 80) ;
- ses propres labels publient son **tableau de bord** sur `traefik.swarm.localhost`.

**Le service `whoami`**, une petite application de test qui affiche des infos sur la requête reçue. Il n'expose **aucun port** : il se présente à Traefik avec ses labels.
- `traefik.http.routers.whoami.rule=Host(...)` : « envoie-moi les requêtes qui arrivent pour `whoami.swarm.localhost` » ;
- `traefik.http.services.whoami.loadbalancer.server.port=80` : « je réponds sur mon port 80 ».

Les deux services se branchent sur le réseau `web`, déclaré `external: true` : la stack ne le crée pas, il doit donc exister **avant** le déploiement.
<br/>On le crée en mode **overlay** : un réseau qui s'étend sur tous les nœuds du cluster. Traefik, sur le manager, peut ainsi parler à un conteneur placé sur n'importe quel autre nœud.

```bash
docker compose exec manager docker network create --driver overlay web
docker compose exec manager docker network ls --filter name=web
```

<p align="center">
  <img src="screenshots/td3-02-network-web.png" alt="Création du réseau overlay web">
</p>

Le réseau `web` existe, avec le driver `overlay` et la portée `swarm` : il est bien partagé par tout le cluster.

On fait d'abord le ménage du TD2 (`docker compose exec manager docker stack rm hello` et `docker compose exec manager docker service rm web`), puis on copie la stack dans le manager et on la déploie :

```bash
docker compose cp traefik.compose.yml manager:/home/manager/
docker compose exec manager docker stack deploy -c /home/manager/traefik.compose.yml traefik
docker compose exec manager docker service ls
```

<p align="center">
  <img src="screenshots/td3-03-traefik-deploy.png" alt="Déploiement de la stack Traefik">
</p>

- `stack deploy` crée les 2 services `traefik_traefik` et `traefik_whoami`.
- Les 2 services sont à **`1/1`** : Traefik et whoami tournent.
- Seul Traefik publie un port (`*:80->80/tcp`) : `whoami` reste caché derrière lui.

### 1.3 Accéder à Traefik depuis le navigateur

On travaille en local : aucun vrai nom de domaine ne pointe vers notre PC.
<br/>On passe donc par le **fichier hosts**, une sorte de mini-DNS interne à l'ordinateur, consulté en priorité et pris en compte immédiatement.
<br/>Sous Windows, il se trouve dans `C:\Windows\System32\drivers\etc\hosts` (il faut l'ouvrir en administrateur). On y ajoute nos 2 adresses, qui pointent vers notre propre machine :

```
127.0.0.1   traefik.swarm.localhost
127.0.0.1   whoami.swarm.localhost
```

<p align="center">
  <img src="screenshots/td3-04-hosts.png" alt="Les 2 domaines ajoutés au fichier hosts">
</p>

Le trajet d'une requête est alors le suivant :
1. le navigateur demande `whoami.swarm.localhost`, et le fichier hosts lui répond `127.0.0.1` ;
2. la requête arrive sur le port 80 du PC, qui mène au port 80 du manager ;
3. Traefik lit le nom demandé et transmet la requête au bon conteneur.

**Le tableau de bord de Traefik**, sur http://traefik.swarm.localhost :

<p align="center">
  <img src="screenshots/td3-05-traefik-dashboard.png" alt="Tableau de bord de Traefik">
</p>

On y retrouve le point d'entrée `web` sur le port **80**, et les routeurs et services découverts tout seuls grâce aux labels, sans aucune erreur.

**L'application whoami**, sur http://whoami.swarm.localhost :

<p align="center">
  <img src="screenshots/td3-06-whoami.png" alt="Page whoami servie par Traefik">
</p>

whoami nous renvoie le détail de la requête qu'elle a reçue :
- `Host: whoami.swarm.localhost` : c'est grâce à cet en-tête que Traefik a su vers quelle application envoyer la requête.
- Les en-têtes `X-Forwarded-…` sont ajoutés par Traefik : la requête est bien passée par le reverse proxy avant d'arriver au conteneur.
- Les adresses en `10.0.x.x` appartiennent aux réseaux internes de Swarm : `10.0.2.x` pour notre réseau overlay `web` (celui où Traefik joint whoami), et `10.0.0.x` pour le réseau d'entrée du cluster (`ingress`), par lequel la requête est arrivée sur le port 80.

La suite du TD3 (exercice 2) se trouve dans [voting-app/TD3.md](../voting-app/TD3.md).

## Exercice 3 : déployer Portainer

Jusqu'ici, on pilote le cluster en tapant des commandes dans le manager (`docker compose exec manager …`).
<br/>**Portainer** est une interface web qui permet de faire la même chose depuis le navigateur : voir les nœuds, les stacks, les services, et en déployer de nouvelles.

### 3.1 Déployer Portainer sur le cluster

On suit la documentation d'installation de Portainer pour Docker Swarm. On télécharge d'abord sa stack dans `swarm/portainer-agent-stack.yml` :

```yaml
version: '3.2'

services:
  agent:
    image: portainer/agent:lts
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes
    networks:
      - agent_network
    deploy:
      mode: global
      placement:
        constraints: [node.platform.os == linux]

  portainer:
    image: portainer/portainer-ce:lts
    command: -H tcp://tasks.agent:9001 --tlsskipverify
    ports:
      - "9443:9443"
      - "9000:9000"
      - "8000:8000"
    volumes:
      - portainer_data:/data
    networks:
      - agent_network
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints: [node.role == manager]

networks:
  agent_network:
    driver: overlay
    attachable: true

volumes:
  portainer_data:
```

Elle contient 2 services :
- `agent` : en mode `global`, il tourne sur **chaque nœud** et donne à Portainer accès au Docker de ce nœud (via `docker.sock`).
- `portainer` : l'interface elle-même, placée sur le manager (`node.role == manager`). Elle parle aux agents par le réseau overlay `agent_network`.

L'interface répond sur le port **9000** (HTTP) et **9443** (HTTPS). Le port 8000 ne sert que pour des agents distants, dont on n'a pas besoin ici.

```bash
curl -sL https://downloads.portainer.io/ce-lts/portainer-agent-stack.yml -o portainer-agent-stack.yml
docker compose cp portainer-agent-stack.yml manager:/home/manager/
docker compose exec manager docker stack deploy --with-registry-auth -c /home/manager/portainer-agent-stack.yml portainer
docker compose exec manager docker stack services portainer
docker compose exec manager docker ps --filter name=portainer --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

<p align="center">
  <img src="screenshots/td3-16-portainer-deploy.png" alt="Déploiement de la stack Portainer">
</p>

- `stack deploy` crée le réseau `portainer_agent_network` et les 2 services.
- `portainer_agent` affiche **`4/4`** en mode `global` : un agent sur chacun de nos 4 nœuds.
- `portainer_portainer` est à `1/1`, sur le manager. Comme le demande la documentation, `docker ps` montre bien les 2 conteneurs `portainer-ce` et `agent` sur le manager.
- Les ports 9000 et 9443 ne sont publiés qu'à l'intérieur du cluster : depuis le PC, on passera par Traefik à la question suivante.

### 3.2 Publier Portainer avec Traefik

Comme pour `whoami`, on ajoute à Portainer les labels qui le publient sur une nouvelle adresse, `portainer.swarm.localhost`. Son interface principale répond sur le port **9000**.
<br/>On le branche aussi sur le réseau `web`, sinon Traefik ne pourrait pas le joindre. Le tout est rangé dans une nouvelle version de la stack, `swarm/portainer-agent-stack.traefik.yml` :

```yaml
  portainer:
    image: portainer/portainer-ce:lts
    command: -H tcp://tasks.agent:9001 --tlsskipverify
    ports:
      - "9443:9443"
      - "9000:9000"
      - "8000:8000"
    volumes:
      - portainer_data:/data
    networks:
      - agent_network
      - web
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints: [node.role == manager]
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.portainer.rule=Host(`portainer.swarm.localhost`)"
        - "traefik.http.routers.portainer.entrypoints=web"
        - "traefik.http.services.portainer.loadbalancer.server.port=9000"

networks:
  agent_network:
    driver: overlay
    attachable: true
  web:
    external: true
```

On redéploie avec le même nom de stack, `portainer`, pour mettre à jour le service :

```bash
docker compose cp portainer-agent-stack.traefik.yml manager:/home/manager/
docker compose exec manager docker stack deploy --with-registry-auth -c /home/manager/portainer-agent-stack.traefik.yml portainer
docker compose exec manager docker stack services portainer
```

<p align="center">
  <img src="screenshots/td3-17-portainer-traefik.png" alt="Mise à jour de la stack Portainer avec Traefik">
</p>

- `stack deploy` affiche `Updating service` pour les 2 services : la stack est mise à jour, pas recréée.
- Les 2 services sont de nouveau au complet : `4/4` pour les agents, `1/1` pour Portainer.

### 3.3 Ouvrir Portainer dans le navigateur

On ajoute la nouvelle adresse dans le fichier hosts :

```
127.0.0.1   portainer.swarm.localhost
```

<p align="center">
  <img src="screenshots/td3-19-hosts-portainer.png" alt="L'adresse de Portainer dans le fichier hosts">
</p>

Au premier lancement, Portainer demande de créer un compte administrateur.
<br/>Les versions récentes demandent aussi un **setup token**, une sécurité qui prouve qu'on a bien accès au serveur. On le trouve dans les logs de Portainer :

```bash
docker compose exec manager docker service logs --raw portainer_portainer 2>&1 | grep -A2 setup_token=
```

<p align="center">
  <img src="screenshots/td3-18-portainer-token.png" alt="Le setup token dans les logs de Portainer">
</p>

On ouvre http://portainer.swarm.localhost, et on crée le compte `admin` avec un mot de passe d'au moins 12 caractères et le token :

<p align="center">
  <img src="screenshots/td3-20-portainer-setup.png" alt="Création du compte administrateur de Portainer">
</p>

> **Attention :** Portainer ne laisse que **5 minutes** après son démarrage pour créer ce compte. Passé ce délai, il s'arrête par sécurité, et il faut le relancer.

**L'accueil de Portainer** :

<p align="center">
  <img src="screenshots/td3-21-portainer-home.png" alt="Accueil de Portainer avec l'environnement primary">
</p>

Portainer a trouvé notre cluster tout seul, grâce aux agents : l'environnement `primary` est `Up`, de type **Swarm**, avec ses **4 nœuds**.

**La liste des stacks**, dans `primary` puis **Stacks** :

<p align="center">
  <img src="screenshots/td3-22-portainer-stacks.png" alt="Liste des stacks dans Portainer">
</p>

On retrouve bien nos 3 stacks : `portainer`, `traefik` et `voting`.
<br/>Elles sont marquées **Limited** : elles ont été créées en ligne de commande, et non depuis Portainer, qui ne peut donc pas modifier leur fichier.

## Exercice 4 : déployer l'API de MFP depuis Portainer

Les questions 4.1 à 4.3 (redéployer l'application de vote depuis Portainer) se trouvent dans [voting-app/TD3.md](../voting-app/TD3.md#exercice-4--redéployer-lapplication-de-vote).

### 4.4 Créer une stack pour l'API de MFP

On écrit une stack pour l'API, `swarm/mfp-api.stack.yml`. Elle reprend la base et le serveur de notre `compose.yml`, avec 2 différences :
- le serveur utilise l'image publiée sur GHCR (prérequis du TD2), puisque Swarm ne sait pas construire d'images ;
- au lieu de publier le port 3000, le serveur passe par Traefik, sur l'adresse `api.swarm.localhost`.

```yaml
services:
  db:
    image: postgres:17
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: supersecret
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - backend

  server:
    image: ghcr.io/dark-shad0w/clusterisation-conteneurs/server:latest
    networks:
      - backend
      - web
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.mfp-api.rule=Host(`api.swarm.localhost`)"
        - "traefik.http.routers.mfp-api.entrypoints=web"
        - "traefik.http.services.mfp-api.loadbalancer.server.port=3000"

networks:
  backend:
  web:
    external: true

volumes:
  db-data:
```

- `db` reste sur le réseau `backend` : seul le serveur peut lui parler, et il le trouve toujours par son nom, `db`.
- `server` est aussi sur `web`, pour que Traefik puisse lui transmettre les requêtes.

Dans Portainer, on crée la stack comme à la question 4.2 : **Add stack**, nom `mfp`, **Upload** du fichier, puis **Deploy the stack**.

<p align="center">
  <img src="screenshots/td3-29-portainer-add-mfp.png" alt="Création de la stack mfp dans Portainer">
</p>

<p align="center">
  <img src="screenshots/td3-30-portainer-stacks-mfp.png" alt="La stack mfp dans la liste des stacks">
</p>

<p align="center">
  <img src="screenshots/td3-31-portainer-mfp-services.png" alt="Les services de la stack mfp">
</p>

La stack `mfp` apparaît, créée par `admin`, avec ses 2 services au complet : `mfp_db` et `mfp_server`.

> **Problème rencontré :** au premier démarrage, le serveur s'arrête sur `unable to connect to db: getaddrinfo ENOTFOUND db`. Swarm lance les 2 services en même temps, et la base n'existait pas encore.
> <br/>**Solution :** rien à faire. Swarm relance automatiquement le serveur, qui se connecte au deuxième essai (`connected to PgSQL db`, puis `server started on port 3000`).

On ajoute l'adresse de l'API dans le fichier hosts :

```
127.0.0.1   api.swarm.localhost
```

<p align="center">
  <img src="screenshots/td3-32-hosts-api.png" alt="L'adresse de l'API dans le fichier hosts">
</p>

**Test avec Bruno.** Notre collection vise `http://localhost:3000`. Pour ne pas la modifier, on en fait une copie dans laquelle on remplace l'adresse par `http://api.swarm.localhost`, puis on lance les 3 requêtes avec le Bruno CLI (`bru run`) :

```bash
cp -r mfp-bruno-api-test-collection ~/mfp-bruno-swarm
sed -i 's#http://localhost:3000#http://api.swarm.localhost#' ~/mfp-bruno-swarm/*.yml
cd ~/mfp-bruno-swarm && bru run
```

<p align="center">
  <img src="screenshots/td3-33-bruno-swarm.png" alt="Les 3 requêtes Bruno vers l'API sur le cluster">
</p>

Les 3 requêtes répondent `200 OK`, et les 3 tests passent (**PASS**) :
- `01-create-user` crée l'utilisateur dans la base du cluster ;
- `02-login` renvoie un token ;
- `03-my-profile` utilise ce token pour lire le profil.

L'API de MFP tourne donc sur le cluster, et répond depuis le PC à l'adresse `api.swarm.localhost`.

---

# TD4

**Objectif :** utiliser les **secrets** et les **configs** de Docker Swarm.
<br/>Certaines informations (mots de passe, clés, fichiers de configuration) doivent être lues par des conteneurs qui peuvent tourner sur n'importe quel nœud. Un volume ou un fichier `.env` ne suffit plus : ils restent sur une seule machine.
<br/>Swarm stocke donc lui-même ces informations, chiffrées, et les monte comme des **fichiers** dans les conteneurs qui en ont besoin :
- un **secret** sert aux informations sensibles : une fois créé, on ne peut plus ni le lire ni le modifier ;
- une **config** sert aux fichiers de configuration : on peut la relire, mais pas la modifier. Pour la mettre à jour, il faut en créer une nouvelle.

Toutes les commandes se lancent depuis le dossier `swarm/`.

## Prérequis : relancer le cluster et passer en HTTPS

### Relancer le cluster

On repart du cluster du TD3. Pour cet exercice, Traefik devra aussi répondre en **HTTPS** (on voit pourquoi juste après) : on publie donc aussi le port **443** du manager dans `swarm/compose.yml`.

```yaml
  manager:
    image: docker:dind
    hostname: manager
    privileged: true
    ports:
      - "80:80" # Traefik, reachable from the host browser
      - "443:443" # Traefik HTTPS (TD4: Authelia only works over https)
    volumes:
      - /home/manager
```

```bash
docker compose up -d
docker compose ps
docker compose exec manager docker node ls
```

<p align="center">
  <img src="screenshots/td4-01-cluster-up.png" alt="Le manager recréé avec le port 443, les nœuds Down">
</p>

`up -d` recrée le manager pour lui ajouter le port 443 (`0.0.0.0:443->443/tcp`).
<br/>Mais, comme après le redémarrage du TD2, les conteneurs ont changé d'adresse IP : `node1`, `node2` et `node3` sont `Down`. On reconstruit donc le cluster avec les mêmes commandes que dans la partie [Redémarrage du cluster](#redémarrage-du-cluster) :

```bash
docker compose exec node1 docker swarm leave --force
docker compose exec node2 docker swarm leave --force
docker compose exec node3 docker swarm leave --force
docker compose exec manager docker swarm leave --force

docker compose exec manager docker swarm init
TOKEN=$(docker compose exec manager docker swarm join-token -q worker)
docker compose exec node1 docker swarm join --token $TOKEN manager:2377
docker compose exec node2 docker swarm join --token $TOKEN manager:2377
docker compose exec node3 docker swarm join --token $TOKEN manager:2377

docker compose exec manager docker node ls
```

<p align="center">
  <img src="screenshots/td4-02-swarm-rebuild.png" alt="Cluster reconstruit">
</p>

Les 4 nœuds sont de nouveau `Ready`, avec `manager` en `Leader`.
<br/>En quittant l'ancien cluster, on a perdu ses stacks et son réseau `web` : on redéploie Traefik et Portainer plus bas. Les volumes, eux, sont restés sur les nœuds. Les stacks du TD3 (vote et API de MFP) ne servent pas ici, on ne les relance pas.

### Pourquoi HTTPS ?

Authelia (question 1.2) refuse de démarrer si son adresse ne commence pas par `https://`, même pour un test en local : sa session repose sur un cookie sécurisé, qui ne voyage que sur une connexion chiffrée. Or notre Traefik ne parle qu'en HTTP.
<br/>Un vrai certificat (Let's Encrypt par exemple) n'est délivré que pour un vrai nom de domaine, joignable depuis Internet. On fabrique donc le nôtre :
1. une petite **autorité de certification** (CA) locale ;
2. un certificat pour `*.swarm.localhost`, signé par cette CA ;
3. Windows fait confiance à notre CA : le navigateur accepte alors le certificat, sans avertissement.

### Créer le certificat

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -noenc -days 3650 -subj "/CN=Swarm Local CA" -keyout certs/ca.key -out certs/ca.crt
openssl req -newkey rsa:2048 -noenc -subj "/CN=*.swarm.localhost" -keyout certs/swarm.localhost.key -out certs/swarm.localhost.csr
openssl x509 -req -in certs/swarm.localhost.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -days 365 -extfile <(printf "subjectAltName=DNS:*.swarm.localhost,DNS:swarm.localhost") -out certs/swarm.localhost.crt
ls certs
openssl verify -CAfile certs/ca.crt certs/swarm.localhost.crt
```

<p align="center">
  <img src="screenshots/td4-03-certs.png" alt="Création de la CA et du certificat *.swarm.localhost">
</p>

- `ca.crt` et `ca.key` : notre autorité de certification.
- `swarm.localhost.crt` et `swarm.localhost.key` : le certificat et sa clé privée, valables pour toutes les adresses en `.swarm.localhost` (c'est le rôle du `*`).
- `openssl verify` répond `OK` : le certificat est bien signé par notre CA.

Le dossier `certs/` est ignoré par Git (`swarm/.gitignore`) : une clé privée ne doit jamais être publiée.

On ajoute ensuite la CA aux autorités de confiance de Windows, pour l'utilisateur courant. Windows demande une confirmation, qu'on accepte :

```bash
certutil.exe -user -addstore Root "$(wslpath -w certs/ca.crt)"
```

<p align="center">
  <img src="screenshots/td4-04-ca-trust.png" alt="La CA ajoutée aux autorités de confiance de Windows">
</p>

### Le certificat dans le cluster : un secret et des configs

C'est la première utilisation des briques du cours. Traefik a besoin de 3 fichiers :

| Fichier | Contenu | Rangé dans |
|---|---|---|
| `certs/swarm.localhost.key` | la clé privée du certificat | le **secret** `swarm_localhost_key`, car elle est sensible |
| `certs/swarm.localhost.crt` | le certificat, qui est public | la **config** `swarm_localhost_crt` |
| `traefik-tls.yml` | indique à Traefik le certificat à utiliser par défaut | la **config** `traefik_tls` |

`swarm/traefik-tls.yml` :

```yaml
tls:
  stores:
    default:
      defaultCertificate:
        certFile: /certs/swarm.localhost.crt # config swarm_localhost_crt
        keyFile: /run/secrets/swarm.localhost.key # secret swarm_localhost_key
```

On les crée avec les commandes Docker. Le `-` final indique que le contenu arrive par l'entrée standard, ici le fichier. On recrée aussi le réseau `web`, perdu avec l'ancien cluster :

```bash
docker compose exec manager docker network create --driver overlay web
docker compose exec -T manager docker config create swarm_localhost_crt - < certs/swarm.localhost.crt
docker compose exec -T manager docker config create traefik_tls - < traefik-tls.yml
docker compose exec -T manager docker secret create swarm_localhost_key - < certs/swarm.localhost.key
docker compose exec manager docker config ls
docker compose exec manager docker secret ls
```

<p align="center">
  <img src="screenshots/td4-05-tls-secret-config.png" alt="Création du réseau web, des 2 configs et du secret">
</p>

On voit tout de suite la différence entre les deux en les inspectant :

```bash
docker compose exec manager docker config inspect --pretty traefik_tls
docker compose exec manager docker secret inspect --pretty swarm_localhost_key
```

<p align="center">
  <img src="screenshots/td4-06-inspect-config-secret.png" alt="Une config affiche son contenu, un secret non">
</p>

- La config affiche son contenu (`Data`) : elle est **consultable**.
- Le secret n'affiche que son nom et ses dates : il n'est **pas consultable**, même par l'administrateur du cluster.

### Traefik en HTTPS

La nouvelle stack, `swarm/traefik-https.stack.yml`, reprend celle du TD3 (`traefik.compose.yml`). Voici ce qui change :

```yaml
services:
  traefik:
    image: traefik:v3.6
    networks:
      web:
        aliases:
          # containers of the cluster (Dozzle, Outline) reach Authelia's https address through Traefik
          - authelia.swarm.localhost
    ports:
      - 80:80 # HTTP
      - 443:443 # HTTPS
    configs:
      - source: traefik_tls
        target: /etc/traefik/tls.yml
      - source: swarm_localhost_crt
        target: /certs/swarm.localhost.crt
    secrets:
      - source: swarm_localhost_key
        target: swarm.localhost.key # mounted in /run/secrets/
    command:
      # EntryPoints: HTTP on 80, HTTPS on 443
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.websecure.http.tls=true"
      # ... (Swarm provider, dashboard and logs unchanged)
      # File provider: the default certificate (traefik-tls.yml)
      - "--providers.file.filename=/etc/traefik/tls.yml"
    deploy:
      labels:
        # ... (dashboard router unchanged)
        # Any other http request is redirected to https (lowest priority, so the
        # http routers of the TD3 apps still win)
        - "traefik.http.routers.to-https.rule=HostRegexp(`.+`)"
        - "traefik.http.routers.to-https.entrypoints=web"
        - "traefik.http.routers.to-https.priority=1"
        - "traefik.http.routers.to-https.middlewares=to-https"
        - "traefik.http.routers.to-https.service=noop@internal"
        - "traefik.http.middlewares.to-https.redirectscheme.scheme=https"

  whoami:
    # ...
        - "traefik.http.routers.whoami.entrypoints=web,websecure"

# Created beforehand with `docker config create` and `docker secret create`
configs:
  traefik_tls:
    external: true
  swarm_localhost_crt:
    external: true

secrets:
  swarm_localhost_key:
    external: true
```

- Un nouveau point d'entrée, `websecure`, écoute sur le port **443** en TLS. Son certificat par défaut est indiqué dans `tls.yml`, lu par le provider `file`.
- Les configs et le secret arrivent dans le conteneur sous forme de **fichiers** : les configs à l'endroit choisi (`target`), le secret dans `/run/secrets/`.
- `external: true` : ils existent déjà, la stack ne les crée pas.
- Le routeur `to-https` renvoie vers `https://` toute adresse http qui n'a pas son propre routeur. Avec sa priorité de 1 (la plus basse), les adresses http du TD3 (`whoami`, tableau de bord…) continuent de fonctionner.
- L'alias `authelia.swarm.localhost` servira à la question 1.2.
- `whoami` répond maintenant sur les 2 points d'entrée, pour tester le HTTPS.

```bash
docker compose cp traefik-https.stack.yml manager:/home/manager/
docker compose exec manager docker stack deploy -c /home/manager/traefik-https.stack.yml traefik
docker compose exec manager docker service ls
```

<p align="center">
  <img src="screenshots/td4-07-traefik-https.png" alt="Déploiement de Traefik avec HTTPS">
</p>

Traefik publie maintenant les ports 80 **et** 443. On teste depuis WSL : `--cacert` indique à `curl` notre CA, puisque WSL ne lit pas les autorités de confiance de Windows.

```bash
curl -s --cacert certs/ca.crt https://whoami.swarm.localhost | head -4
curl -sI http://dozzle.swarm.localhost | head -2
```

<p align="center">
  <img src="screenshots/td4-08-https-test.png" alt="whoami en HTTPS et la redirection vers https">
</p>

- `whoami` répond en **HTTPS**, et `curl` accepte le certificat.
- Une adresse sans routeur http, comme `dozzle.swarm.localhost`, est redirigée vers `https://` (`307 Temporary Redirect`).

**Le tableau de bord de Traefik**, sur http://traefik.swarm.localhost :

<p align="center">
  <img src="screenshots/td4-09-traefik-dashboard.png" alt="Tableau de bord de Traefik avec les points d'entrée web et websecure">
</p>

On y voit les 2 points d'entrée, `web` sur `:80` et `websecure` sur `:443`, et les 2 providers, `Swarm` et `File`, sans aucune erreur.

### Relancer Portainer

On redéploie la stack du TD3, sans rien y changer :

```bash
docker compose exec manager docker volume ls
docker compose cp portainer-agent-stack.traefik.yml manager:/home/manager/
docker compose exec manager docker stack deploy -c /home/manager/portainer-agent-stack.traefik.yml portainer
docker compose exec manager docker service ls
```

<p align="center">
  <img src="screenshots/td4-10-portainer-redeploy.png" alt="Portainer redéployé">
</p>

Le volume `portainer_portainer_data` est resté sur le manager : Portainer retrouve son compte `admin`, pas besoin de le recréer.

### Les nouvelles adresses dans le fichier hosts

Comme au TD3, on ajoute les 3 adresses de l'exercice dans le fichier hosts de Windows (en administrateur) :

```
127.0.0.1 dozzle.swarm.localhost
127.0.0.1 authelia.swarm.localhost
127.0.0.1 outline.swarm.localhost
```

<p align="center">
  <img src="screenshots/td4-11-hosts.png" alt="Les 3 adresses ajoutées au fichier hosts">
</p>
