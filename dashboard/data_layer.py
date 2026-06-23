# -*- coding: utf-8 -*-
"""Couche d'accès aux données pour le dashboard de supervision.

Réutilise src/etl/fetch_supabase.py et pipeline/corrosion_pipeline.py tels quels.
Les secrets sont injectés dans os.environ AVANT l'import de fetch_supabase
(qui lit SUPABASE_URL / SUPABASE_KEY au moment de l'import).
"""
import os
import sys
import tempfile

import pandas as pd
import requests
import streamlit as st

# --- Bridge secrets Streamlit -> variables d'environnement (AVANT les imports projet)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    if "SUPABASE_URL" in st.secrets:
        os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
    if "SUPABASE_KEY" in st.secrets:
        os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]
except Exception:
    pass  # pas de secrets.toml : on suppose les env vars déjà définies

from src.etl.fetch_supabase import fetch_run, fetch_all_runs, SUPABASE_URL, HEADERS  # noqa: E402
from pipeline.corrosion_pipeline import traiter_run  # noqa: E402


# ============================================================
# REGISTRE DES RUNS — source de vérité du dashboard
# (les notes de cr_runs sont brouillonnes ; ce registre est propre)
# ============================================================
RUNS_REGISTRY = {
    "d6e31719-c3fb-4797-aa0b-65c4e605002a": {
        "label": "Run #1", "condition": "HCl dilué (proportion inconnue)", "groupe": "Référence",
        "temp": "29.4 °C", "duree": "22.3 h", "phase": "Exploratoire",
        "note": "Acide DILUÉ (proportion non consignée) — d'où une durée (22.3 h) plus longue "
                "que les runs à acide pur (10–15 h). Cycle de vie complet (0.97 → 84.7 Ω).",
    },
    "66e66c0a-b4c6-40fd-937b-c25fcc71a56c": {
        "label": "Run #2", "condition": "HCl dilué 1:1", "groupe": "Auxiliaire",
        "temp": "29.8 °C", "duree": "62 h", "phase": "Exploratoire",
        "note": "Biais gravité identifié (fil suspendu) — rupture localisée prématurée",
    },
    "1a42265f-96a6-4f52-aaff-d7a6d5f27d4c": {
        "label": "Run #3", "condition": "HCl 2:1", "groupe": "Auxiliaire",
        "temp": "29.9 °C", "duree": "~93 h", "phase": "Exploratoire",
        "note": "Rupture par piqûre à une extrémité (effet de bord électrochimique)",
    },
    "72d0f7b7-e1ef-40b0-8416-851873c72440": {
        "label": "Run #11", "condition": "HCl brut", "groupe": "Auxiliaire",
        "temp": "32.7 °C", "duree": "10.2 h", "phase": "Série répétition",
        "note": "Température élevée (canicule) — hors plage contrôlable, reclassé auxiliaire",
    },
    "f5852fd4-8c3f-474e-9c20-a1ac129e018c": {
        "label": "Run #12", "condition": "HCl brut", "groupe": "Série test",
        "temp": "29.5 °C", "duree": "14.7 h", "phase": "Série répétition",
        "note": "Run propre — meilleur score ML (R² = 0.43 en LORO variante C)",
    },
    "5134db06-aa83-4ba3-838f-698de4e3b38b": {
        "label": "Run #13", "condition": "HCl brut", "groupe": "Archive (exclu ML)",
        "temp": "31.3 °C", "duree": "12.6 h", "phase": "Série répétition",
        "note": "EXCLU du ML — qualité partielle (phase finale restaurée, rx oscillant 50→86 Ω). "
                "Conservé pour transparence, jamais en entraînement ni test.",
    },
    "83760a06-b2c8-4730-8368-18babfcae3e1": {
        "label": "Run #14", "condition": "HCl brut", "groupe": "Série test",
        "temp": "31.7 °C", "duree": "13.6 h", "phase": "Série répétition",
        "note": "Run propre — clôturé au dernier point avant plateau",
    },
    "1d0762a0-c008-410c-a366-41411bebdc56": {
        "label": "Run #15", "condition": "HCl brut", "groupe": "Série test",
        "temp": "30.2 °C", "duree": "10.9 h", "phase": "Phase 2 contrôlée",
        "note": "1er run phase contrôlée (bain-marie consigne 30°C) — T° dérive 31→28°C, "
                "régulation imparfaite — rupture nette 10.9h",
    },
    "cc4b4bec-1f3b-45ba-85d9-9c1db733eeae": {
        "label": "Run #16", "condition": "HCl brut", "groupe": "Série test",
        "temp": "30.1 °C", "duree": "12.3 h", "phase": "Phase 2 contrôlée",
        "note": "2e run plage 30°C — régulation EXCELLENTE (σ=0.52°C, plat, bien mieux que Run#15) — "
                "rupture nette 12.3h — forme la paire répétable 30°C avec Run#15",
    },
    "598f3857-6fac-4beb-aebc-57ced8b13e6b": {
        "label": "Run #17", "condition": "HCl brut (évaporé)", "groupe": "Contre-exemple (concentration)",
        "temp": "29.9 °C", "duree": "19.8 h", "phase": "Phase 2 contrôlée",
        "note": "CONTRE-EXEMPLE concentration — régulation thermique PARFAITE (σ=0.55°C) mais acide laissé "
                ">1h à l'air avant immersion → HCl évaporé → concentration plus basse → cinétique 2× lente "
                "(19.8h, rupture 45Ω). Hors LORO. Prouve que la concentration est un facteur à contrôler.",
    },
}

