# CESIZen — Infrastructure et déploiement

Ce dossier contient tout ce qui est nécessaire pour construire, déployer et
exploiter l'application CESIZen. Il est le pendant technique du *Plan de
déploiement* remis au Ministère.

## Contenu

| Fichier | Rôle |
|---|---|
| `Dockerfile` | Image de l'API Django, build multi-stage, exécution sans privilèges |
| `docker-compose.yml` | Environnement de développement local (Postgres, API, Mailhog) |
| `docker-compose.prod.yml` | Environnements de recette et de production (Traefik, Postgres, Redis, sauvegardes) |
| `.env.example` | Modèle de configuration ; le `.env` réel n'est jamais versionné |
| `traefik/dynamic/` | En-têtes de sécurité HTTP et limitation de débit |
| `postgres/init/` | Extensions et rôle en lecture seule créés à l'initialisation |
| `scripts/` | Sauvegarde chiffrée quotidienne et procédure de restauration |

## Développement local

```bash
cp .env.example .env          # les valeurs de dev suffisent
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py loaddata fixtures/emotions.json
docker compose exec backend python manage.py createsuperuser
```

L'API répond sur <http://localhost:8000>, les emails sont capturés sur
<http://localhost:8025>.

## Installation d'un serveur (recette ou production)

```bash
# 1. Durcissement du système (une seule fois)
adduser --disabled-password deploy
usermod -aG docker deploy
# SSH par clé uniquement, root interdit
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/'               /etc/ssh/sshd_config
systemctl restart ssh

# 2. Pare-feu : seuls 22, 80 et 443 sont ouverts
ufw default deny incoming && ufw allow 22,80,443/tcp && ufw enable

# 3. Protection contre le bourrage d'identifiants SSH
apt install -y fail2ban && systemctl enable --now fail2ban

# 4. Correctifs de sécurité système appliqués automatiquement
apt install -y unattended-upgrades && dpkg-reconfigure -plow unattended-upgrades

# 5. Déploiement applicatif
mkdir -p /srv/cesizen /srv/backups && cd /srv/cesizen
git clone https://github.com/barthelemy-lebel/cesizen.git .
cp deploy/.env.example .env && chmod 600 .env    # puis renseigner les secrets
docker compose -f deploy/docker-compose.prod.yml --env-file .env up -d
docker compose -f deploy/docker-compose.prod.yml --env-file .env \
  run --rm backend python manage.py migrate --noinput
```

Les déploiements suivants sont entièrement automatisés par GitHub Actions ;
cette procédure manuelle ne sert qu'à l'installation initiale et à la
reconstruction d'un serveur.

## Restauration après incident

```bash
docker compose -f docker-compose.prod.yml exec backup \
  /scripts/restore.sh /backups/cesizen-20260318-030000.sql.gz.gpg
```

La procédure est testée chaque trimestre sur l'environnement de recette et le
résultat est consigné dans un ticket `veille`.
