# Guide de démonstration — soutenance Bloc 3

Ce document décrit ce qu'il faut montrer, dans quel ordre, et ce que chaque
élément prouve au regard de la grille d'évaluation.

---

## 0. Préparation (à faire une fois, avant la soutenance)

```bash
# 1. Déposer les fichiers dans le dépôt du prototype
cp -r deploy .github docs /chemin/vers/cesizen/
cd /chemin/vers/cesizen

# 2. Vérifier que les chemins des workflows correspondent à votre arborescence
#    ci.yml suppose  backend/  (Django)  et  mobile/  (Expo)
ls backend/requirements.txt mobile/package.json

# 3. Créer le référentiel d'étiquettes
gh label create --file .github/labels.yml     # ou création manuelle dans l'interface

# 4. Pousser sur une branche puis ouvrir une pull request vers develop
git switch -c chore/chaine-cicd
git add deploy .github docs
git commit -m "chore: chaîne de déploiement, ticketing et sécurisation"
git push -u origin chore/chaine-cicd
gh pr create --base develop
```

L'ouverture de la *pull request* déclenche la chaîne d'intégration continue :
c'est cette exécution qui fournit la majorité des copies d'écran.

### Protections à activer dans l'interface GitHub

| Emplacement | Réglage |
|---|---|
| Settings > Branches | Règle sur `main` et `develop` : *pull request* obligatoire, contrôles CI obligatoires, historique linéaire |
| Settings > Environments | Créer `recette` et `production` ; sur `production`, cocher *Required reviewers* |
| Settings > Code security | Activer *Secret scanning*, *Push protection*, *Dependabot alerts* |
| Projects | Créer « CESIZen — Pilotage », colonnes : À qualifier, Qualifié, En cours, En revue, En recette, Livré |

---

## 1. Mode démonstration des déploiements

Les travaux qui écrivent sur une infrastructure réelle sont conditionnés à la
variable de dépôt **`DEPLOY_ENABLED`**. Tant qu'elle n'est pas définie :

- les travaux `build` et `deploy` sont **ignorés** (aucune exécution en échec) ;
- un travail `simulation` s'exécute à leur place et **réussit**.

Ce travail de démonstration n'est pas décoratif : il vérifie réellement que la
composition de production est valide, que le réseau interne reste cloisonné,
qu'aucun port PostgreSQL n'est publié et que le durcissement du conteneur
applicatif est intact. Il affiche ensuite la séquence de déploiement qui serait
exécutée, dans l'ordre, avec les commandes correspondantes.

### Bascule en déploiement réel

Aucune modification de code n'est nécessaire :

```bash
gh variable set DEPLOY_ENABLED --body true
gh secret  set STAGING_HOST    --body "recette.cesizen.fr"
gh secret  set STAGING_SSH_KEY < ~/.ssh/cesizen_deploy
```

À partir de là, `build` et `deploy` prennent le relais et `simulation` cesse de
s'exécuter.

---

## 2. Déroulé conseillé de la démonstration (environ 6 minutes)

| # | Écran | Ce que cela prouve | Critère de la grille |
|---|---|---|---|
| 1 | Onglet **Actions** — exécution de la *pull request*, les 4 travaux détaillés | La chaîne d'intégration existe et bloque la fusion | Outil de versioning configuré (2 pts) |
| 2 | Détail du travail **Tests** — rapport `pytest` et couverture | Tests unitaires et de non-régression automatisés | Automatisation (plan de déploiement) |
| 3 | Détail du travail **Sécurité** — `bandit`, `pip-audit`, `check --deploy`, Trivy | Le contrôle de sécurité est bloquant, pas déclaratif | Bonnes pratiques (1 pt) |
| 4 | Onglet **Security** — alertes Dependabot, résultats Trivy remontés en SARIF | Les vulnérabilités sont centralisées et suivies | Plan de sécurisation (8 pts) |
| 5 | **Branches** — règles de protection sur `main` | Aucune fusion directe possible | Versioning |
| 6 | Exécution **Déploiement Recette** — travail `simulation` vert, avec son résumé | La séquence de déploiement est configurée et vérifiée | Environnements de déploiement (2 pts) |
| 7 | Exécution **Déploiement Production** — travail `controle` puis étape d'approbation | Séparation entre développer et autoriser la livraison | Plan de déploiement (6 pts) |
| 8 | **Nouveau ticket** — formulaire d'anomalie avec le tableau des SLA | Le délai contractuel est porté par l'outil | Outil de gestion des évolutions (6 pts) |
| 9 | Formulaire **incident de sécurité** — liste de contrôle CNIL 72 h | La gestion de crise est outillée | Plan de sécurisation |
| 10 | **Projects** — tableau de pilotage, filtres par sévérité et module | Pilotage du portefeuille | Maintenance |
| 11 | Ticket **[VEILLE]** créé automatiquement le lundi | La veille produit des actions, pas des rapports | Veille et méthodologie (3 pts) |
| 12 | *Pull request* **Dependabot** validée par la CI | Montées de version maîtrisées | Garanties d'évolutivité |

Pour l'écran 11, la veille hebdomadaire peut être déclenchée à la demande :

```bash
gh workflow run "Veille sécurité hebdomadaire"
```

---

## 3. Questions probables du jury

**« Votre environnement de production tourne-t-il réellement ? »**
Non. La chaîne est configurée et vérifiée de bout en bout ; le provisionnement
d'un serveur est une décision d'exploitation, distincte de la configuration du
déploiement. La bascule tient à une variable de dépôt et deux secrets, sans
modification du code ni des procédures — c'est précisément l'intérêt d'avoir
décrit l'infrastructure dans le dépôt plutôt que de l'avoir configurée à la main.

**« Pourquoi pas Kubernetes ? »**
Charge attendue au démarrage sans commune mesure avec le coût d'exploitation, et
un prestataire unique. Les images produites sont identiques : le passage à
l'échelle ne demande pas de réécriture.

**« Comment revenez-vous en arrière ? »**
Quatre mécanismes : images immuables étiquetées par version, sauvegarde
automatique avant chaque migration, vérification de disponibilité après bascule,
et retour arrière automatique avec ouverture d'un ticket d'incident en cas
d'échec.

**« Que se passe-t-il en cas de fuite de données ? »**
Escalade N3 : cellule de crise sous 2 h, notification CNIL sous 72 h à compter de
la détection, information des personnes si le risque est élevé. Le formulaire
d'incident porte la liste de contrôle correspondante.
