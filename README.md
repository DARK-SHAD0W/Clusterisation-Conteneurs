# Clusterisation de conteneurs

Projet du module **Clusterisation de conteneurs** (ESGI Lyon, 5ESGI AL + IABD).
<br/>Le dépôt contient deux applications, chacune dans son dossier et avec sa propre documentation.

| Dossier | Application | Documentation |
|---|---|---|
| `mfp/` | **My Favorite Places** : un client React, une API Node.js/Express et une base PostgreSQL. | [mfp/TD2.md](mfp/TD2.md) |
| `voting-app/` | **Voting App** : une application de vote répartie en 5 services. | [voting-app/TD3.md](voting-app/TD3.md) |

## Sommaire

**My Favorite Places**

- [TD1 : dockerisation de l'application](mfp/TD2.md#td1)
- [TD2 : cluster Docker Swarm](mfp/TD2.md#td2)
- [TD3 : Traefik, exercice 1](mfp/TD2.md#td3)
- [TD3 : Portainer, exercice 3](mfp/TD2.md#exercice-3--déployer-portainer)
- [TD3 : Portainer, exercice 4.4 (API de MFP)](mfp/TD2.md#exercice-4--déployer-lapi-de-mfp-depuis-portainer)
- [TD4 : secrets et configs (Dozzle, Authelia, Outline)](mfp/TD2.md#td4)

**Voting App**

- [TD3 : Traefik, exercice 2](voting-app/TD3.md#td3)
- [TD3 : Portainer, exercice 4.1 à 4.3](voting-app/TD3.md#exercice-4--redéployer-lapplication-de-vote)

## Structure du dépôt

```
.
├── .github/workflows/   # construit et publie les images de mfp sur GHCR
├── mfp/                 # My Favorite Places et le cluster Docker Swarm (documentation dans TD2.md)
└── voting-app/          # Voting App (documentation dans TD3.md)
```

Toutes les commandes se lancent dans un terminal **WSL (Ubuntu)**, depuis le dossier indiqué dans chaque documentation.
