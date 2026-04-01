"""
parse_labo_excel.py
-------------------
Parser pour analyses laboratoire (Excel).
Fréquence : mensuelle chez COTCO.

Paramètres : pH, Cl⁻ (mg/L), Fe²⁺ (mg/L), résiduel inhibiteur, SRB (ufc/mL)

Usage à COTCO :
    df_labo = parse_labo_excel("data/enterprise/labo/analyses_2024.xlsx")
    df_labo = parse_labo_folder("data/enterprise/labo/")
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Colonnes de sortie standardisées
COLONNES_LABO = [
    "date", "CML_ID", "pH_labo", "Cl_mgL", "Fe_mgL",
    "inhib_residuel_mgL", "SRB_ufc_mL", "H2S_dissous_mgL",
    "notes_labo", "source_fichier"
]

# Mapping flexible — adapter selon le format Excel COTCO réel
COLUMN_MAPPING = {
    # pH
    "ph": "pH_labo", "ph_field": "pH_labo", "ph_lab": "pH_labo",

    # Chlorures
    "chlorures": "Cl_mgL", "cl-": "Cl_mgL", "chloride": "Cl_mgL",
    "cl (mg/l)": "Cl_mgL", "cl_mgl": "Cl_mgL",

    # Fer dissous
    "fer": "Fe_mgL", "fe2+": "Fe_mgL", "fe (mg/l)": "Fe_mgL",
    "iron": "Fe_mgL", "fe_mgl": "Fe_mgL", "fe dissolved": "Fe_mgL",

    # Résiduel inhibiteur
    "inhibiteur": "inhib_residuel_mgL", "inhibitor": "inhib_residuel_mgL",
    "inhib residuel": "inhib_residuel_mgL", "ci (mg/l)": "inhib_residuel_mgL",
    "corrosion inhibitor": "inhib_residuel_mgL",

    # SRB
    "srb": "SRB_ufc_mL", "bsr": "SRB_ufc_mL",
    "sulfate reducing bacteria": "SRB_ufc_mL",
    "bacteria": "SRB_ufc_mL", "srb (ufc/ml)": "SRB_ufc_mL",

    # H2S dissous
    "h2s": "H2S_dissous_mgL", "h2s dissous": "H2S_dissous_mgL",
    "dissolved h2s": "H2S_dissous_mgL",

    # CML / point
    "cml": "CML_ID", "point": "CML_ID", "location": "CML_ID",
    "sample_point": "CML_ID", "point prélèvement": "CML_ID",

    # Date
    "date": "date", "date analyse": "date", "sample date": "date",

    # Notes
    "remarques": "notes_labo", "comments": "notes_labo", "notes": "notes_labo",
}


def parse_labo_excel(path: str, sheet: str | int = 0) -> pd.DataFrame:
    """
    Parse un fichier Excel de résultats labo.
    Détecte automatiquement les colonnes via COLUMN_MAPPING.

    Args:
        path  : chemin vers le fichier Excel
        sheet : nom ou index de la feuille (défaut = 0)
    """
    path = Path(path)
    print(f"[Labo Excel] Lecture : {path.name}")

    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {path}")

    # Essayer plusieurs lignes d'en-tête (certains labo mettent un titre en ligne 1)
    df = None
    for header_row in [0, 1, 2]:
        try:
            candidate = pd.read_excel(path, sheet_name=sheet, header=header_row)
            # Valider : au moins 3 colonnes numériques après mapping
            candidate_mapped = _remap(candidate)
            cols_num = sum(1 for c in ["pH_labo", "Cl_mgL", "Fe_mgL"]
                          if c in candidate_mapped.columns)
            if cols_num >= 1:
                df = candidate_mapped
                print(f"[Labo Excel] En-têtes ligne {header_row}")
                break
        except Exception:
            continue

    if df is None:
        print(f"[WARN] Format Excel non reconnu — vérifier {path.name}")
        return pd.DataFrame(columns=COLONNES_LABO)

    df["source_fichier"] = path.name
    df = _normaliser(df)

    print(f"[Labo Excel] {len(df)} analyses extraites")
    return df


def parse_labo_folder(folder: str) -> pd.DataFrame:
    """
    Parse tous les fichiers Excel labo dans un dossier.
    Fusionne et trie par date.
    """
    folder = Path(folder)
    fichiers = sorted(folder.glob("*.xlsx")) + sorted(folder.glob("*.xls"))

    if not fichiers:
        print(f"[WARN] Aucun fichier Excel dans {folder}")
        return pd.DataFrame(columns=COLONNES_LABO)

    dfs = []
    for f in fichiers:
        try:
            dfs.append(parse_labo_excel(str(f)))
        except Exception as e:
            print(f"[WARN] Erreur {f.name} : {e}")

    if not dfs:
        return pd.DataFrame(columns=COLONNES_LABO)

    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values("date").drop_duplicates(
        subset=["date", "CML_ID"], keep="last"
    )

    print(f"\n[Labo Folder] Total : {len(df)} analyses | {df['date'].min()} → {df['date'].max()}")
    return df.reset_index(drop=True)


def get_labo_30j(df_labo: pd.DataFrame, date_reference: pd.Timestamp,
                 cml_id: str = None) -> dict:
    """
    Retourne les moyennes labo sur le mois précédant une mesure UT.
    (Labo mensuel → souvent 1 seule analyse dans la fenêtre.)

    Args:
        df_labo        : DataFrame labo complet
        date_reference : date de la mesure UT
        cml_id         : CML concerné (filtre optionnel)
    """
    debut = date_reference - pd.Timedelta(days=35)  # marge 5j

    mask = (df_labo["date"] >= debut) & (df_labo["date"] <= date_reference)
    if cml_id:
        mask &= df_labo["CML_ID"].fillna("").str.contains(cml_id, case=False)

    fenetre = df_labo[mask]

    if len(fenetre) == 0:
        return {}

    stats = {}
    for col in ["pH_labo", "Cl_mgL", "Fe_mgL", "inhib_residuel_mgL",
                "SRB_ufc_mL", "H2S_dissous_mgL"]:
        if col in fenetre.columns:
            vals = fenetre[col].dropna()
            if len(vals) > 0:
                stats[col] = vals.mean()

    return stats


# ── Fonctions utilitaires privées ─────────────────────────────────────────────

def _remap(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme les colonnes selon COLUMN_MAPPING."""
    mapping = {
        col: COLUMN_MAPPING[col.lower().strip()]
        for col in df.columns
        if col.lower().strip() in COLUMN_MAPPING
    }
    return df.rename(columns=mapping)


def _normaliser(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les types et valeurs."""
    # Date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

    # Numériques
    for col in ["pH_labo", "Cl_mgL", "Fe_mgL", "inhib_residuel_mgL",
                "SRB_ufc_mL", "H2S_dissous_mgL"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".").str.extract(r"([\d.]+)")[0],
                errors="coerce"
            )

    # Seuils physiologiques plausibles
    if "pH_labo" in df.columns:
        df.loc[~df["pH_labo"].between(0, 14), "pH_labo"] = np.nan
    if "Cl_mgL" in df.columns:
        df.loc[df["Cl_mgL"] > 100_000, "Cl_mgL"] = np.nan
    if "Fe_mgL" in df.columns:
        df.loc[df["Fe_mgL"] > 1_000, "Fe_mgL"] = np.nan

    # Supprimer lignes sans date ni pH ni Cl
    df = df.dropna(subset=["date"], how="all")

    # Ajouter colonnes manquantes
    for col in COLONNES_LABO:
        if col not in df.columns:
            df[col] = np.nan

    return df[COLONNES_LABO]
