-- ---------------------------------------------------------------------------
-- CESIZen - Initialisation PostgreSQL (exécutée une seule fois, au 1er démarrage)
-- ---------------------------------------------------------------------------

-- pgcrypto : chiffrement au niveau colonne pour les données de santé
-- (commentaires libres du tracker d'émotions).
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Suivi des requêtes lentes, utilisé pour la maintenance corrective
-- (détection des régressions de performance sur l'API).
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Rôle en lecture seule dédié aux exports statistiques anonymisés :
-- respecte le principe de moindre privilège (le compte applicatif
-- n'est pas réutilisé pour la BI).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cesizen_readonly') THEN
        CREATE ROLE cesizen_readonly WITH LOGIN PASSWORD 'change_me_via_vault';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE cesizen TO cesizen_readonly;
GRANT USAGE ON SCHEMA public TO cesizen_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO cesizen_readonly;
