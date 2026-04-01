"""
validate_tags.py
----------------
Script de validation du mapping PI Server → colonnes du projet.
À lancer DÈS LE PREMIER EXPORT depuis le PI Server COTCO.

PROBLÈME QU'IL RÉSOUT :
  Le parser parse_pi_csv.py attend des noms de tags précis (TI-1001, PI-2001...).
  Si COTCO utilise des variantes (TI1001, T_INLET, TI_1001...), toutes les
  colonnes seront NaN silencieusement — le pipeline tourne mais prédit n'importe quoi.

  Ce script détecte ce problème en 30 secondes et propose les corrections.

UTILISATION :
  1. Exporter 50-100 lignes depuis PI Server (quelques heures de données)
  2. Sauvegarder sous data/raw/test_pi_export.csv
  3. Lancer : python stage_kit/validate_tags.py data/raw/test_pi_export.csv
  4. Suivre les instructions à l'écran

SORTIE :
  - Colonnes reconnues : ✅ (seront utilisées par le parser)
  - Colonnes manquantes : ❌ (à mapper manuellement dans config)
  - Colonnes inconnues  : ⚠️  (dans le CSV mais pas dans nos tags — probablement des tags supplémentaires)
  - Suggestions de mapping par similarité textuelle (fuzzy match)
"""

import sys
import csv
from pathlib import Path
from difflib import SequenceMatcher

# Forcer UTF-8 sur Windows (terminal cp1252 par défaut)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ajouter le root au path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.parsers.parse_pi_csv import COTCO_TAG_MAPPING, COLONNES_DCS


