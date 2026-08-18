#!/usr/bin/env python3
"""
CESIZen — Contrôles d'invariants de l'infrastructure.

Ces vérifications ne dépendent d'aucun serveur : elles s'assurent que les
fichiers de déploiement respectent les décisions de sécurité documentées dans
le plan de sécurisation. Une régression sur l'un de ces points passerait
autrement inaperçue jusqu'à la mise en production.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML requis : pip install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[2]
echecs: list[str] = []
succes: list[str] = []


def verifier(condition: bool, libelle: str, detail: str = "") -> None:
    if condition:
        succes.append(libelle)
    else:
        echecs.append(f"{libelle}{' — ' + detail if detail else ''}")


def lire(chemin: str) -> str:
    return (ROOT / chemin).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# 1. Tous les fichiers YAML doivent être analysables
# --------------------------------------------------------------------------
for f in sorted(list(ROOT.glob(".github/**/*.yml")) + list(ROOT.glob("deploy/**/*.yml"))):
    rel = f.relative_to(ROOT)
    try:
        yaml.safe_load(f.read_text(encoding="utf-8"))
        succes.append(f"YAML analysable : {rel}")
    except yaml.YAMLError as exc:
        echecs.append(f"YAML invalide : {rel} — {exc}")

# --------------------------------------------------------------------------
# 2. Formulaires de tickets : structure attendue par GitHub
# --------------------------------------------------------------------------
for f in sorted((ROOT / ".github/ISSUE_TEMPLATE").glob("*.yml")):
    if f.name == "config.yml":
        continue
    data = yaml.safe_load(f.read_text(encoding="utf-8"))
    verifier(
        isinstance(data, dict) and {"name", "description", "body"} <= set(data),
        f"Formulaire complet : {f.name}",
        "clés name/description/body attendues",
    )

# --------------------------------------------------------------------------
# 3. Invariants de la composition de production
# --------------------------------------------------------------------------
prod = lire("deploy/docker-compose.prod.yml")

verifier(
    re.search(r"^  internal:\n(?:.*\n)?.*internal: true", prod, re.M) is not None,
    "Réseau interne cloisonné (aucune route vers Internet)",
)
verifier(
    re.search(r'^\s+- "?\d+:5432', prod, re.M) is None,
    "Aucun port PostgreSQL publié sur l'hôte",
)
verifier(
    re.search(r'^\s+- "?\d+:6379', prod, re.M) is None,
    "Aucun port Redis publié sur l'hôte",
)
for regle in ("read_only: true", "no-new-privileges:true", "cap_drop"):
    verifier(regle in prod, f"Durcissement du conteneur applicatif : {regle}")
verifier(
    "/var/run/docker.sock:/var/run/docker.sock:ro" in prod,
    "Socket Docker monté en lecture seule",
)
verifier(
    "entrypoints.web.http.redirections.entrypoint.to=websecure" in prod,
    "Redirection HTTP vers HTTPS active",
)

# --------------------------------------------------------------------------
# 4. Invariants de l'image applicative
# --------------------------------------------------------------------------
dockerfile = lire("deploy/Dockerfile")
verifier(re.search(r"^USER \w+", dockerfile, re.M) is not None,
         "L'image ne s'exécute pas en root")
verifier("HEALTHCHECK" in dockerfile,
         "L'image déclare un contrôle de santé")

# --------------------------------------------------------------------------
# 5. En-têtes de sécurité HTTP
# --------------------------------------------------------------------------
middlewares = yaml.safe_load(lire("deploy/traefik/dynamic/middlewares.yml"))
entetes = middlewares["http"]["middlewares"]["secure-headers"]["headers"]
for cle in ("stsSeconds", "frameDeny", "contentTypeNosniff", "referrerPolicy"):
    verifier(cle in entetes, f"En-tête de sécurité déclaré : {cle}")

# --------------------------------------------------------------------------
# 6. Aucun secret en clair dans les fichiers versionnés
# --------------------------------------------------------------------------
MOTIFS = [
    (r"ghp_[A-Za-z0-9]{20,}", "jeton GitHub"),
    (r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----", "clé privée"),
    (r"AKIA[0-9A-Z]{16}", "clé AWS"),
]
suspects = []
for f in list(ROOT.glob("deploy/**/*")) + list(ROOT.glob(".github/**/*")):
    if not f.is_file() or f.suffix in {".png", ".jpg", ".pdf"}:
        continue
    contenu = f.read_text(encoding="utf-8", errors="ignore")
    for motif, libelle in MOTIFS:
        if re.search(motif, contenu):
            suspects.append(f"{f.relative_to(ROOT)} ({libelle})")
verifier(not suspects, "Aucun secret en clair dans les fichiers versionnés",
         ", ".join(suspects))

# --------------------------------------------------------------------------
# Restitution
# --------------------------------------------------------------------------
print(f"\n{len(succes)} contrôles réussis")
for s in succes:
    print(f"  OK   {s}")

if echecs:
    print(f"\n{len(echecs)} contrôles en échec")
    for e in echecs:
        print(f"  ÉCHEC {e}")

resume = Path(__import__("os").environ.get("GITHUB_STEP_SUMMARY", "/dev/null"))
try:
    with resume.open("a", encoding="utf-8") as fh:
        fh.write("### Invariants d'infrastructure\n\n")
        fh.write(f"- {len(succes)} contrôles réussis\n")
        fh.write(f"- {len(echecs)} contrôles en échec\n")
except OSError:
    pass

sys.exit(1 if echecs else 0)