LABELS = {rid: meta["label"] for rid, meta in RUNS_REGISTRY.items()}


# ============================================================
# ACCÈS DONNÉES (avec cache Streamlit)
# ============================================================
@st.cache_data(ttl=3600, show_spinner="Chargement des mesures…")
def charger_run_brut(run_id: str) -> pd.DataFrame:
    """Mesures brutes d'un run (immuable une fois terminé -> cache long)."""
    return fetch_run(run_id)


@st.cache_data(ttl=3600, show_spinner="Traitement du signal (pipeline)…")
def couper_plateau_saturation(raw: pd.DataFrame) -> pd.DataFrame:
    """Nettoie un run brut pour le pipeline :
    1. retire les points Rx<=0 (aberrants au démarrage / débranchement ESP32) ;
    2. coupe au PREMIER passage durable au plateau de saturation (Rx >=99% du max
       confirmé sur les points suivants = rupture / circuit ouvert). Tout ce qui suit
       la rupture (plateau OU queue parasite si l'ESP32 a continué d'émettre) est retiré.
    Ne touche pas un emballement réel (montée progressive) : seul le plateau franc coupe."""
    if "rx_ohm" not in raw.columns or len(raw) < 50:
        return raw
    raw = raw[pd.to_numeric(raw["rx_ohm"], errors="coerce") > 0].reset_index(drop=True)
    if len(raw) < 50:
        return raw
    rx = pd.to_numeric(raw["rx_ohm"], errors="coerce").reset_index(drop=True)
    mx = float(rx.max())
    for i in range(len(rx)):
        if rx.iloc[i] >= 0.99 * mx:
            # confirmer un plateau durable (et non un pic isolé)
            if rx.iloc[i:i + 10].median() >= 0.95 * mx:
                return raw.iloc[: i + 1].reset_index(drop=True)
    return raw.reset_index(drop=True)


def charger_run_traite(run_id: str) -> pd.DataFrame:
    """Run complet passé dans le pipeline (nettoyage, compensation, CR, RUL)."""
    raw = fetch_run(run_id)
    raw = couper_plateau_saturation(raw)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
    raw.to_csv(tmp, sep=";", index=False)
    tmp.close()
    df = traiter_run(tmp.name)
    try:
        os.unlink(tmp.name)
    except OSError:
        pass
    df = df.replace([float("inf"), float("-inf")], pd.NA)
    return df


@st.cache_data(ttl=30)
def lister_runs() -> pd.DataFrame:
    """Liste cr_runs (cache court : détecte un nouveau run actif rapidement)."""
    return fetch_all_runs()


def detecter_run_actif():
    """Retourne (run_id, row) du run actif le plus récent, ou (None, None)."""
    try:
        runs = lister_runs()
        actifs = runs[runs["status"] == "active"]
        if len(actifs) == 0:
            return None, None
        row = actifs.iloc[0]
        return row["run_id"], row
    except Exception:
        return None, None


@st.cache_data(ttl=25)
def dernieres_mesures(run_id: str, n: int = 240) -> pd.DataFrame:
    """N derniers points d'un run (léger — pour la page Live, refresh 30 s)."""
    params = {
        "run_id": f"eq.{run_id}",
        "order": "timestamp_s.desc",
        "select": "timestamp_s,rx_ohm,temp_c,delta_r_per_h",
        "limit": str(n),
    }
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/cr_measurements",
                        headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    if len(df):
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.sort_values("timestamp_s").reset_index(drop=True)
    return df


@st.cache_data(ttl=25)
def dernieres_predictions(run_id: str, n: int = 200) -> pd.DataFrame:
    """Prédictions ML d'un run (alimentées par le service predict_loop)."""
    params = {
        "run_id": f"eq.{run_id}",
        "order": "predicted_at.desc",
        "select": "predicted_at,cr_pred,rul_pred,model_version",
        "limit": str(n),
    }
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/cr_predictions",
                        headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    if len(df):
        df["predicted_at"] = pd.to_datetime(df["predicted_at"], errors="coerce")
        for c in ("cr_pred", "rul_pred"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.sort_values("predicted_at").reset_index(drop=True)
    return df


@st.cache_data(ttl=3600)
def stats_globales() -> dict:
    """KPIs globaux : nb runs, mesures totales, heures cumulées."""
    runs = fetch_all_runs()
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/cr_measurements",
        headers={**HEADERS, "Prefer": "count=exact"},
        params={"select": "id", "limit": "1"},
        timeout=15,
    )
    total = 0
    cr = resp.headers.get("content-range", "")
    if "/" in cr:
        try:
            total = int(cr.split("/")[-1])
        except ValueError:
            total = 0
    heures = 0.0
    for _, r in runs.iterrows():
        if pd.notna(r.get("ended_at")) and pd.notna(r.get("started_at")):
            try:
                heures += (pd.Timestamp(r["ended_at"]) - pd.Timestamp(r["started_at"])).total_seconds() / 3600
            except Exception:
                pass
    return {
        "nb_runs": len(runs),
        "nb_termines": int((runs["status"] == "completed").sum()),
        "nb_actifs": int((runs["status"] == "active").sum()),
        "total_mesures": total,
        "heures_cumulees": heures,
    }


def downsample(df: pd.DataFrame, max_points: int = 4000) -> pd.DataFrame:
    """Sous-échantillonne pour l'affichage si le run est très long."""
    if len(df) <= max_points:
        return df
    pas = max(1, len(df) // max_points)
    return df.iloc[::pas].reset_index(drop=True)
