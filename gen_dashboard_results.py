# -*- coding: utf-8 -*-
"""Précalcule les résultats ML pour le dashboard -> dashboard/static_results.json.

Le dashboard déployé ne ré-entraîne JAMAIS de modèle : il lit ce fichier.
À relancer localement après chaque nouveau run terminé :
    venv/Scripts/python.exe gen_dashboard_results.py
"""
import json
import os
import sys
import tempfile
import warnings
from datetime import datetime, timezone

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run, PARAMS_XGB

RUNS = {
    "Run1":  "d6e31719-c3fb-4797-aa0b-65c4e605002a",
    "Run2":  "66e66c0a-b4c6-40fd-937b-c25fcc71a56c",
    "Run3":  "1a42265f-96a6-4f52-aaff-d7a6d5f27d4c",
    "Run11": "72d0f7b7-e1ef-40b0-8416-851873c72440",
    "Run12": "f5852fd4-8c3f-474e-9c20-a1ac129e018c",
    "Run13": "5134db06-aa83-4ba3-838f-698de4e3b38b",
    "Run14": "83760a06-b2c8-4730-8368-18babfcae3e1",
}
SERIE_HIST = ["Run11", "Run12", "Run13", "Run14"]   # étude variantes (historique session 2026-06-11)
SERIE_TEST = ["Run12", "Run13", "Run14"]            # protocole actuel (Run11 reclassé auxiliaire)
AUX_HIST   = ["Run1", "Run2", "Run3"]
AUX_ACTUEL = ["Run1", "Run2", "Run3", "Run11"]

FEATURES = ["rx_corr", "temp_lisse", "temp_moy_6h", "temps_immersion_h",
            "delta_R_absolu", "section_perdue_pct"]
CIBLE = "CR_lisse"
N_SOUS_ECH = 1500

print("=== Chargement des runs ===")
dfs = {}
for name, rid in RUNS.items():
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    dfs[name] = df.dropna(subset=FEATURES + [CIBLE]).reset_index(drop=True)
    print(f"  {name}: {len(dfs[name])} pts")


def eval_xgb(train, test):
    m = xgb.XGBRegressor(**PARAMS_XGB)
    m.fit(train[FEATURES], train[CIBLE])
    p = m.predict(test[FEATURES])
    return round(float(r2_score(test[CIBLE], p)), 3), round(float(mean_absolute_error(test[CIBLE], p)), 1)


def sous_ech(name):
    d = dfs[name]
    return d.sample(n=min(N_SOUS_ECH, len(d)), random_state=42)


# ---------- 1. Étude des 4 variantes (LORO sur Run11-14, XGBoost) ----------
print("\n=== Étude variantes A-D (LORO Run11-14) ===")
variantes = {}
for code, nom in [("A", "Série seule"), ("B", "+ Auxiliaires bruts"),
                  ("C", "+ Auxiliaires sous-échantillonnés"), ("D", "+ Auxiliaires pondérés")]:
    res = {}
    for test_name in SERIE_HIST:
        serie_train = [n for n in SERIE_HIST if n != test_name]
        if code == "A":
            tr = pd.concat([dfs[n] for n in serie_train], ignore_index=True)
            w = None
        elif code == "B":
            tr = pd.concat([dfs[n] for n in serie_train] + [dfs[n] for n in AUX_HIST], ignore_index=True)
            w = None
        elif code == "C":
            tr = pd.concat([dfs[n] for n in serie_train] + [sous_ech(n) for n in AUX_HIST], ignore_index=True)
            w = None
        else:
            tr_s = pd.concat([dfs[n] for n in serie_train], ignore_index=True)
            tr_a = pd.concat([dfs[n] for n in AUX_HIST], ignore_index=True)
            tr = pd.concat([tr_s, tr_a], ignore_index=True)
            w = np.concatenate([np.ones(len(tr_s)), np.full(len(tr_a), len(tr_s) / len(tr_a))])
        m = xgb.XGBRegressor(**PARAMS_XGB)
        m.fit(tr[FEATURES], tr[CIBLE], sample_weight=w)
        p = m.predict(dfs[test_name][FEATURES])
        res[test_name] = {
            "r2": round(float(r2_score(dfs[test_name][CIBLE], p)), 3),
            "mae": round(float(mean_absolute_error(dfs[test_name][CIBLE], p)), 1),
        }
    moy_r2 = round(float(np.mean([v["r2"] for v in res.values()])), 3)
    moy_mae = round(float(np.mean([v["mae"] for v in res.values()])), 1)
    variantes[code] = {"nom": nom, "runs": res, "moyenne_r2": moy_r2, "moyenne_mae": moy_mae,
                       "retenue": code == "C"}
    print(f"  Variante {code} ({nom}) : R2 moyen = {moy_r2}")

# ---------- 2. Protocole actuel : LORO Run12-14, variante C, 3 modèles ----------
print("\n=== Protocole actuel (test Run12/13/14, variante C, 3 modèles) ===")
protocole = {}
for test_name in SERIE_TEST:
    serie_train = [n for n in SERIE_TEST if n != test_name]
    tr = pd.concat([dfs[n] for n in serie_train] + [sous_ech(n) for n in AUX_ACTUEL],
                   ignore_index=True)
    te = dfs[test_name]
    entry = {}
    for nom_m, modele in [("XGBoost", xgb.XGBRegressor(**PARAMS_XGB)),
                          ("Régression linéaire", LinearRegression()),
                          ("Moyenne constante", DummyRegressor(strategy="mean"))]:
        modele.fit(tr[FEATURES], tr[CIBLE])
        p = modele.predict(te[FEATURES])
        entry[nom_m] = {"r2": round(float(r2_score(te[CIBLE], p)), 3),
                        "mae": round(float(mean_absolute_error(te[CIBLE], p)), 1)}
    protocole[test_name] = entry
    print(f"  {test_name}: XGB R2={entry['XGBoost']['r2']}  RegLin R2={entry['Régression linéaire']['r2']}")

# ---------- 3. Importance des features (XGBoost, tout le corpus variante C) ----------
tr_all = pd.concat([dfs[n] for n in SERIE_TEST] + [sous_ech(n) for n in AUX_ACTUEL],
                   ignore_index=True)
m_all = xgb.XGBRegressor(**PARAMS_XGB)
m_all.fit(tr_all[FEATURES], tr_all[CIBLE])
importance = {f: round(float(v), 4) for f, v in zip(FEATURES, m_all.feature_importances_)}

# ---------- 4. Méta ----------
resultats = {
    "genere_le": datetime.now(timezone.utc).isoformat(),
    "nb_points_par_run": {n: int(len(d)) for n, d in dfs.items()},
    "features": FEATURES,
    "cible": CIBLE,
    "variantes": variantes,
    "protocole_actuel": protocole,
    "importance_features": importance,
    "narratif": {
        "mecanisme": "La prédiction réussit quand l'entraînement couvre la plage de température du run testé. "
                     "La couverture thermique compte plus que le volume brut de données.",
        "variante_retenue": "C — auxiliaires sous-échantillonnés à 1500 points (équilibre série/auxiliaires)",
        "phase2": "Phase contrôlée : bain thermostaté 25W — Run15/16 à 30°C, Run17/18 à 32°C (3 runs/consigne).",
    },
}

out = os.path.join("dashboard", "static_results.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)
print(f"\n>>> Résultats écrits dans {out}")
