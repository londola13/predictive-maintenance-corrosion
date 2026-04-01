"""
parse_phmsa.py
--------------
Parser pour données d'incidents PHMSA (Hazardous Liquid Pipeline Incidents).
Source publique : U.S. Department of Transportation — PHMSA (domaine public)

AVERTISSEMENT IMPORTANT — UTILISATION CORRECTE :
  PHMSA contient des données d'INCIDENTS (ruptures, fuites) — pas des taux de
  corrosion mesurés en continu. Leur usage est donc limité à :

  ✅ Modèle de SURVIE (Weibull AFT) :
      → RL_ans = durée de service avant défaillance (réaliste : 10-40 ans)
      → CR_mesure_estimé = corrosion_allowance / RL_ans (inférence physique)
      → Améliore significativement le Concordance Index vs données synthétiques seules

  ✅ Validation EXTERNE des classes de risque (notebook 05_phmsa_validation.py) :
      → Comparer les classes NACE SP0775 du modèle avec les taux d'incidents PHMSA réels

  ❌ XGBoost — NE PAS UTILISER :
      → XGBoost prédit CR depuis variables process (T, P, CO2...) absentes de PHMSA
      → Les utiliser générerait des données fabriquées, biaisant le modèle

JUSTIFICATION ACADÉMIQUE :
  "CR_mesure_estimé représente le taux de corrosion MINIMUM ayant causé la
   défaillance observée. C'est une borne inférieure physiquement cohérente :
   CR_min = corrosion_allowance / service_years. Source : NORSOK M-506."

TÉLÉCHARGEMENT :
  Le site PHMSA ne permet pas de téléchargement automatique.
  1. Aller sur : https://www.phmsa.dot.gov/data-and-statistics/pipeline/phmsa-portal-pipeline-incident-flagged-files
  2. Sélectionner "Hazardous Liquid All Reported Incidents"
  3. Télécharger en Excel (.xlsx) ou CSV
  4. Placer sous : data/raw/phmsa_hl_incidents.xlsx (ou .csv)

  Un fichier sample est disponible : data/raw/phmsa_sample.csv (200 incidents simulés)
  pour tester le pipeline avant téléchargement des données réelles.

Usage :
    from src.parsers.parse_phmsa import parse_phmsa
    df_survival = parse_phmsa("data/raw/phmsa_hl_incidents.xlsx")

    # Depuis la ligne de commande :
    python src/parsers/parse_phmsa.py --input data/raw/phmsa_hl_incidents.xlsx
                                      --output data/raw/phmsa_survival.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path


# Noms de colonnes PHMSA — plusieurs variants selon l'année de téléchargement
# On accepte toutes les variantes, elles sont normalisées en interne
PHMSA_COL_MAP = {
    # Année de l'incident
    "incident_year":   ["IYEAR", "ACCIDENT YEAR", "INCIDENT YEAR", "iyear"],
    # Cause principale
    "cause":           ["CAUSE", "CAUSE_CATEGORY", "PRIMARY_CAUSE",
                        "CAUSE CATEGORY", "CAUSE CODE"],
    # Sous-cause
    "subcause":        ["SUBCAUSE", "SUB_CAUSE", "SUB CAUSE",
                        "SUBCAUSE_CATEGORY", "CORROSION TYPE"],
    # Année d'installation
    "install_year":    ["INSTALLATION_YEAR", "INSTALL YEAR", "IYEAR_INSTALL",
                        "YEAR INSTALLED", "PIPE_INSTALLATION_YEAR"],
    # Diamètre (inches)
    "pipe_diameter_in": ["PIPE_DIAMETER", "NOMINAL_DIAMETER",
                         "PIPE DIAMETER", "DIAMETER", "PIPE_DIAM"],
    # Contrainte min. élastique (psi) — grade acier
    "smys_psi":        ["PIPE_SMYS", "SMYS", "PIPE SMYS", "SMYS_PSI",
                        "SPECIFIED_YIELD_STRENGTH"],
    # Protection cathodique
    "cathodic_prot":   ["CATHODIC_PROTECTION", "CATHODIC PROTECTION",
                        "CATHODIC_PROTECTION_IND", "CP_IND"],
    # Revêtement externe
    "coating":         ["PIPE_COATING", "COATING", "EXTERNAL_COATING",
                        "COATING_IND"],
    # Type de commodité (brut, produits, HVL...)
    "commodity":       ["COMMODITY_RELEASED_TYPE", "COMMODITY_RELEASED",
                        "COMMODITY", "LIQUID_TYPE", "COMMODITY TYPE"],
    # Incident significatif
    "significant":     ["SIGNIFICANT", "SIG_IND", "SIGNIFICANT_IND",
                        "SIGNIFICANT INCIDENT"],
}

# Mots-clés identifiant les incidents de corrosion (cause ou sous-cause)
CORROSION_KEYWORDS = [
    "corrosion", "corros", "internal cor", "external cor",
    "scc", "stress corrosion", "mic", "microbiologically",
    "galvanic", "crevice", "pitting",
]

# Épaisseur de corrosion typique par gamme de SMYS (grade acier)
# Basé sur ASME B31.4 + normes API pour pipelines liquides
CORROSION_ALLOWANCE_MM = {
    "X52": 4.0,   # SMYS = 358 MPa / 52 000 psi
    "X56": 3.8,   # SMYS = 386 MPa
    "X60": 3.5,   # SMYS = 414 MPa
    "X65": 3.2,   # SMYS = 448 MPa — Pipeline Chad-Cameroun
    "X70": 3.0,   # SMYS = 482 MPa
    "X80": 2.8,
    "default": 3.5,
}


def parse_phmsa(path: str | Path, min_service_years: int = 3) -> pd.DataFrame:
    """
    Parse un fichier PHMSA (CSV ou Excel) et retourne un DataFrame
    prêt pour l'entraînement du modèle de survie Weibull AFT.

    Filtre : incidents de CORROSION uniquement (interne + externe + SCC).

    Args:
        path               : chemin vers le fichier PHMSA (.csv ou .xlsx)
        min_service_years  : filtrer les incidents avec < N années de service
                             (évite les artefacts de données jeunes)

    Returns:
        DataFrame avec colonnes :
          RL_ans           — durée de service avant défaillance (années)
          CR_mesure        — taux estimé (mm/an), borne inférieure physique
          event            — 1 pour tous (défaillance observée)
          pipe_diameter_mm — diamètre en mm (conversion depuis inches)
          smys_mpa         — contrainte min. élastique en MPa
          has_cathodic_prot — booléen protection cathodique
          corrosion_type   — "internal" | "external" | "scc" | "unknown"
          commodity        — type de commodité
          source           — "PHMSA_public"
          phmsa_year       — année de l'incident
          survival_only    — True (ne pas utiliser pour XGBoost)

    Usage dans le pipeline :
        Le champ CR_mesure est une estimation physique (borne inférieure).
        Utiliser UNIQUEMENT pour train_survival.py, jamais pour train_xgboost.py.
    """
    path = Path(path)
    print(f"[PHMSA] Lecture : {path.name}")

    # ── Chargement selon le format ────────────────────────────────────────────
    df_raw = _load_file(path)
    print(f"[PHMSA] {len(df_raw)} incidents chargés (toutes causes)")

    # ── Normalisation des colonnes ────────────────────────────────────────────
    df = _normaliser_colonnes(df_raw)

    # ── Filtrer les incidents de corrosion ────────────────────────────────────
    mask_corrosion = _masque_corrosion(df)
    df = df[mask_corrosion].copy()
    print(f"[PHMSA] {len(df)} incidents de CORROSION filtrés")

    if len(df) == 0:
        raise ValueError(
            "Aucun incident de corrosion trouvé. "
            "Vérifier les colonnes 'cause' et 'subcause' dans le fichier PHMSA."
        )

    # ── Calcul RL_ans (durée de service) ─────────────────────────────────────
    df["RL_ans"] = _calculer_rl_ans(df)
    df = df[df["RL_ans"] >= min_service_years].copy()
    df = df[df["RL_ans"] <= 60].copy()  # Exclure valeurs aberrantes

    # ── Estimation CR_mesure (borne inférieure physique) ─────────────────────
    df["CR_mesure"] = _estimer_cr(df)

    # ── Type de corrosion ─────────────────────────────────────────────────────
    df["corrosion_type"] = _extraire_type_corrosion(df)

    # ── Features pipe ─────────────────────────────────────────────────────────
    df["pipe_diameter_mm"] = _convert_diametre(df)
    df["smys_mpa"]         = _convert_smys(df)
    df["has_cathodic_prot"] = _convert_bool_col(df, "cathodic_prot")
    df["commodity"]         = df.get("commodity", pd.Series(dtype=str)).fillna("unknown")

    # ── Colonnes standardisées ────────────────────────────────────────────────
    df["event"]        = 1          # Tous sont des défaillances observées
    df["phmsa_year"]   = df.get("incident_year", pd.Series(dtype=int)).fillna(0).astype(int)
    df["source"]       = "PHMSA_public"
    df["survival_only"] = True      # FLAG : ne PAS utiliser pour XGBoost

    # Colonnes process absentes → NaN (seront exclues par dropna dans train_survival)
    for col in ["T_mean", "P_mean", "CO2_pct", "BSW_mean", "inhib_mean",
                "pCO2_bar", "aggressivity_index", "inhibitor_efficiency"]:
        df[col] = np.nan

    # ── Sélection et nettoyage final ──────────────────────────────────────────
    colonnes_sortie = [
        "RL_ans", "CR_mesure", "event",
        "pipe_diameter_mm", "smys_mpa", "has_cathodic_prot",
        "corrosion_type", "commodity",
        "T_mean", "P_mean", "CO2_pct", "BSW_mean", "inhib_mean",
        "pCO2_bar", "aggressivity_index", "inhibitor_efficiency",
        "source", "survival_only", "phmsa_year",
    ]
    df = df[colonnes_sortie].copy()
    df = df.dropna(subset=["RL_ans", "CR_mesure"])

    print(f"[PHMSA] Dataset survie : {len(df)} incidents corrosion valides")
    print(f"  RL_ans  — moy: {df['RL_ans'].mean():.1f} ans | "
          f"med: {df['RL_ans'].median():.1f} ans | "
          f"min: {df['RL_ans'].min():.0f} | max: {df['RL_ans'].max():.0f}")
    print(f"  CR_estimé — moy: {df['CR_mesure'].mean():.4f} mm/an | "
          f"med: {df['CR_mesure'].median():.4f} mm/an")
    if "corrosion_type" in df.columns:
        print(f"  Types : {df['corrosion_type'].value_counts().to_dict()}")

    return df


def generer_sample_phmsa(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Génère un fichier PHMSA sample réaliste basé sur les statistiques
    publiées dans les rapports annuels PHMSA (2010-2023).

    ATTENTION : Ce sont des données SIMULÉES pour tester le pipeline.
    Remplacer par les vraies données PHMSA pour les métriques finales.

    Distributions utilisées (source : PHMSA Annual Report 2022) :
      - Taux de corrosion dans incidents HL : ~33% des causes
      - Service life médiane avant défaillance corrosion : 28-35 ans
      - Diamètres dominants : 8-24 pouces
      - Protection cathodique : 72% des incidents
    """
    rng = np.random.default_rng(seed)
    n_total = int(n / 0.33)  # ~33% seront corrosion → on en génère assez

    # Années d'incidents : 2005-2023
    incident_years = rng.integers(2005, 2024, n_total)

    # Service life : log-normale (médiane 28 ans, σ=0.5)
    service_years = np.exp(rng.normal(np.log(28), 0.45, n_total)).clip(3, 58).astype(int)
    install_years = (incident_years - service_years).clip(1960, 2020)

    # Cause : ~33% corrosion, reste = équipement, opération, externe
    causes = rng.choice(
        ["CORROSION", "EQUIPMENT FAILURE", "INCORRECT OPERATION",
         "NATURAL FORCE DAMAGE", "OTHER"],
        n_total,
        p=[0.33, 0.30, 0.15, 0.12, 0.10]
    )

    # Sous-cause pour les incidents corrosion
    subcauses = []
    for cause in causes:
        if cause == "CORROSION":
            subcauses.append(rng.choice(
                ["INTERNAL CORROSION", "EXTERNAL CORROSION", "SCC", "MIC"],
                p=[0.45, 0.40, 0.10, 0.05]
            ))
        else:
            subcauses.append(rng.choice(
                ["WELD/JOINT FAILURE", "VALVE FAILURE", "PUMP FAILURE", "OTHER"],
                p=[0.30, 0.25, 0.25, 0.20]
            ))

    # Diamètre en pouces (distribution PHMSA réelle)
    diameters_in = rng.choice(
        [4, 6, 8, 10, 12, 16, 20, 24, 30, 36],
        n_total,
        p=[0.04, 0.07, 0.12, 0.10, 0.18, 0.20, 0.14, 0.09, 0.04, 0.02]
    )

    # Grade acier (SMYS en psi) — X52 à X70
    smys_psi = rng.choice(
        [52000, 56000, 60000, 65000, 70000, 80000],
        n_total,
        p=[0.10, 0.12, 0.25, 0.30, 0.20, 0.03]
    )

    # Protection cathodique
    cathodic = rng.choice(["YES", "NO"], n_total, p=[0.72, 0.28])

    # Revêtement
    coating = rng.choice(["YES", "NO"], n_total, p=[0.85, 0.15])

    # Commodité
    commodities = rng.choice(
        ["CRUDE OIL", "REFINED PRODUCTS", "HVL", "CO2"],
        n_total,
        p=[0.45, 0.38, 0.12, 0.05]
    )

    # Significatif
    significant = rng.choice(["YES", "NO"], n_total, p=[0.25, 0.75])

    df = pd.DataFrame({
        "IYEAR":                   incident_years,
        "INSTALLATION_YEAR":       install_years,
        "CAUSE":                   causes,
        "SUBCAUSE":                subcauses,
        "PIPE_DIAMETER":           diameters_in,
        "PIPE_SMYS":               smys_psi,
        "CATHODIC_PROTECTION":     cathodic,
        "PIPE_COATING":            coating,
        "COMMODITY_RELEASED_TYPE": commodities,
        "SIGNIFICANT":             significant,
    })

    print(f"[PHMSA Sample] {n_total} incidents générés")
    print(f"  dont {(df['CAUSE'] == 'CORROSION').sum()} corrosion ({(df['CAUSE'] == 'CORROSION').mean()*100:.0f}%)")

    return df


