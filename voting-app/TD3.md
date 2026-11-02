# Example Voting App : Clusterisation de conteneurs

Application de vote utilisée pour l'exercice 2 du TD3 (Traefik), après le déploiement de Traefik fait dans [`mfp/`](../mfp/README.md#exercice-1--déployer-traefik).
<br/>Retour au [sommaire général](../README.md).

## Structure du dossier

Le dossier `voting-app/` est une copie du dépôt [dockersamples/example-voting-app](https://github.com/dockersamples/example-voting-app) (commit `63e9150`), sans son historique Git.
<br/>On ne modifie aucun de ses fichiers (son `README.md` est celui d'origine) : on ajoute seulement les nôtres à côté.

```
voting-app/
├── vote/  result/  worker/  seed-data/  healthchecks/  # code de l'application (professeur)
├── docker-compose.yml                                  # lancement local (professeur)
├── docker-stack.yml                                    # stack Swarm fournie (professeur)
├── README.md                                           # README d'origine (professeur)
├── TD3.md                                              # notre documentation
└── screenshots/                                        # nos captures d'écran
```

---

# TD3

## Exercice 2 : déployer une autre application
