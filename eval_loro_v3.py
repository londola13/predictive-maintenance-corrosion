# -*- coding: utf-8 -*-
"""Protocole v3 — corriger le desequilibre serie (4400 pts) vs auxiliaires (19700 pts).

4 variantes comparees en LORO complet sur la serie Run #11-14 :
  A. Serie seule
  B. Serie + auxiliaires bruts (desequilibre 4.5:1)
  C. Serie + auxiliaires sous-echantillonnes (~1500 pts chacun)
  D. Serie + auxiliaires ponderes (sample_weight equilibre les volumes)
"""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd, numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score

from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run, PARAMS_XGB

SERIE = {
    "Run11": "72d0f7b7-e1ef-40b0-8416-851873c72440",
    "Run12": "f5852fd4-8c3f-474e-9c20-a1ac129e018c",
    "Run13": "5134db06-aa83-4ba3-838f-698de4e3b38b",
    "Run14": "83760a06-b2c8-4730-8368-18babfcae3e1",
}
AUX = {
    "Run1": "d6e31719-c3fb-4797-aa0b-65c4e605002a",
    "Run2": "66e66c0a-b4c6-40fd-937b-c25fcc71a56c",
    "Run3": "1a42265f-96a6-4f52-aaff-d7a6d5f27d4c",
}
FEATURES = ["rx_corr", "temp_lisse", "temp_moy_6h", "temps_immersion_h",
            "delta_R_absolu", "section_perdue_pct"]
CIBLE = "CR_lisse"
N_SOUS_ECH = 1500  # taille cible par run auxiliaire (variante C)

dfs = {}
for name, rid in {**SERIE, **AUX}.items():
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    dfs[name] = df.dropna(subset=FEATURES + [CIBLE]).reset_index(drop=True)

def xgb_eval(tr, te, weights=None):
    m = xgb.XGBRegressor(**PARAMS_XGB)
    m.fit(tr[FEATURES], tr[CIBLE], sample_weight=weights)
    pred = m.predict(te[FEATURES])
    return r2_score(te[CIBLE], pred), mean_absolute_error(te[CIBLE], pred)

resultats = {}
for variante in ["A", "B", "C", "D"]:
    lignes = {}
    for test_name in SERIE:
        serie_train = [n for n in SERIE if n != test_name]
        if variante == "A":
            tr = pd.concat([dfs[n] for n in serie_train], ignore_index=True)
            w = None
        elif variante == "B":
            tr = pd.concat([dfs[n] for n in serie_train] + [dfs[n] for n in AUX],
                           ignore_index=True)
            w = None
        elif variante == "C":
            aux_ss = [dfs[n].sample(n=min(N_SOUS_ECH, len(dfs[n])), random_state=42)
                      for n in AUX]
            tr = pd.concat([dfs[n] for n in serie_train] + aux_ss, ignore_index=True)
            w = None
        else:  # D — ponderation
            tr_serie = pd.concat([dfs[n] for n in serie_train], ignore_index=True)
            tr_aux = pd.concat([dfs[n] for n in AUX], ignore_index=True)
            # poids auxiliaires : volume serie / volume aux -> contribution totale egale
            w_aux = len(tr_serie) / len(tr_aux)
            tr = pd.concat([tr_serie, tr_aux], ignore_index=True)
            w = np.concatenate([np.ones(len(tr_serie)), np.full(len(tr_aux), w_aux)])
        lignes[test_name] = xgb_eval(tr, dfs[test_name], w)
    resultats[variante] = lignes

NOMS = {"A": "A. Serie seule", "B": "B. + Aux bruts", "C": "C. + Aux sous-ech.", "D": "D. + Aux ponderes"}
print("\n=== LORO serie Run #11-14 — XGBoost, 4 variantes d'entrainement ===\n")
header = "  {:22s}".format("Variante") + "".join(f" | {n:>14s}" for n in SERIE) + " | {:>14s}".format("MOYENNE R2")
print(header)
print("  " + "-" * (len(header) - 2))
for v in ["A", "B", "C", "D"]:
    r2s = [resultats[v][n][0] for n in SERIE]
    ligne = "  {:22s}".format(NOMS[v])
    for n in SERIE:
        ligne += f" | R2={resultats[v][n][0]:10.3f}"
    ligne += f" | {np.mean(r2s):14.3f}"
    print(ligne)
print()
for v in ["A", "B", "C", "D"]:
    maes = [resultats[v][n][1] for n in SERIE]
    ligne = "  {:22s}".format(NOMS[v])
    for n in SERIE:
        ligne += f" | MAE={resultats[v][n][1]:9.1f}"
    ligne += f" | {np.mean(maes):14.1f}"
    print(ligne)