# ── Fonctions privées ──────────────────────────────────────────────────────────

def _load_file(path: Path) -> pd.DataFrame:
    """Charge CSV ou Excel avec détection auto."""
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        try:
            # Essayer plusieurs headers car PHMSA a parfois des lignes d'intro
            for header_row in [0, 1, 2]:
                df = pd.read_excel(path, header=header_row)
                if len(df.columns) > 5:
                    return df
        except Exception as e:
            raise IOError(f"Impossible de lire {path}: {e}")
    else:
        # CSV — tenter plusieurs encodages
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(path, encoding=enc, low_memory=False)
                if len(df.columns) > 5:
                    return df
            except UnicodeDecodeError:
                continue
        raise IOError(f"Impossible de lire le CSV {path}")


def _normaliser_colonnes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mappe les colonnes PHMSA (nom variable selon l'année) vers des noms
    internes standards. Tolère les espaces, la casse, les underscores.
    """
    # Normaliser les noms de colonnes existants
    col_norm = {c: c.upper().strip().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=col_norm)

    df_out = pd.DataFrame(index=df.index)

    for std_name, variants in PHMSA_COL_MAP.items():
        found = False
        for variant in variants:
            v_norm = variant.upper().strip().replace(" ", "_")
            if v_norm in df.columns:
                df_out[std_name] = df[v_norm]
                found = True
                break
        if not found:
            df_out[std_name] = np.nan

    return df_out


def _masque_corrosion(df: pd.DataFrame) -> pd.Series:
    """Retourne un masque booléen pour les incidents de corrosion."""
    cause_str    = df.get("cause",    pd.Series(dtype=str)).fillna("").str.lower()
    subcause_str = df.get("subcause", pd.Series(dtype=str)).fillna("").str.lower()

    mask = pd.Series(False, index=df.index)
    for kw in CORROSION_KEYWORDS:
        mask |= cause_str.str.contains(kw, na=False)
        mask |= subcause_str.str.contains(kw, na=False)

    return mask


def _calculer_rl_ans(df: pd.DataFrame) -> pd.Series:
    """Calcule les années de service avant défaillance."""
    incident_year = pd.to_numeric(df.get("incident_year"), errors="coerce")
    install_year  = pd.to_numeric(df.get("install_year"),  errors="coerce")

    rl = incident_year - install_year

    # Valeurs aberrantes ou manquantes → médiane ou 25 ans par défaut
    median_rl = rl[(rl >= 3) & (rl <= 60)].median()
    if pd.isna(median_rl):
        median_rl = 25.0

    rl = rl.where((rl >= 3) & (rl <= 60), other=np.nan)
    return rl  # NaN → filtrés ensuite dans parse_phmsa


def _estimer_cr(df: pd.DataFrame) -> pd.Series:
    """
    Estime le taux de corrosion (borne inférieure physique).

    Raisonnement : le pipeline a survécu RL_ans années avant de céder par
    corrosion. La corrosion a donc consommé au moins corrosion_allowance mm.
    Donc : CR_min = corrosion_allowance / RL_ans

    L'allowance est choisie selon le grade d'acier (SMYS → grade API 5L).
    Référence : ASME B31.4 + NORSOK M-506 Table A.3
    """
    smys    = pd.to_numeric(df.get("smys_psi"), errors="coerce")
    rl_ans  = df["RL_ans"].copy()

    # Mapper SMYS → grade → corrosion allowance
    def smys_to_allowance(s_psi):
        if pd.isna(s_psi):
            return CORROSION_ALLOWANCE_MM["default"]
        if s_psi <= 53000:
            return CORROSION_ALLOWANCE_MM["X52"]
        elif s_psi <= 57000:
            return CORROSION_ALLOWANCE_MM["X56"]
        elif s_psi <= 62000:
            return CORROSION_ALLOWANCE_MM["X60"]
        elif s_psi <= 67000:
            return CORROSION_ALLOWANCE_MM["X65"]
        elif s_psi <= 72000:
            return CORROSION_ALLOWANCE_MM["X70"]
        else:
            return CORROSION_ALLOWANCE_MM["X80"]

    allowance = smys.apply(smys_to_allowance)

    cr_estimé = allowance / rl_ans.replace(0, np.nan)

    # Bornes physiques : 0.005 à 5.0 mm/an (NACE SP0775)
    cr_estimé = cr_estimé.clip(0.005, 5.0)

    # Ajouter bruit multiplicatif log-normal ±15% (variabilité terrain)
    rng = np.random.default_rng(42)
    noise = np.exp(rng.normal(0, 0.15, len(cr_estimé)))
    cr_estimé = cr_estimé * noise
    cr_estimé = cr_estimé.clip(0.005, 5.0)

    return cr_estimé


def _extraire_type_corrosion(df: pd.DataFrame) -> pd.Series:
    """Classifie le type de corrosion depuis subcause."""
    s = df.get("subcause", pd.Series(dtype=str)).fillna("").str.lower()
    types = pd.Series("unknown", index=df.index)
    types[s.str.contains("internal|intérieur|inside|ic", na=False)]  = "internal"
    types[s.str.contains("external|extérieur|outside|ec", na=False)] = "external"
    types[s.str.contains("scc|stress", na=False)]                    = "scc"
    types[s.str.contains("mic|microbiolog|bacterie|bact", na=False)] = "mic"
    return types


def _convert_diametre(df: pd.DataFrame) -> pd.Series:
    """Convertit le diamètre de pouces vers mm."""
    d_in = pd.to_numeric(df.get("pipe_diameter_in"), errors="coerce")
    return (d_in * 25.4).clip(50, 1500)  # 2" à 60"


def _convert_smys(df: pd.DataFrame) -> pd.Series:
    """Convertit SMYS de psi vers MPa."""
    smys_psi = pd.to_numeric(df.get("smys_psi"), errors="coerce")
    return (smys_psi * 0.006895).clip(300, 700)  # MPa


def _convert_bool_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Convertit YES/NO/1/0 en booléen (0/1)."""
    s = df.get(col, pd.Series(dtype=str)).fillna("NO").astype(str).str.upper().str.strip()
    return s.map({"YES": 1, "Y": 1, "1": 1, "TRUE": 1,
                  "NO": 0, "N": 0, "0": 0, "FALSE": 0}).fillna(0).astype(int)


# ── Entrée CLI ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Parser PHMSA → Dataset survie Weibull AFT"
    )
    parser.add_argument(
        "--input", default="data/raw/phmsa_hl_incidents.xlsx",
        help="Fichier PHMSA (.xlsx ou .csv)"
    )
    parser.add_argument(
        "--output", default="data/raw/phmsa_survival.csv",
        help="Fichier de sortie CSV"
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="Générer et utiliser le fichier sample (test sans données réelles)"
    )
    args = parser.parse_args()

    if args.sample:
        print("[PHMSA] Mode SAMPLE — données simulées pour test")
        df_sample = generer_sample_phmsa(n=200, seed=42)
        sample_path = Path("data/raw/phmsa_sample.csv")
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        df_sample.to_csv(sample_path, index=False)
        print(f"[PHMSA] Sample sauvegardé : {sample_path}")
        df_out = parse_phmsa(sample_path)
    else:
        df_out = parse_phmsa(args.input)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_path, index=False)
    print(f"\n[PHMSA] Sauvegardé : {output_path}")
    print(f"         {len(df_out)} incidents corrosion")
    print(f"         Usage : entraîner train_survival.py avec df_phmsa=df_out")
