# -*- coding: utf-8 -*-
"""
Service de prédiction temps réel — sonde ER corrosion.

Tourne en tâche de fond (même dashboard fermé). À chaque tick :
  1. détecte le run actif (cr_runs.status = 'active') ;
  2. recalcule les features via le pipeline (traiter_run) sur les mesures live ;
  3. prédit le CR avec le modèle ML (xgb_cr) et lit le RUL par extrapolation
     physique du pipeline (RUL_h) — le modèle xgb_rul est écarté (instable) ;
  4. enregistre la prédiction (cr_predictions), déclenche une alerte si le niveau
     change (cr_alerts), et crée un ordre de travail au franchissement de seuil
     (CMMS maison, cr_work_orders).

Seuils LABO (fil de fer en HCl) : sur la SECTION PERDUE (%) et le RUL (h) —
le CR du labo (~centaines) n'est pas comparable aux seuils NACE en mm/an.

Usage :
  export SUPABASE_KEY=...           # service_role (jamais en dur)
  python src/realtime/predict_loop.py            # boucle continue (45 s)
  python src/realtime/predict_loop.py --once     # une seule itération (test)
  python src/realtime/predict_loop.py --interval 30
"""
import argparse
import os
import pickle
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

for _flux in (sys.stdout, sys.stderr):          # console Windows -> UTF-8 (≈, …, —)
    try:
        _flux.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.etl.fetch_supabase import fetch_run, fetch_all_runs       # noqa: E402
from pipeline.corrosion_pipeline import traiter_run                # noqa: E402
from src.etl.save_predictions import save_prediction               # noqa: E402
from src.etl.trigger_alerts import insert_alert                    # noqa: E402
from src.cmms.work_orders import create_work_order                 # noqa: E402

MODELE_CR = os.path.join(ROOT, "models", "xgb_cr.pkl")

# Seuils labo — réglables (« seuil souhaité » du fil)
SECTION_ROUGE, SECTION_ORANGE = 85.0, 60.0   # % de section perdue
RUL_ROUGE, RUL_ORANGE = 2.0, 5.0             # heures avant rupture
# Garde-fou RUL : le RUL physique = (r - r_crit)/|dr/dt| n'est fiable qu'une fois la
# corrosion avancée. Tôt dans le run, dr/dt (phase de stabilisation/induction) est
# instable -> RUL aberrant -> fausse alerte. Sous ce seuil de section, l'alerte suit
# la SECTION seule. C'est un garde-fou contre l'estimateur, pas un seuil de corrosion.
RUL_GATE_SECTION = 40.0
_LIBELLE = {"rouge": "INTERVENTION URGENTE", "orange": "Planifier inspection", "vert": "Nominal"}


def couper_plateau(raw: pd.DataFrame) -> pd.DataFrame:
    """rx>0 + cadrage emballement (rx>100) + troncature du plateau de saturation."""
    rx = pd.to_numeric(raw["rx_ohm"], errors="coerce")
    raw = raw[rx > 0].reset_index(drop=True)
    rx = pd.to_numeric(raw["rx_ohm"], errors="coerce").reset_index(drop=True)
    emb = rx > 100.0
    if emb.any():
        raw = raw.iloc[: int(emb.idxmax())].reset_index(drop=True)
        rx = pd.to_numeric(raw["rx_ohm"], errors="coerce").reset_index(drop=True)
    if len(raw) < 30:
        return raw
    mx = float(rx.max())
    for i in range(len(rx)):
        if rx.iloc[i] >= 0.99 * mx and rx.iloc[i:i + 10].median() >= 0.95 * mx:
            return raw.iloc[: i + 1].reset_index(drop=True)
    return raw


def niveau_de(section: float, rul) -> str:
    # le RUL ne peut escalader que si la corrosion est déjà avancée (garde-fou début de run)
    rul_ok = rul is not None and section >= RUL_GATE_SECTION
    if section >= SECTION_ROUGE or (rul_ok and rul <= RUL_ROUGE):
        return "rouge"
    if section >= SECTION_ORANGE or (rul_ok and rul <= RUL_ORANGE):
        return "orange"
    return "vert"


def run_actif():
    runs = fetch_all_runs()
    act = runs[runs["status"] == "active"]
    return act.iloc[0]["run_id"] if len(act) else None


def predire(run_id: str, model, feats):
    raw = couper_plateau(fetch_run(run_id))
    if len(raw) < 15:
        return None
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False)
    tmp.close()
    d = traiter_run(tmp.name)
    try:
        os.unlink(tmp.name)
    except OSError:
        pass
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=feats)
    if d.empty:
        return None
    last = d.iloc[[-1]]
    cr = float(model.predict(last[feats])[0])
    rul = None
    if "RUL_h" in d.columns and pd.notna(last["RUL_h"].iloc[0]):
        rul = float(last["RUL_h"].iloc[0])
        if rul < 0:
            rul = 0.0
    section = float(last["section_perdue_pct"].iloc[0])
    return cr, rul, section


def iteration(model, feats, etat: dict):
    rid = run_actif()
    if not rid:
        print("… aucun run actif")
        return
    res = predire(rid, model, feats)
    if not res:
        print(f"… run {rid[:8]} : pas encore assez de points exploitables")
        return
    cr, rul, section = res
    rul_val = rul if rul is not None else 0.0
    save_prediction(rid, cr, rul_val, model_version="xgb_cr_live")
    niveau = niveau_de(section, rul)
    msg = f"section={section:.0f}% · RUL≈{rul_val:.1f}h · CR(ML)={cr:.1f} — {_LIBELLE[niveau]}"
    if etat.get(rid) != niveau:        # dédupe alerte : seulement au changement de niveau
        insert_alert(rid, niveau, msg)
        etat[rid] = niveau
    wo = create_work_order(rid, niveau, cr, rul_val, section)
    flag = f"  → OT créé {str(wo)[:8]}" if wo else ""
    print(f"[{rid[:8]}] CR={cr:7.1f}  RUL≈{rul_val:6.1f}h  section={section:3.0f}%  [{niveau.upper()}]{flag}")


def main():
    ap = argparse.ArgumentParser(description="Service de prédiction temps réel corrosion")
    ap.add_argument("--interval", type=int, default=45, help="secondes entre deux ticks")
    ap.add_argument("--once", action="store_true", help="une seule itération (test)")
    args = ap.parse_args()

    if not os.environ.get("SUPABASE_KEY"):
        print("ERREUR: SUPABASE_KEY non défini", file=sys.stderr)
        sys.exit(1)

    model = pickle.load(open(MODELE_CR, "rb"))
    feats = list(model.feature_names_in_)
    print(f"Service de prédiction démarré — modèle xgb_cr ({len(feats)} features), "
          f"intervalle {args.interval}s, RUL = pipeline.")
    etat: dict = {}
    while True:
        try:
            iteration(model, feats, etat)
        except Exception as e:
            print(f"[err] {e}", file=sys.stderr)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
