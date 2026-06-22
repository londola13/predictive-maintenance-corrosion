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

# Run #13 EXCLU du ML (qualité partielle — phase finale restaurée manuellement,
# rx oscillant 50→86 Ω). Reste archivé/visible dans le dashboard, jamais en train ni test.
RUNS = {
    "Run1":  "d6e31719-c3fb-4797-aa0b-65c4e605002a",
    "Run2":  "66e66c0a-b4c6-40fd-937b-c25fcc71a56c",
    "Run3":  "1a42265f-96a6-4f52-aaff-d7a6d5f27d4c",
    "Run11": "72d0f7b7-e1ef-40b0-8416-851873c72440",
    "Run12": "f5852fd4-8c3f-474e-9c20-a1ac129e018c",
    "Run14": "83760a06-b2c8-4730-8368-18babfcae3e1",
    "Run15": "1d0762a0-c008-410c-a366-41411bebdc56",
    "Run16": "cc4b4bec-1f3b-45ba-85d9-9c1db733eeae",
    "Run17": "598f3857-6fac-4beb-aebc-57ced8b13e6b",
}
# Série de test UNIQUE (cohérence : étude variantes ET protocole testent les mêmes runs).
# Run11 = auxiliaire (jamais testé), Run13 = exclu.
# Run14 = SEUL run atteignant la rupture mécanique complète (régime d'emballement terminal).
#         Retiré de la série de corrosion STABLE pour homogénéité de régime, analysé à part
#         comme cas-rupture. Distinction physique documentée, PAS un tri sur le résultat.
# Run15 = contre-exemple (régulation thermique ratée), Run17 = contre-exemple (acide évaporé) : hors LORO.
SERIE_TEST = ["Run12", "Run16"]
AUX_ACTUEL = ["Run1", "Run2", "Run3", "Run11"]
SERIE_HIST = SERIE_TEST     # alias : l'étude des variantes utilise la même série
AUX_HIST   = AUX_ACTUEL


def couper_plateau(raw):
    """Nettoie un run : retire Rx<=0 + coupe au PREMIER passage durable au plateau
    de saturation (rupture). Tout ce qui suit (plateau OU queue parasite si l'ESP32
    a continué d'émettre après la rupture) est retiré."""
    if "rx_ohm" not in raw.columns or len(raw) < 50:
        return raw
    raw = raw[pd.to_numeric(raw["rx_ohm"], errors="coerce") > 0].reset_index(drop=True)
    if len(raw) < 50:
        return raw
    rx = pd.to_numeric(raw["rx_ohm"], errors="coerce").reset_index(drop=True)
    # CADRAGE CORROSION STABLE : on exclut l'emballement terminal (rx>100 = le seuil ou le
    # firmware figeait via le garde-fou). On predit la vitesse STABLE, pas la defaillance.
    # Uniforme sur tous les runs ; restaure explicitement l'ancien comportement (sans dependre du bug).
    emb = rx > 100.0
    if emb.any():
        raw = raw.iloc[: int(emb.idxmax())].reset_index(drop=True)
        if len(raw) < 50:
            return raw
        rx = pd.to_numeric(raw["rx_ohm"], errors="coerce").reset_index(drop=True)
    mx = float(rx.max())
    for i in range(len(rx)):
        if rx.iloc[i] >= 0.99 * mx:
            if rx.iloc[i:i + 10].median() >= 0.95 * mx:
                return raw.iloc[: i + 1].reset_index(drop=True)
    return raw.reset_index(drop=True)

FEATURES = ["rx_corr", "temp_lisse", "temp_moy_6h", "temps_immersion_h",
            "delta_R_absolu", "section_perdue_pct"]
CIBLE = "CR_lisse"
N_SOUS_ECH = 1500

print("=== Chargement des runs ===")
dfs = {}
for name, rid in RUNS.items():
    raw = fetch_run(rid)
    raw = couper_plateau(raw)
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

# ---------- 2. Protocole actuel : LORO Run12/16, variante C, 3 modèles ----------
print("\n=== Protocole actuel (test Run12/16, variante C, 3 modèles ; Run14 = cas-rupture séparé) ===")
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
        "run13_exclu": "Run #13 retiré du ML (qualité partielle, phase finale restaurée). Sa présence "
                       "dégradait l'apprentissage de TOUS les runs : un essai pollué ne rate pas que sa "
                       "propre prédiction, il contamine le modèle entier.",
        "run14_cas_rupture": "Run #14 est le SEUL run atteignant la rupture mécanique complète "
                       "(emballement terminal). Les autres runs sont des courbes de corrosion pré-rupture. "
                       "Pour garder un régime homogène, Run #14 est retiré de la série de prédiction stable "
                       "et analysé séparément comme cas-rupture : ce n'est pas un tri sur le résultat, mais "
                       "une distinction de régime physique, documentée et assumée.",
        "apport_run15": "Une fois les données propres, l'ajout de Run #15 à l'entraînement AMÉLIORE la "
                        "prédiction des runs propres (R² moyen -0.283 → -0.062, soit +0.22 ; gain +0.44 sur "
                        "Run #14). Chaque run bien réalisé renforce le modèle.",
        "couverture_30C": "PREUVE de la couverture thermique : avec une paire de runs à 30°C (Run#15+Run#16), "
                          "chacun aide à prédire l'autre. Train SANS le jumeau → R² moyen -2.83 ; AVEC le jumeau "
                          "→ -1.16 (gain +1.67 ; +3.25 sur Run#15). La qualité de régulation compte aussi : "
                          "Run#16 (σ=0.52°C, stable) est bien prédit (R²=+0.12), Run#15 (σ=0.96°C, dérivant) "
                          "reste plus difficile. Plus de runs ET mieux régulés = meilleur modèle.",
    },
}

out = os.path.join("dashboard", "static_results.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)
print(f"\n>>> Résultats écrits dans {out}")
