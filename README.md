# My Favorite Places — Clusterisation de conteneurs

Projet du module **Clusterisation de conteneurs** (ESGI Lyon, 5ESGI AL + IABD).
<br/>L'objectif est de conteneuriser, orchestrer puis gérer la montée en charge de l'application **My Favorite Places** (un client React et une API Node.js/Express qui stocke ses données dans PostgreSQL).

Ce README documente **toute la démarche, étape par étape**. 
<br/>Chaque nouvelle étape du module ajoute une section à la suite.

## Sommaire

1. [Test initial avec Bruno](#1-test-initial-avec-bruno)

## Structure du dépôt

```
.
├── client/                          # application React (Vite)
├── server/                          # API Node.js / Express / TypeORM
├── mfp-bruno-api-test-collection/   # collection Bruno pour tester l'API
└── screenshots/                     # captures d'écran des tests
```

## Environnement de travail

| Outil | Version | Remarque |
|---|---|---|
| Docker Engine | 29.7.2 | installé dans WSL2 (Ubuntu 24.04), sans Docker Desktop |
| Docker Compose | v5.5.0 | plugin `docker compose` |
| Node.js / Yarn | 22.23.2 / 1.22.22 | installés dans WSL via nvm |
| Bruno | 4.2.1 | client API installé sous Windows |

Toutes les commandes sont lancées depuis un terminal **WSL (Ubuntu)**, à la racine du dépôt.

---

## 1. Test initial avec Bruno

**Objectif (TD1, étape 1) :** prendre en main le projet, lancer l'API en local avec `yarn dev` et vérifier qu'elle répond, avant toute dockerisation.

### 1.1 Prérequis : lancer d'abord une base PostgreSQL

Le serveur ne démarre **que s'il arrive à se connecter à PostgreSQL**. 
<br/>Sans base, le serveur affiche `🚨 unable to connect to db` et n'écoute jamais sur le port 3000.

Les paramètres de connexion sont écrits en dur dans `server/src/datasource.ts` :

| Paramètre | Valeur |
|---|---|
| host | `localhost` |
| port | `5432` (port par défaut) |
| username | `postgres` |
| password | `supersecret` |
| database | `postgres` |

L'option `synchronize: true` de TypeORM crée automatiquement les tables `user` et `address` au démarrage.
<br/>Il suffit donc de fournir une base PostgreSQL vide.

On lance une base PostgreSQL dans un conteneur Docker, avec ces identifiants :

```bash
docker run -d --name mfp-db \
  -e POSTGRES_PASSWORD=supersecret \
  -p 5432:5432 \
  postgres:17
```

- `-e POSTGRES_PASSWORD=supersecret` : mot de passe de l'utilisateur `postgres`, identique à celui attendu par le serveur.
- `-p 5432:5432` : expose le port de la base sur `localhost`, pour que le serveur (lancé hors Docker) puisse la joindre.

On vérifie avec `docker ps` que le conteneur `mfp-db` est bien démarré (statut `Up`, port `5432` exposé) :

![Lancement de la base PostgreSQL](screenshots/td1-00-postgres-db.png)

### 1.2 Lancer l'API en mode développement

```bash
cd server
yarn install
yarn dev
```

`yarn dev` lance `nodemon src/index.ts`
<br/>Le démarrage est réussi lorsque la console affiche :

```
✅ connected to PgSQL db
🚀 server started on port 3000
```

![Démarrage du serveur avec yarn dev](screenshots/td1-00-yarn-dev.png)

### 1.3 Routes de l'API

Toutes les routes sont préfixées par `/api` et l'API écoute sur `http://localhost:3000`.

| Méthode | Route | Authentification | Rôle |
|---|---|---|---|
| POST | `/api/users` | non | créer un utilisateur (`email`, `password`) |
| POST | `/api/users/tokens` | non | se connecter et obtenir un JWT |
| GET | `/api/users/me` | oui | profil de l'utilisateur connecté |
| POST | `/api/addresses` | oui | ajouter une adresse |
| GET | `/api/addresses` | oui | lister ses adresses |
| POST | `/api/addresses/searches` | oui | rechercher ses adresses dans un rayon (en km) autour d'un point |

L'authentification se fait avec le header `Authorization: Bearer <token>`. 

### 1.4 Collection Bruno

La collection est versionnée dans `mfp-bruno-api-test-collection/` (ouvrir ce dossier dans Bruno). 
Elle contient 3 requêtes, à exécuter dans l'ordre :

| # | Requête | Résultat attendu |
|---|---|---|
| 01 | Create user | `200`, l'utilisateur créé |
| 02 | Login (get token) | `200`, `{ "token": "..." }` |
| 03 | My profile | `200`, l'utilisateur connecté |

Utilisateur de test : **ahmed test 1**, email `ahmedtest@gmail.com`, mot de passe `azerty123`.

### 1.5 Résultats des tests

#### 01 — Créer un utilisateur

`POST http://localhost:3000/api/users`

```json
{
  "email": "ahmedtest@gmail.com",
  "password": "azerty123"
}
```

![01 - Create user](screenshots/td1-01-create-user.png)

#### 02 — Se connecter (obtenir un token)

`POST http://localhost:3000/api/users/tokens` (même corps que la requête 01)

![02 - Login](screenshots/td1-02-login.png)

#### 03 — Mon profil

`GET http://localhost:3000/api/users/me` (header `Authorization: Bearer {{token}}`)

![03 - My profile](screenshots/td1-03-my-profile.png)
