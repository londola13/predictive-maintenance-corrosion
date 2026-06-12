# -*- coding: utf-8 -*-
"""Protocole d'evaluation v2 — serie homogene Run #11-14 (repetitions HCl brut).

1. LORO complet sur les 4 runs de la serie (chacun teste a tour de role)
2. Deux variantes d'entrainement : serie seule vs serie + runs auxiliaires (R1/R2/R3)
3. Baselines : regression lineaire (memes features) + moyenne du train
   -> repond a la question : XGBoost apporte-t-il quelque chose vs un modele simple ?
"""
import sys, os, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd, numpy as np
import xgboost as xgb
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from src.etl.fetch_supabase import fetch_run
from pipeline.corrosion_pipeline import traiter_run, PARAMS_XGB

# Serie homogene : repetitions Run #1 (HCl brut, fil au fond)
SERIE = {
    "Run11": "72d0f7b7-e1ef-40b0-8416-851873c72440",
    "Run12": "f5852fd4-8c3f-474e-9c20-a1ac129e018c",
    "Run13": "5134db06-aa83-4ba3-838f-698de4e3b38b",
    "Run14": "83760a06-b2c8-4730-8368-18babfcae3e1",
}
# Runs auxiliaires (conditions differentes — apport a quantifier)
AUX = {
    "Run1": "d6e31719-c3fb-4797-aa0b-65c4e605002a",
    "Run2": "66e66c0a-b4c6-40fd-937b-c25fcc71a56c",
    "Run3": "1a42265f-96a6-4f52-aaff-d7a6d5f27d4c",
}
FEATURES = ["rx_corr", "temp_lisse", "temp_moy_6h", "temps_immersion_h",
            "delta_R_absolu", "section_perdue_pct"]
CIBLE = "CR_lisse"

print("=== Chargement ===")
dfs = {}
for name, rid in {**SERIE, **AUX}.items():
    raw = fetch_run(rid)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False); tmp.close()
    df = traiter_run(tmp.name)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    dfs[name] = df
    print(f"  {name}: {len(df)} pts  T_moy={df['temp_lisse'].mean():.1f}C")

def evaluer(train_df, test_df, label):
    tr = train_df.dropna(subset=FEATURES + [CIBLE])
    te = test_df.dropna(subset=FEATURES + [CIBLE])
    res = {}
    for nom, modele in [
        ("XGBoost", xgb.XGBRegressor(**PARAMS_XGB)),
        ("RegLin",  LinearRegression()),
        ("Moyenne", DummyRegressor(strategy="mean")),
    ]:
        m = modele
        m.fit(tr[FEATURES], tr[CIBLE])
        pred = m.predict(te[FEATURES])
        res[nom] = (r2_score(te[CIBLE], pred), mean_absolute_error(te[CIBLE], pred))
    return res

for variante, extra in [("SERIE SEULE (train = 3 autres de la serie)", []),
                        ("SERIE + AUXILIAIRES (R1+R2+R3 ajoutes au train)", list(AUX))]:
    print(f"\n=== LORO — {variante} ===")
    agg = {n: [] for n in ["XGBoost", "RegLin", "Moyenne"]}
    for test_name in SERIE:
        train_names = [n for n in SERIE if n != test_name] + extra
        train = pd.concat([dfs[n] for n in train_names], ignore_index=True)
        train.replace([np.inf, -np.inf], np.nan, inplace=True)
        res = evaluer(train, dfs[test_name], test_name)
        ligne = "  Test {:6s} |".format(test_name)
        for nom in ["XGBoost", "RegLin", "Moyenne"]:
            r2, mae = res[nom]
            agg[nom].append((r2, mae))
            ligne += f"  {nom}: R2={r2:7.3f} MAE={mae:7.1f} |"
        print(ligne)
    print("  " + "-" * 100)
    ligne = "  MOYENNE     |"
    for nom in ["XGBoost", "RegLin", "Moyenne"]:
        r2m = np.mean([x[0] for x in agg[nom]])
        maem = np.mean([x[1] for x in agg[nom]])
        ligne += f"  {nom}: R2={r2m:7.3f} MAE={maem:7.1f} |"
    print(ligne)
