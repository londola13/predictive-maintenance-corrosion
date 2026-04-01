#!/bin/bash
# activate_fusion.sh
# ------------------
# Bascule le pipeline en MODE FUSION (données réelles COTCO).
# À lancer après avoir exporté les données depuis le PI Server.
#
# Usage :
#   bash stage_kit/activate_fusion.sh                    (données dans les paths par défaut)
#   bash stage_kit/activate_fusion.sh mon_export_pi.csv  (spécifier le fichier PI)
#
# Prérequis :
#   - Python venv activé : source venv/bin/activate (Linux/Mac) ou venv\Scripts\activate (Windows)
#   - Fichiers dans data/enterprise/ :
#       pi_export.csv        (export PI Server — toutes les heures, min. 6 mois)
#       ut_reports/          (dossier avec les PDFs de rapports UT)
#       labo_analyses.xlsx   (analyses labo mensuelles)

set -e  # Arrêter si erreur

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$ROOT/venv/Scripts/python.exe"

# Sur Linux/Mac utiliser python3
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="$ROOT/venv/bin/python"
fi

if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python"
    echo "[WARN] venv non trouvé — utilisation du python système"
fi

cd "$ROOT"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ACTIVATION MODE FUSION — COTCO KRIBI"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── Étape 1 : Valider les tags PI ────────────────────────────────────────────
PI_FILE="${1:-data/enterprise/pi_export.csv}"

if [ -f "$PI_FILE" ]; then
    echo "Étape 1/4 — Validation tags PI Server..."
    "$VENV_PYTHON" stage_kit/validate_tags.py "$PI_FILE"
    echo ""
    read -p "Les tags sont-ils corrects ? Continuer ? [o/N] " confirm
    if [ "$confirm" != "o" ] && [ "$confirm" != "O" ]; then
        echo "Annulé. Corriger le mapping dans src/parsers/parse_pi_csv.py puis relancer."
        exit 0
    fi
else
    echo "⚠️  Fichier PI non trouvé : $PI_FILE"
    echo "   Placer l'export PI sous data/enterprise/pi_export.csv"
    echo "   Ou spécifier le chemin : bash stage_kit/activate_fusion.sh mon_export.csv"
    echo ""
    echo "   Format attendu → voir : stage_kit/pi_export_template.csv"
    exit 1
fi

echo ""

# ── Étape 2 : Parser PHMSA si pas encore fait ─────────────────────────────────
if [ ! -f "data/raw/phmsa_survival.csv" ]; then
    echo "Étape 2/4 — Génération données PHMSA sample (validation externe)..."
    "$VENV_PYTHON" src/parsers/parse_phmsa.py --sample
else
    echo "Étape 2/4 — Données PHMSA OK ($(wc -l < data/raw/phmsa_survival.csv) lignes)"
fi

echo ""

# ── Étape 3 : Lancer le pipeline fusion ──────────────────────────────────────
echo "Étape 3/4 — Entraînement pipeline FUSION (données réelles COTCO)..."
echo "  XGBoost + WeibullAFT (avec PHMSA) + Isolation Forest"
echo "  Durée estimée : 5-15 minutes selon le volume de données"
echo ""

"$VENV_PYTHON" src/run_pipeline.py --mode fusion --retrain

echo ""

# ── Étape 4 : Lancer le dashboard ────────────────────────────────────────────
echo "Étape 4/4 — Pipeline terminé ✅"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Lancer le dashboard :"
echo "  $VENV_PYTHON -m streamlit run dashboard/app.py"
echo ""
echo "  Validation externe PHMSA :"
echo "  $VENV_PYTHON notebooks/05_phmsa_validation.py"
echo "═══════════════════════════════════════════════════════"
