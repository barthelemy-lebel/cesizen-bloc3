#!/bin/sh
# ---------------------------------------------------------------------------
# CESIZen - Restauration d'une sauvegarde (procédure de reprise d'activité)
#
# Usage : ./restore.sh /backups/cesizen-20260318-030000.sql.gz.gpg
#
# À exécuter au minimum une fois par trimestre sur l'environnement de test :
# une procédure de restauration jamais testée est une procédure inexistante.
# ---------------------------------------------------------------------------
set -eu

archive="${1:?Usage: restore.sh <archive.sql.gz.gpg>}"

[ -f "${archive}" ] || { echo "Archive introuvable : ${archive}"; exit 1; }

echo "ATTENTION : la base ${PGDATABASE} va être écrasée par ${archive}."
printf 'Confirmer en tapant RESTORE : '
read -r confirm
[ "${confirm}" = "RESTORE" ] || { echo "Restauration annulée."; exit 1; }

echo "Restauration en cours..."
gpg --batch --quiet --decrypt --passphrase "${BACKUP_PASSPHRASE}" "${archive}" \
    | gunzip \
    | psql --set ON_ERROR_STOP=on

echo "Restauration terminée. Vérifier l'application avant réouverture du service."
