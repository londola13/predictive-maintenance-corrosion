"""
parse_pi_csv.py
---------------
Parser pour exports PI Server (OSIsoft/AVEVA Historian).
Supporte les formats : PI DataLink (Excel) et PI Web API (CSV).

Usage à COTCO :
    df_dcs = parse_pi_csv("data/enterprise/pi_export.csv")
    df_dcs = parse_pi_datalink("data/enterprise/pi_datalink.xlsx")
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Mapping noms colonnes PI → noms standards du projet
# Adapter selon l'export réel COTCO
COTCO_TAG_MAPPING = {
    # Températures
    "TI-1001": "T_mean",
    "TI-1002": "T_aval",
    "TI-1003": "T_paroi",
    "TI-1004": "T_ambiante",
    # Pressions
    "PI-2001": "P_mean",
    "PI-2002": "P_aval",
    "PI-2003": "dP_filtre",
    "PI-2004": "P_psv",
    "PI-2005": "P_detendeur",
    # Débits
    "FI-3001": "debit_vol",
    "FI-3002": "debit_masse",
    "FI-3003": "debit_inhib",
    # Analyseurs
    "AI-4001": "CO2_pct",
    "AI-4002": "H2S_ppm",
    "AI-4003": "BSW_mean",
    "AI-4004": "sable_ppm",
    # Corrosion & intégrité
    "CI-5001": "CR_sonde_amont",
    "CI-5002": "CR_sonde_aval",
    "CI-5003": "inhib_mean",
    "CI-5004": "CP_mV",
}

# Colonnes attendues après mapping
COLONNES_DCS = list(COTCO_TAG_MAPPING.values())


def parse_pi_csv(path: str, encoding: str = "utf-8") -> pd.DataFrame:
    """
    Parse un export CSV du PI Server.
    Format attendu : colonnes = tags DCS, lignes = horodatages.

    Retourne un DataFrame propre avec colonnes standardisées.
    """
    path = Path(path)
    print(f"[PI CSV] Lecture : {path.name}")

    df = pd.read_csv(path, encoding=encoding)

    # Détecter colonne timestamp
    timestamp_col = _detect_timestamp_col(df)
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
    df = df.rename(columns={timestamp_col: "timestamp"})
    df = df.set_index("timestamp").sort_index()

    # Filtrer qualité (colonne "quality" si présente)
    df = _filter_good_quality(df)

    # Renommer les tags vers noms standards
    df = _remap_columns(df, COTCO_TAG_MAPPING)

    # Convertir en numérique
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Supprimer lignes entièrement vides
    df = df.dropna(how="all")

    # Resample horaire (PI peut donner des données irrégulières)
    df = df.resample("1h").mean()

    print(f"[PI CSV] {len(df)} lignes | {df.index.min()} → {df.index.max()}")
    _rapport_completude(df)

    return df.reset_index()


def parse_pi_datalink(path: str) -> pd.DataFrame:
    """
    Parse un export PI DataLink (Excel).
    PI DataLink génère des tableaux avec une ligne de tags en ligne 1
    et les timestamps en colonne A.
    """
    path = Path(path)
    print(f"[PI DataLink] Lecture : {path.name}")

    # PI DataLink : ligne 0 = tags, ligne 1+ = données
    df = pd.read_excel(path, header=0)

    timestamp_col = df.columns[0]
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
    df = df.rename(columns={timestamp_col: "timestamp"})
    df = df.set_index("timestamp").sort_index()

    df = _filter_good_quality(df)
    df = _remap_columns(df, COTCO_TAG_MAPPING)

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(how="all").resample("1h").mean()

    print(f"[PI DataLink] {len(df)} lignes | {df.index.min()} → {df.index.max()}")
    _rapport_completude(df)

    return df.reset_index()


def aggregate_30j(df_dcs: pd.DataFrame, date_reference: pd.Timestamp) -> dict:
    """
    Calcule les statistiques DCS sur les 30 jours précédant une mesure UT.
    Retourne un dict avec mean, max, std et nb_upsets pour chaque tag.

    Usage :
        stats = aggregate_30j(df_dcs, date_mesure_UT)
    """
    debut = date_reference - pd.Timedelta(days=30)
    fenetre = df_dcs[
        (df_dcs["timestamp"] >= debut) & (df_dcs["timestamp"] < date_reference)
    ]

    if len(fenetre) == 0:
        print(f"[WARN] Aucune donnée DCS dans les 30j avant {date_reference}")
        return {}

    stats = {}
    for col in COLONNES_DCS:
        if col not in fenetre.columns:
            continue
        serie = fenetre[col].dropna()
        if len(serie) == 0:
            continue
        stats[f"{col}_mean"] = serie.mean()
        stats[f"{col}_max"] = serie.max()
        stats[f"{col}_std"] = serie.std()

    # Compter les upsets (valeurs hors plage normale)
    stats["nb_upsets"] = _count_upsets(fenetre)

    return stats


# ── Fonctions utilitaires privées ─────────────────────────────────────────────

def _detect_timestamp_col(df: pd.DataFrame) -> str:
    """Détecte automatiquement la colonne timestamp."""
    candidats = ["timestamp", "Timestamp", "DateTime", "datetime",
                 "Date", "date", "Time", "time"]
    for c in candidats:
        if c in df.columns:
            return c
    # Fallback : première colonne
    return df.columns[0]


def _filter_good_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Filtre sur la colonne quality PI si elle existe."""
    quality_cols = [c for c in df.columns if "quality" in c.lower()]
    for qcol in quality_cols:
        df = df[df[qcol].astype(str).str.lower().isin(["good", "0", "192"])]
        df = df.drop(columns=[qcol])
    return df


def _remap_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Renomme les colonnes selon le mapping tag → nom standard."""
    rename = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename)
    # Garder seulement les colonnes reconnues
    cols_connues = [c for c in COLONNES_DCS if c in df.columns]
    return df[cols_connues]


def _count_upsets(df: pd.DataFrame) -> int:
    """
    Compte les points hors plage normale (upsets process).
    Les seuils sont ceux de cotco_kribi_config.yaml.
    """
    upsets = 0
    seuils = {
        "T_mean":     (35, 65),
        "P_mean":     (65, 100),
        "CO2_pct":    (0.5, 5.0),
        "BSW_mean":   (0.5, 30),
        "inhib_mean": (20, 80),
    }
    for col, (lo, hi) in seuils.items():
        if col in df.columns:
            serie = df[col].dropna()
            upsets += int(((serie < lo) | (serie > hi)).sum())
    return upsets


def _rapport_completude(df: pd.DataFrame) -> None:
    """Affiche le taux de complétude par tag."""
    total = len(df)
    print(f"\n  Complétude des tags ({total} points) :")
    for col in df.columns:
        pct = 100 * df[col].notna().sum() / total
        flag = "[OK]" if pct > 90 else ("[??]" if pct > 50 else "[!!]")
        print(f"  {flag} {col:<20} {pct:.0f}%")
