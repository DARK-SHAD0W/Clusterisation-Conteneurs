# Clusterisation de conteneurs

Travaux du module **Clusterisation de conteneurs** (ESGI Lyon, 5ESGI AL + IABD).
<br/>Le dépôt est rangé en deux dossiers, un par application. Chacun a son propre README, qui raconte la démarche étape par étape.

| Dossier | Application | Ce qu'on y trouve |
|---|---|---|
| [`mfp/`](mfp/README.md) | **My Favorite Places** : client React, API Node.js/Express, PostgreSQL | TD1 (Docker, Compose), TD2 (cluster Docker Swarm), TD3 exercice 1 (Traefik) |
| [`voting-app/`](voting-app/README.md) | **Example Voting App** : l'application de vote fournie par le professeur | TD3 exercice 2 (Docker Compose, Swarm et Traefik) |

## Sommaire

**[My Favorite Places](mfp/README.md)**

- [TD1 : dockerisation de l'application](mfp/README.md#td1)
- [TD2 : cluster Docker Swarm](mfp/README.md#td2)
- [TD3 : Traefik, exercice 1](mfp/README.md#td3)

**[Example Voting App](voting-app/README.md)**

- TD3 : Traefik, exercice 2

## Structure du dépôt

```
.
├── .github/workflows/   # CI : construit et publie les images de mfp sur GHCR
├── mfp/                 # My Favorite Places + cluster Swarm (swarm/)
│   └── README.md
└── voting-app/          # application de vote
    ├── example-voting-app/   # copie intacte du dépôt du professeur
    └── README.md
```

Toutes les commandes se lancent dans un terminal **WSL (Ubuntu)**, depuis le dossier indiqué dans chaque README.
