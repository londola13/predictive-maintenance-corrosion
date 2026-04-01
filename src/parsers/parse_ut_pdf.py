"""
parse_ut_pdf.py
---------------
Parser pour rapports d'inspection par ultrasons (UT).
Supporte 2 formats courants :
  - Format A : tableaux structurés (pdfplumber)
  - Format B : texte libre avec regex (si tableaux mal formatés)

Usage à COTCO :
    df_ut = parse_ut_report("data/enterprise/ut_reports/UT_2024_Q1.pdf")
    df_ut = parse_ut_folder("data/enterprise/ut_reports/")
"""

import re
import pandas as pd
from pathlib import Path

try:
    import pdfplumber
    PDFPLUMBER_OK = True
except ImportError:
    PDFPLUMBER_OK = False
    print("[WARN] pdfplumber non installé — pip install pdfplumber")


# Colonnes de sortie standardisées
COLONNES_UT = [
    "CML_ID", "date", "t_mm", "t_nominal_mm", "t_min_mm",
    "inspecteur", "technique", "equipement", "notes", "source_fichier"
]

# Patterns regex pour format texte libre
PATTERNS_REGEX = {
    "CML_ID":       r"CML[- ]?(\w+[-]\w+)",
    "t_mm":         r"(?:épaisseur|thickness|t\s*=)\s*([\d.,]+)\s*mm",
    "t_nominal_mm": r"(?:nominale?|nominal)\s*[:=]\s*([\d.,]+)\s*mm",
    "date":         r"(?:date|Date)\s*[:=]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    "inspecteur":   r"(?:inspecteur|inspector)\s*[:=]?\s*([A-Za-z\s]+?)(?:\n|$)",
}


def parse_ut_report(path: str) -> pd.DataFrame:
    """
    Parse un rapport UT PDF.
    Essaie d'abord le format tableau (pdfplumber),
    puis bascule sur regex si le tableau échoue.
    """
    path = Path(path)
    print(f"[UT PDF] Lecture : {path.name}")

    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {path}")

    df = None

    # Tentative 1 — format tableau structuré
    if PDFPLUMBER_OK:
        df = _parse_tableau(path)

    # Tentative 2 — format texte libre
    if df is None or len(df) == 0:
        print(f"[UT PDF] Tableau non détecté → mode regex")
        df = _parse_regex(path)

    if df is None or len(df) == 0:
        print(f"[WARN] Aucune donnée extraite de {path.name}")
        return pd.DataFrame(columns=COLONNES_UT)

    df["source_fichier"] = path.name
    df = _normaliser(df)

    print(f"[UT PDF] {len(df)} mesures extraites")
    return df


def parse_ut_folder(folder: str) -> pd.DataFrame:
    """
    Parse tous les rapports UT dans un dossier.
    Fusionne et déduplique les mesures.
    """
    folder = Path(folder)
    pdfs = sorted(folder.glob("*.pdf"))

    if not pdfs:
        print(f"[WARN] Aucun PDF dans {folder}")
        return pd.DataFrame(columns=COLONNES_UT)

    dfs = []
    for pdf in pdfs:
        try:
            dfs.append(parse_ut_report(str(pdf)))
        except Exception as e:
            print(f"[WARN] Erreur {pdf.name} : {e}")

    if not dfs:
        return pd.DataFrame(columns=COLONNES_UT)

    df = pd.concat(dfs, ignore_index=True)

    # Dédupliquer : garder la mesure la plus récente par CML
    df = df.sort_values("date").drop_duplicates(
        subset=["CML_ID", "date"], keep="last"
    )

    print(f"\n[UT Folder] Total : {len(df)} mesures | {df['CML_ID'].nunique()} CMLs")
    return df.reset_index(drop=True)


# ── Parsers internes ──────────────────────────────────────────────────────────

def _parse_tableau(path: Path) -> pd.DataFrame | None:
    """
    Extrait les tableaux UT via pdfplumber.
    Adapte les noms de colonnes au format COTCO.
    """
    MAPPING_COLONNES = {
        # Noms courants en rapports UT francophones/anglophones
        "cml": "CML_ID", "cml_id": "CML_ID", "point": "CML_ID",
        "épaisseur mesurée": "t_mm", "measured": "t_mm",
        "thickness": "t_mm", "t (mm)": "t_mm", "t mesurée": "t_mm",
        "nominale": "t_nominal_mm", "nominal": "t_nominal_mm",
        "minimale": "t_min_mm", "minimum": "t_min_mm",
        "date": "date", "date inspection": "date",
        "inspecteur": "inspecteur", "inspector": "inspecteur",
        "technique": "technique", "méthode": "technique",
        "équipement": "equipement", "equipment": "equipement",
        "remarques": "notes", "comments": "notes",
    }

    toutes_lignes = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Ligne 0 = en-têtes
                headers = [
                    str(h).strip().lower() if h else f"col_{i}"
                    for i, h in enumerate(table[0])
                ]

                # Vérifier si c'est un tableau UT (contient au moins t_mm ou CML)
                headers_mapped = [MAPPING_COLONNES.get(h, h) for h in headers]
                if "t_mm" not in headers_mapped and "CML_ID" not in headers_mapped:
                    continue

                for row in table[1:]:
                    if not any(row):
                        continue
                    ligne = {}
                    for h_orig, h_std, val in zip(headers, headers_mapped, row):
                        if val:
                            ligne[h_std] = str(val).strip()
                    toutes_lignes.append(ligne)

    if not toutes_lignes:
        return None

    return pd.DataFrame(toutes_lignes)


def _parse_regex(path: Path) -> pd.DataFrame:
    """
    Extrait les mesures UT via expressions régulières (texte libre).
    Utilisé si le PDF ne contient pas de tableaux structurés.
    """
    if not PDFPLUMBER_OK:
        return pd.DataFrame(columns=COLONNES_UT)

    with pdfplumber.open(path) as pdf:
        texte = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )

    lignes = []

    # Chercher les blocs de texte par CML
    blocs = re.split(r"(?=CML[- ]?\w+)", texte, flags=re.IGNORECASE)

    for bloc in blocs:
        if not bloc.strip():
            continue
        ligne = {}
        for champ, pattern in PATTERNS_REGEX.items():
            match = re.search(pattern, bloc, re.IGNORECASE)
            if match:
                ligne[champ] = match.group(1).strip()

        if "t_mm" in ligne:  # au moins une épaisseur trouvée
            lignes.append(ligne)

    return pd.DataFrame(lignes) if lignes else pd.DataFrame(columns=COLONNES_UT)


def _normaliser(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les types et valeurs du DataFrame UT."""
    # Épaisseurs en float
    for col in ["t_mm", "t_nominal_mm", "t_min_mm"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".")
                .str.extract(r"([\d.]+)")[0]
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Dates
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

    # Valeurs impossibles
    if "t_mm" in df.columns:
        df = df[df["t_mm"].between(1, 50)]   # épaisseurs réalistes

    # Ajouter colonnes manquantes
    for col in COLONNES_UT:
        if col not in df.columns:
            df[col] = None

    return df[COLONNES_UT]
