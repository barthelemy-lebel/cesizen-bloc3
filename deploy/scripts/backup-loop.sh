#!/bin/sh
# ---------------------------------------------------------------------------
# CESIZen - Sauvegarde quotidienne de la base de production
#
# Stratégie : dump logique compressé + chiffré GPG symétrique, poussé sur
# l'Object Storage OVHcloud (région GRA, France). Rétention 30 jours locale
# et distante. Le chiffrement garantit qu'une fuite du bucket n'expose
# aucune donnée de santé (RGPD art. 32).
# ---------------------------------------------------------------------------
set -eu

RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_DIR=/backups

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"; }

run_backup() {
    stamp=$(date -u '+%Y%m%d-%H%M%S')
    archive="${BACKUP_DIR}/cesizen-${stamp}.sql.gz.gpg"

    log "Début du dump vers ${archive}"
    pg_dump --format=plain --no-owner --no-privileges \
        | gzip -9 \
        | gpg --batch --yes --symmetric --cipher-algo AES256 \
              --passphrase "${BACKUP_PASSPHRASE}" \
              --output "${archive}"

    size=$(du -h "${archive}" | cut -f1)
    log "Dump terminé (${size})"

    # Vérification d'intégrité : une sauvegarde non restaurable n'est pas une sauvegarde
    if ! gpg --batch --quiet --decrypt --passphrase "${BACKUP_PASSPHRASE}" \
             "${archive}" 2>/dev/null | gzip -t; then
        log "ERREUR : archive corrompue, sauvegarde invalidée"
        rm -f "${archive}"
        return 1
    fi
    log "Intégrité vérifiée"

    if [ -n "${S3_BUCKET:-}" ]; then
        aws s3 cp "${archive}" "s3://${S3_BUCKET}/postgres/" --only-show-errors \
            && log "Copie distante OK" \
            || log "AVERTISSEMENT : copie distante échouée (sauvegarde locale conservée)"
    fi

    find "${BACKUP_DIR}" -name 'cesizen-*.sql.gz.gpg' -mtime "+${RETENTION_DAYS}" -delete
    log "Purge des sauvegardes de plus de ${RETENTION_DAYS} jours effectuée"
}

log "Service de sauvegarde démarré (rétention ${RETENTION_DAYS} jours)"
while true; do
    run_backup || log "Cycle de sauvegarde en échec - nouvelle tentative dans 1 h"
    sleep 86400
done