def valider_export_pi(chemin_csv: str, afficher_sample: bool = True) -> dict:
    """
    Valide un export PI Server CSV et affiche un rapport complet.

    Args:
        chemin_csv     : chemin vers le fichier CSV PI Server
        afficher_sample : afficher les 3 premières lignes pour inspection visuelle

    Returns:
        dict avec les clés : reconnues, manquantes, inconnues, suggestions
    """
    chemin = Path(chemin_csv)
    if not chemin.exists():
        print(f"❌ Fichier introuvable : {chemin_csv}")
        print(f"   Vérifier le chemin et relancer.")
        sys.exit(1)

    print(f"\n{'═'*60}")
    print(f"  VALIDATION EXPORT PI SERVER — COTCO KRIBI")
    print(f"{'═'*60}")
    print(f"  Fichier : {chemin.name}")
    print(f"  Taille  : {chemin.stat().st_size / 1024:.1f} Ko\n")

    # ── Lire les colonnes du CSV ───────────────────────────────────────────────
    try:
        with open(chemin, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            colonnes_csv = next(reader)
            premieres_lignes = [next(reader, None) for _ in range(3)]
    except Exception as e:
        print(f"❌ Erreur lecture CSV : {e}")
        sys.exit(1)

    # Normaliser : supprimer espaces, mettre en majuscules pour comparaison
    colonnes_csv_clean = [c.strip() for c in colonnes_csv]
    colonnes_csv_norm  = {c.upper().strip(): c for c in colonnes_csv_clean}

    # ── Afficher sample ───────────────────────────────────────────────────────
    if afficher_sample:
        print("  ─── APERÇU DU FICHIER (3 premières lignes) ───")
        print(f"  Colonnes ({len(colonnes_csv_clean)}) :")
        for i, col in enumerate(colonnes_csv_clean):
            print(f"    [{i:2d}] {col}")
        if premieres_lignes[0]:
            print(f"\n  Ligne 1 : {premieres_lignes[0][:8]} ...")
        print()

    # ── Vérification des tags attendus ────────────────────────────────────────
    tags_attendus = list(COTCO_TAG_MAPPING.keys())  # TI-1001, PI-2001, etc.

    reconnues  = []
    manquantes = []

    for tag in tags_attendus:
        if tag in colonnes_csv_clean or tag.upper() in colonnes_csv_norm:
            reconnues.append(tag)
        else:
            manquantes.append(tag)

    # Colonnes inconnues (dans le CSV mais pas dans les tags attendus)
    inconnues = [c for c in colonnes_csv_clean
                 if c not in tags_attendus
                 and c.upper() not in {t.upper() for t in tags_attendus}
                 and c.lower() not in ("timestamp", "datetime", "date", "time", "quality")]

    # ── Suggestions fuzzy pour les tags manquants ─────────────────────────────
    suggestions = {}
    for tag_manquant in manquantes:
        best_match, best_score = None, 0.0
        for col in colonnes_csv_clean:
            score = SequenceMatcher(None,
                                    tag_manquant.upper().replace("-", ""),
                                    col.upper().replace("-", "").replace("_", "")).ratio()
            if score > best_score:
                best_score = score
                best_match = col
        if best_score > 0.65:
            suggestions[tag_manquant] = (best_match, best_score)

    # ── RAPPORT ────────────────────────────────────────────────────────────────
    print(f"  {'─'*58}")
    print(f"  RÉSUMÉ VALIDATION")
    print(f"  {'─'*58}")
    print(f"  Tags attendus        : {len(tags_attendus)}")
    print(f"  ✅ Reconnus          : {len(reconnues)}")
    print(f"  ❌ Manquants         : {len(manquantes)}")
    print(f"  ⚠️  Inconnus (bonus) : {len(inconnues)}")

    if reconnues:
        print(f"\n  ✅ TAGS RECONNUS ({len(reconnues)}/{len(tags_attendus)}) :")
        for tag in reconnues:
            col_std = COTCO_TAG_MAPPING[tag]
            print(f"     {tag:<15} → {col_std}")

    if manquantes:
        print(f"\n  ❌ TAGS MANQUANTS ({len(manquantes)}) — Action requise :")
        for tag in manquantes:
            col_std = COTCO_TAG_MAPPING[tag]
            if tag in suggestions:
                col_suggérée, score = suggestions[tag]
                print(f"     {tag:<15} [{col_std}]")
                print(f"       → Suggestion : '{col_suggérée}' (similarité {score*100:.0f}%)")
            else:
                print(f"     {tag:<15} [{col_std}]  — aucune colonne similaire trouvée")

    if inconnues:
        print(f"\n  ⚠️  COLONNES INCONNUES dans le CSV (peut inclure tags utiles non cartographiés) :")
        for col in inconnues[:15]:  # Limiter à 15
            print(f"     {col}")
        if len(inconnues) > 15:
            print(f"     ... ({len(inconnues) - 15} de plus)")

    # ── Diagnostic global ─────────────────────────────────────────────────────
    pct_ok = len(reconnues) / len(tags_attendus) * 100
    print(f"\n  {'─'*58}")
    print(f"  DIAGNOSTIC GLOBAL : {pct_ok:.0f}% des tags reconnus")

    if pct_ok == 100:
        print(f"\n  ✅ PARFAIT — Export PI compatible. Lancer directement :")
        print(f"     python src/run_pipeline.py --mode fusion")

    elif pct_ok >= 70:
        print(f"\n  ⚠️  PARTIEL — {len(manquantes)} tags manquants.")
        print(f"  Solutions :")
        _afficher_instructions_mapping(suggestions, manquantes)

    else:
        print(f"\n  ❌ INCOMPATIBLE — Seulement {pct_ok:.0f}% des tags trouvés.")
        print(f"  Le nommage PI COTCO est très différent des tags attendus.")
        print(f"\n  Action : contacter l'ingénieur PI Server COTCO et demander :")
        print(f"  'Quels sont les noms exacts des tags TI-1001 à CI-5004 dans votre PI ?'")
        print(f"  Puis éditer : config/cotco_kribi_config.yaml section [tags_dcs]")

    print(f"\n  {'═'*58}")

    return {
        "reconnues":    reconnues,
        "manquantes":   manquantes,
        "inconnues":    inconnues,
        "suggestions":  suggestions,
        "pct_ok":       pct_ok,
    }


def _afficher_instructions_mapping(suggestions: dict, manquantes: list) -> None:
    """Affiche les instructions pour corriger le mapping manuellement."""
    print(f"\n  Option A — Modifier le fichier config :")
    print(f"     Éditer : config/cotco_kribi_config.yaml")
    print(f"     Section tags_dcs, remplacer les noms qui ne matchent pas")
    print(f"\n  Option B — Mapper directement dans parse_pi_csv.py :")
    print(f"     Éditer : src/parsers/parse_pi_csv.py → COTCO_TAG_MAPPING")
    print(f"\n  Exemple de mapping à ajouter si PI utilise 'TI1001' au lieu de 'TI-1001' :")
    print(f"     COTCO_TAG_MAPPING = {{")
    print(f"         'TI1001': 'T_mean',    # au lieu de 'TI-1001'")
    print(f"         'PI2001': 'P_mean',    # au lieu de 'PI-2001'")
    print(f"         ...                    # continuer pour tous les tags")
    print(f"     }}")


def generer_template_csv(sortie: str = "stage_kit/pi_export_template.csv") -> None:
    """
    Génère un fichier CSV template montrant le format attendu exactement.
    À montrer à l'ingénieur PI pour qu'il configure l'export correctement.
    """
    import csv
    from datetime import datetime, timedelta

    chemin = Path(sortie)
    chemin.parent.mkdir(parents=True, exist_ok=True)

    tags = list(COTCO_TAG_MAPPING.keys())
    headers = ["Timestamp"] + tags

    # 5 lignes d'exemple avec valeurs réalistes
    base_time = datetime(2026, 4, 1, 8, 0, 0)
    lignes_exemple = [
        [
            (base_time + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S"),
            # TI-1001, TI-1002, TI-1003, TI-1004
            f"{50.0 + i*0.1:.1f}", f"{25.0 - i*0.05:.1f}", f"{48.0:.1f}", f"{30.0:.1f}",
            # PI-2001, PI-2002, PI-2003, PI-2004, PI-2005
            f"{82.5:.1f}", f"{11.2:.1f}", f"{2.1:.1f}", f"{108.0:.1f}", f"{82.5:.1f}",
            # FI-3001, FI-3002, FI-3003
            f"{520.0:.0f}", f"{450.0:.0f}", f"{22.0:.0f}",
            # AI-4001, AI-4002, AI-4003, AI-4004
            f"{2.8:.2f}", f"{125.0:.0f}", f"{12.5:.1f}", f"{45.0:.0f}",
            # CI-5001, CI-5002, CI-5003, CI-5004
            f"{0.045:.4f}", f"{0.038:.4f}", f"{38.0:.0f}", f"{-920:.0f}",
        ]
        for i in range(5)
    ]

    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(lignes_exemple)

    print(f"\n[Template] Fichier généré : {chemin}")
    print(f"  Colonnes attendues : {len(tags)} tags + Timestamp")
    print(f"  À montrer à l'ingénieur PI pour configurer l'export.")
    print(f"\n  Note : les noms de colonnes DOIVENT correspondre exactement")
    print(f"  (ex: 'TI-1001' pas 'TI1001' ni 'T_INLET_1')")
    print(f"  Si les noms different -> utiliser validate_tags.py pour diagnostiquer")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--template":
        # Générer le template si pas d'argument
        print("Usage : python stage_kit/validate_tags.py <chemin_export_pi.csv>")
        print("        python stage_kit/validate_tags.py --template  (générer le template)")
        print()
        generer_template_csv()
    else:
        chemin = sys.argv[1]
        valider_export_pi(chemin)
