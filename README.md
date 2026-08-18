# CESIZen — Déploiement, maintenance et sécurisation

Infrastructure, chaîne d'intégration et de déploiement continus, outillage de
maintenance et dispositif de sécurisation de l'application **CESIZen**,
plateforme grand public de prévention en santé mentale.

Ce dépôt constitue le rendu de l'activité 3 du titre *Concepteur Développeur
d'Applications* : **Déployer et sécuriser les applications informatiques**.

---

## Contenu

```
.
├── DOSSIER_BLOC3_CESIZEN.docx    Dossier écrit (20 pages)
├── deploy/                       Infrastructure
│   ├── Dockerfile                Image API, multi-stage, exécution sans privilèges
│   ├── docker-compose.yml        Environnement de développement
│   ├── docker-compose.prod.yml   Recette et production (Traefik, Postgres, Redis, sauvegardes)
│   ├── .env.example              Modèle de configuration (le .env réel n'est jamais versionné)
│   ├── traefik/dynamic/          En-têtes de sécurité HTTP et limitation de débit
│   ├── postgres/init/            Extensions et rôle en lecture seule
│   └── scripts/                  Sauvegarde chiffrée et restauration
├── .github/
│   ├── workflows/                CI, déploiement recette, déploiement production, veille sécurité
│   ├── ISSUE_TEMPLATE/           Anomalie, évolution, incident de sécurité
│   ├── scripts/                  Contrôle des invariants d'infrastructure
│   ├── labels.yml                Référentiel d'étiquettes (sévérité, priorité, module)
│   └── dependabot.yml            Mise à jour automatisée des dépendances
└── docs/
    ├── DEMO.md                   Guide de démonstration et déroulé de soutenance
    └── figures/                  Schémas du dossier
```

## Intégration continue

La chaîne s'adapte au contenu du dépôt : un travail de détection identifie les
composants présents, et les contrôles applicatifs ne s'exécutent que lorsque le
code correspondant existe.

| Travail | Condition | Contenu |
|---|---|---|
| `detection` | toujours | Identifie `backend/` et `mobile/` |
| `infrastructure` | toujours | 31 invariants de sécurité, syntaxe des scripts, validation des compositions Docker |
| `lint` | `backend/` présent | `ruff`, `black` |
| `tests` | `backend/` présent | `pytest` sur PostgreSQL, couverture ≥ 70 % |
| `securite` | `backend/` présent | `bandit`, `pip-audit`, `check --deploy`, Trivy |
| `mobile` | `mobile/` présent | `eslint`, Jest, `npm audit` |

Les invariants d'infrastructure sont vérifiables en local :

```bash
pip install pyyaml
python3 .github/scripts/validate_infra.py
```

## Déploiement

Les travaux agissant sur une infrastructure réelle sont conditionnés à la
variable de dépôt `DEPLOY_ENABLED`. En son absence, un travail de démonstration
s'exécute à leur place : il vérifie la configuration et déroule la séquence de
déploiement sans rien provisionner.

```bash
# Bascule vers un déploiement réel
gh variable set DEPLOY_ENABLED --body true
gh secret  set STAGING_HOST    --body "recette.cesizen.fr"
gh secret  set STAGING_SSH_KEY < ~/.ssh/cesizen_deploy
```

L'installation d'un serveur est décrite dans [`deploy/README.md`](deploy/README.md).

## Documentation

- [Dossier écrit](DOSSIER_BLOC3_CESIZEN.docx) — plans de déploiement, de maintenance et de sécurisation
- [Guide de démonstration](docs/DEMO.md) — préparation, déroulé de soutenance, questions du jury
- [Guide d'installation](deploy/README.md) — développement local et installation d'un serveur

---

Barthélémy Le Bel — CDA 2026
