# Voting App : Clusterisation de conteneurs

Deuxième application du module **Clusterisation de conteneurs** (ESGI Lyon, 5ESGI AL + IABD).
<br/>Le but : faire tourner une application de vote, d'abord avec Docker Compose, puis sur notre cluster Docker Swarm, derrière Traefik.

Ce document fait suite à l'[exercice 1 du TD3](../mfp/README.md#exercice-1--déployer-traefik), où Traefik a été déployé sur le cluster.
<br/>Retour au [sommaire général](../README.md).

## Sommaire

**TD3**

- [Exercice 2 : déployer une autre application](#exercice-2--déployer-une-autre-application)

## Structure du dossier

```
voting-app/
├── vote/                 # site de vote (Python)
├── result/               # site des résultats (Node.js)
├── worker/               # traitement des votes (.NET)
├── healthchecks/         # scripts de vérification de redis et de la base
├── docker-compose.yml    # lancement en local
├── docker-stack.yml      # stack pour Docker Swarm
├── screenshots/          # captures d'écran
└── TD3.md                # ce document
```

---

# TD3

## Exercice 2 : déployer une autre application

### 2.1 Tester l'application avec Docker Compose

L'application est découpée en 5 services :

- `vote` : le site sur lequel on vote, entre **Cats** et **Dogs**. Chaque vote est envoyé dans redis.
- `redis` : une file d'attente, où les votes patientent avant d'être traités.
- `worker` : il récupère les votes dans redis et les enregistre dans la base.
- `db` : la base PostgreSQL, qui garde tous les votes.
- `result` : le site qui lit la base et affiche les résultats en direct.

Le fichier `docker-compose.yml` sépare ces services sur 2 réseaux : `front-tier` pour les sites, `back-tier` pour redis, le worker et la base.
<br/>Les sites sont publiés sur 2 ports : **8080** pour le vote et **8081** pour les résultats.

On lance tout depuis le dossier `voting-app/` :

```bash
docker compose up -d
docker compose ps --format 'table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

<p align="center">
  <img src="screenshots/td3-07-voting-compose-up.png" alt="Lancement de l'application avec Docker Compose">
</p>

- `up -d` construit les images de `vote`, `result` et `worker`, puis démarre les 5 conteneurs. La construction est longue : on ne garde ici que la fin de la sortie.
- `ps` montre les 5 conteneurs `Up`. Redis et la base sont `healthy` : leurs scripts de vérification répondent.
- Seuls `vote` (port 8080) et `result` (port 8081) sont accessibles depuis le PC.

**Le site de vote**, sur http://localhost:8080 :

<p align="center">
  <img src="screenshots/td3-08-vote-local.png" alt="Site de vote en local">
</p>

On vote une fois pour **Cats**. Ici, on passe par `curl`, ce qui revient à cliquer sur le bouton :

```bash
curl -X POST -d vote=a http://localhost:8080/
```

**Le site des résultats**, sur http://localhost:8081 :

<p align="center">
  <img src="screenshots/td3-09-result-local.png" alt="Site des résultats en local">
</p>

Le vote apparaît : **1 vote**, 100 % pour Cats.
<br/>Il a fait tout le trajet : le site de vote l'a posé dans redis, le worker l'a enregistré dans la base, et le site des résultats l'a lu.

Une fois le test terminé, on arrête l'application avec `docker compose down`.
