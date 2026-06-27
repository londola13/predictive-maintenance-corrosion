# -*- coding: utf-8 -*-
"""Comparatif des 3 estimateurs de DURÉE DE VIE (temps de rupture) pour un run.

Trois outils, trois natures différentes — tous ramenés sur l'axe « durée de vie totale (h) » :
  1. Extrapolation physique : durée = écoulé + RUL_pipeline (RUL = (r−r_crit)/|dr/dt| mesuré).
  2. XGBoost (dérivé)        : même extrapolation mais avec le CR PRÉDIT par XGBoost au lieu du
                              CR mesuré → RUL_xgb = RUL_phys × (CR_mesuré / CR_xgb). Sans unité.
  3. Jumeau / simulateur     : bande prédictive [P10–P90] du temps de rupture, NON-paramétrique,
                              par mélange Dirichlet des durées des donneurs réels (Run1/12/16).
                              Robuste dès le départ (ne dépend pas de la pente instantanée).

Le simulateur est le seul à donner une PRÉDICTION a priori du temps de rupture ; les deux autres
sont des extrapolations de la vitesse, bruitées tôt dans le run. La bande couvre les 2 morphologies
(graduelle / induction-sprint) — cf. perspective mémoire §III.6.5 (validée sur Run #21 : 13,1 h ∈ [13–20,5]).
"""
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.etl.fetch_supabase import fetch_run                  # noqa: E402
from pipeline.corrosion_pipeline import traiter_run           # noqa: E402

# Donneurs propres = les 3 trajectoires de référence du simulateur (cf. mémoire simulateur)
DONNEURS = {
    "Run1":  "d6e31719-c3fb-4797-aa0b-65c4e605002a",   # graduel
    "Run12": "f5852fd4-8c3f-474e-9c20-a1ac129e018c",   # sprint
    "Run16": "cc4b4bec-1f3b-45ba-85d9-9c1db733eeae",   # sprint
}


def _couper(raw: pd.DataFrame) -> pd.DataFrame:
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


def durees_donneurs() -> dict:
    """Durée de vie réelle (h) de chaque donneur (jusqu'à rupture)."""
    out = {}
    for nom, rid in DONNEURS.items():
        try:
            raw = _couper(fetch_run(rid))
            ts = raw["timestamp_s"].astype(float)
            out[nom] = float((ts.max() - ts.min()) / 3600.0)
        except Exception:
            pass
    return out


def bande_simulateur(durees: dict, n: int = 40000, seed: int = 0):
    """Bande non-paramétrique du temps de rupture : mélange Dirichlet des durées donneurs
    (interpole entre morphologies vues, n'en invente pas). Retourne (p10, p50, p90)."""
    t = np.array(list(durees.values()), dtype=float)
    if len(t) == 0:
        return None
    rng = np.random.default_rng(seed)
    w = rng.dirichlet(np.ones(len(t)), size=n)          # poids de mélange par tirage
    synth = w @ t                                        # durée synthétique = mélange convexe
    synth *= rng.normal(1.0, 0.06, size=n)              # bruit run-to-run résiduel (±6 %)
    return tuple(float(np.percentile(synth, p)) for p in (10, 50, 90))


def estimer(run_id: str, model, feats: list) -> dict | None:
    """Renvoie les 3 estimations de durée de vie pour le run actif (ou None si trop tôt)."""
    raw = _couper(fetch_run(run_id))
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
    ts_raw = raw["timestamp_s"].astype(float)
    elapsed = float(ts_raw.iloc[-1] - ts_raw.iloc[0]) / 3600.0   # relatif au début du run
    section = float(last["section_perdue_pct"].iloc[0])
    cr_xgb = float(model.predict(last[feats])[0])
    cr_meas = float(last["CR_lisse"].iloc[0]) if "CR_lisse" in d.columns else np.nan
    rul_phys = float(last["RUL_h"].iloc[0]) if "RUL_h" in d.columns and pd.notna(last["RUL_h"].iloc[0]) else np.nan
    rul_phys = max(rul_phys, 0.0) if not np.isnan(rul_phys) else np.nan
    # RUL XGBoost-dérivé : RUL ∝ 1/vitesse → on remplace la vitesse mesurée par celle prédite
    rul_xgb = np.nan
    if not np.isnan(rul_phys) and not np.isnan(cr_meas) and cr_xgb > 1e-9:
        rul_xgb = max(rul_phys * (cr_meas / cr_xgb), 0.0)
    p10, p50, p90 = bande_simulateur(durees_donneurs()) or (np.nan, np.nan, np.nan)
    return {
        "elapsed_h": elapsed,
        "section_pct": section,
        "cr_xgb": cr_xgb,
        "cr_meas": cr_meas,
        "rul_phys_h": rul_phys,
        "rul_xgb_h": rul_xgb,
        "vie_phys_h": elapsed + rul_phys if not np.isnan(rul_phys) else np.nan,
        "vie_xgb_h": elapsed + rul_xgb if not np.isnan(rul_xgb) else np.nan,
        "sim_p10": p10, "sim_p50": p50, "sim_p90": p90,
    }


if __name__ == "__main__":
    import pickle
    from src.etl.fetch_supabase import fetch_all_runs
    m = pickle.load(open(os.path.join(ROOT, "models", "xgb_cr.pkl"), "rb"))
    fe = list(m.feature_names_in_)
    runs = fetch_all_runs(); act = runs[runs["status"] == "active"]
    rid = act.iloc[0]["run_id"] if len(act) else None
    print("Durées donneurs (h):", {k: round(v, 1) for k, v in durees_donneurs().items()})
    print("Bande simulateur P10/P50/P90 (h):", tuple(round(x, 1) for x in bande_simulateur(durees_donneurs())))
    if rid:
        r = estimer(rid, m, fe)
        if r:
            print(f"\nRun actif {rid[:8]} — écoulé {r['elapsed_h']:.1f} h, section {r['section_pct']:.0f} %")
            print(f"  Physique   : vie ≈ {r['vie_phys_h']:.1f} h (RUL {r['rul_phys_h']:.1f} h)")
            print(f"  XGBoost    : CR={r['cr_xgb']:.1f} (mesuré {r['cr_meas']:.1f}) → vie ≈ {r['vie_xgb_h']:.1f} h (RUL {r['rul_xgb_h']:.1f} h)")
            print(f"  Simulateur : bande [{r['sim_p10']:.1f} – {r['sim_p90']:.1f}] h, médiane {r['sim_p50']:.1f} h")
        else:
            print("Run actif : pas encore assez de points.")
