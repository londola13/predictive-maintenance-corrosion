"""
Pipeline ML — Maintenance Prédictive de la Corrosion
Projet M2 ENSPD Douala — Monitoring Detar Plus + HX711 + ESP32

Étapes :
  A. Chargement et nettoyage du signal
  B. Compensation thermique
  C. Feature engineering
  D. Détection du temps d'adsorption de l'inhibiteur (changepoint)
  E. Entraînement XGBoost (CR + RUL)
  F. Alertes

Usage :
  python corrosion_pipeline.py --csv data/run1.csv --mode train
  python corrosion_pipeline.py --csv data/run4.csv --mode predict --model models/xgb_cr.pkl
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb
import joblib
import warnings
warnings.filterwarnings("ignore")

# ── Constantes physiques ──────────────────────────────────────────────────────
RHO_FER   = 1.0e-7   # résistivité électrique du fer (Ω·m)
L_FIL     = 1.1      # longueur du fil (m)
ALPHA_FER = 6.5e-3   # coefficient thermique de résistance du fer (1/°C)
T_REF     = 25.0     # température de référence pour compensation (°C)
HEURES_PAR_AN = 8760.0

# ── Paramètres HX711 / pont ───────────────────────────────────────────────────
R1     = 10.0
R2     = 10.0
R_REF  = 0.5
R_SERIE = 100.0

# ─────────────────────────────────────────────────────────────────────────────
# A. CHARGEMENT ET NETTOYAGE
# ─────────────────────────────────────────────────────────────────────────────

def charger_csv(path: str) -> pd.DataFrame:
    """Charge le CSV produit par l'ESP32."""
    df = pd.read_csv(
        path,
        sep=";",
        names=["timestamp_s", "vdiff_v", "rx_ohm", "temp_c", "delta_r_per_h"],
        comment="#"
    )
    # Supprimer la ligne d'en-tête si présente
    df = df[pd.to_numeric(df["timestamp_s"], errors="coerce").notna()].copy()
    df = df.astype({
        "timestamp_s":   float,
        "vdiff_v":       float,
        "rx_ohm":        float,
        "temp_c":        float,
        "delta_r_per_h": float,
    })
    df["timestamp_h"] = df["timestamp_s"] / 3600.0
    df = df.sort_values("timestamp_s").reset_index(drop=True)
    return df


def nettoyer_signal(df: pd.DataFrame, fenetre: int = 5) -> pd.DataFrame:
    """
    Double nettoyage :
      1. Suppression des outliers (IQR sur rx_ohm)
      2. Lissage Savitzky-Golay (préserve mieux les pentes que la moyenne mobile)
    """
    # Outliers IQR
    Q1 = df["rx_ohm"].quantile(0.05)
    Q3 = df["rx_ohm"].quantile(0.95)
    IQR = Q3 - Q1
    mask = (df["rx_ohm"] >= Q1 - 3 * IQR) & (df["rx_ohm"] <= Q3 + 3 * IQR)
    n_outliers = (~mask).sum()
    if n_outliers > 0:
        print(f"  [nettoyage] {n_outliers} outliers supprimés")
    df = df[mask].copy().reset_index(drop=True)

    # Savitzky-Golay (polynomial order=2, window=fenetre — doit être impair)
    if len(df) >= fenetre:
        df["rx_lisse"] = savgol_filter(df["rx_ohm"], window_length=fenetre, polyorder=2)
    else:
        df["rx_lisse"] = df["rx_ohm"]

    # Température : simple moyenne mobile (pas besoin de préserver les pentes)
    df["temp_lisse"] = df["temp_c"].rolling(window=3, min_periods=1, center=True).mean()

    return df


# ─────────────────────────────────────────────────────────────────────────────
# B. COMPENSATION THERMIQUE
# ─────────────────────────────────────────────────────────────────────────────

def compenser_thermique(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retire l'effet de la température sur la résistance du fil.

    La résistivité du fer varie linéairement avec T :
        R(T) = R0 × (1 + α × (T - T_ref))

    Donc :
        R_corr(t) = R(t) / (1 + α × (T(t) - T_ref))

    R_corr ne dépend plus que de la corrosion, pas de la température.
    """
    df["rx_corr"] = df["rx_lisse"] / (1.0 + ALPHA_FER * (df["temp_lisse"] - T_REF))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# C. FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def rayon_depuis_resistance(R_ohm: pd.Series) -> pd.Series:
    """r(t) = sqrt(ρ·L / (π·R(t)))  en mètres"""
    return np.sqrt(RHO_FER * L_FIL / (np.pi * R_ohm))


def calculer_CR(df: pd.DataFrame) -> pd.DataFrame:
    """
    Taux de corrosion en mm/an à partir des variations de rayon.

    CR = |dr/dt| × 8760 × 1000
      dr/dt en m/h → CR en mm/an
    """
    df["rayon_m"] = rayon_depuis_resistance(df["rx_corr"])
    # Dérivée numérique (différences finies centrées)
    dt_h = df["timestamp_h"].diff().fillna(0.1)
    dr_h = df["rayon_m"].diff().fillna(0)
    df["dr_dt_m_per_h"] = dr_h / dt_h.replace(0, np.nan)
    df["CR_mm_an"] = np.abs(df["dr_dt_m_per_h"]) * HEURES_PAR_AN * 1000.0
    # Lisser le CR (très bruité sur dérivée brute)
    if len(df) >= 5:
        df["CR_lisse"] = savgol_filter(
            df["CR_mm_an"].fillna(0), window_length=5, polyorder=2
        ).clip(0)
    else:
        df["CR_lisse"] = df["CR_mm_an"].clip(0)
    return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Construit les features temporelles pour XGBoost."""
    # Deltas de résistance (fenêtres glissantes en indices, 1 indice = 10 min)
    df["delta_R_1h"]  = df["rx_corr"].diff(6)    # 6 × 10 min = 1h
    df["delta_R_6h"]  = df["rx_corr"].diff(36)   # 36 × 10 min = 6h

    # Vitesse de corrosion sur 1h
    dt_1h = df["timestamp_h"].diff(6).replace(0, np.nan)
    df["vitesse_CR_1h"] = np.abs(df["rx_corr"].diff(6) / dt_1h) * HEURES_PAR_AN * 1000.0

    # Tendance (pente linéaire sur 6h glissant)
    def pente_locale(series, n=36):
        pentes = [np.nan] * n
        x = np.arange(n)
        for i in range(n, len(series)):
            y = series.iloc[i-n:i].values
            try:
                pentes.append(np.polyfit(x, y, 1)[0])
            except Exception:
                pentes.append(0.0)
        return pd.Series(pentes, index=series.index)

    df["tendance_6h"] = pente_locale(df["rx_corr"])

    # Température moyenne 6h
    df["temp_moy_6h"] = df["temp_lisse"].rolling(window=36, min_periods=1).mean()

    # Temps depuis début du run
    df["temps_immersion_h"] = df["timestamp_h"] - df["timestamp_h"].iloc[0]

    # Valeur de R au début (référence)
    R0 = df["rx_corr"].iloc[0]
    df["delta_R_absolu"] = df["rx_corr"] - R0

    # Ratio de corrosion (section perdue)
    r0 = rayon_depuis_resistance(pd.Series([R0])).iloc[0]
    df["rayon_m"] = rayon_depuis_resistance(df["rx_corr"])
    df["section_perdue_pct"] = (1.0 - (df["rayon_m"] / r0) ** 2) * 100.0

    return df


def calculer_RUL(df: pd.DataFrame, r_critique_fraction: float = 0.1) -> pd.DataFrame:
    """
    RUL = temps restant avant que le rayon atteigne r_critique.
    r_critique = r0 × r_critique_fraction (10% du rayon initial = rupture imminente)

    Si le run va jusqu'à la rupture : RUL calculé depuis la fin.
    Si non : RUL estimé par extrapolation linéaire de la tendance.
    """
    r0 = df["rayon_m"].iloc[0]
    r_crit = r0 * r_critique_fraction

    # Chercher si la rupture est atteinte dans ce run
    rupture_idx = df[df["rayon_m"] <= r_crit].index
    if len(rupture_idx) > 0:
        t_rupture_h = df.loc[rupture_idx[0], "timestamp_h"]
        df["RUL_h"] = (t_rupture_h - df["timestamp_h"]).clip(lower=0)
        print(f"  [RUL] Rupture détectée à t = {t_rupture_h:.1f}h")
    else:
        # Extrapolation : RUL = (r_actuel - r_crit) / |dr/dt|
        df["RUL_h"] = (
            (df["rayon_m"] - r_crit) / np.abs(df["dr_dt_m_per_h"].replace(0, np.nan))
        ).clip(lower=0)
        print("  [RUL] Pas de rupture dans ce run — RUL extrapolé")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# D. DÉTECTION TEMPS D'ADSORPTION DE L'INHIBITEUR (CHANGEPOINT)
# ─────────────────────────────────────────────────────────────────────────────

def detecter_adsorption(df: pd.DataFrame, seuil_reduction: float = 0.3) -> dict:
    """
    Détecte le moment où l'inhibiteur (AC PROTECT 106) s'adsorbe sur le fil.
    Méthode : chercher la première fenêtre de 6 mesures consécutives où
    la vitesse CR_lisse descend de plus de seuil_reduction × CR_initial.

    Retourne un dict avec t_adsorption_h et efficacite_pct.
    """
    if "CR_lisse" not in df.columns or df["CR_lisse"].max() < 1e-6:
        return {"t_adsorption_h": None, "efficacite_pct": None}

    CR_initial = df["CR_lisse"].iloc[:6].mean()  # baseline 1h
    seuil      = CR_initial * (1.0 - seuil_reduction)
    fenetre    = 6  # 6 mesures = 1h

    for i in range(fenetre, len(df)):
        CR_fenetre = df["CR_lisse"].iloc[i-fenetre:i].mean()
        if CR_fenetre <= seuil:
            t_ads = df["timestamp_h"].iloc[i - fenetre]
            CR_final = df["CR_lisse"].iloc[i:i+fenetre].mean()
            eta = (1.0 - CR_final / CR_initial) * 100.0
            print(f"  [inhibiteur] Adsorption détectée à t = {t_ads:.2f}h | η = {eta:.1f}%")
            return {
                "t_adsorption_h":   round(t_ads, 3),
                "efficacite_pct":   round(eta, 1),
                "CR_avant_mm_an":   round(CR_initial, 4),
                "CR_apres_mm_an":   round(CR_final, 4),
            }

    print("  [inhibiteur] Aucun changement de pente détecté (seuil non atteint)")
    return {"t_adsorption_h": None, "efficacite_pct": None}


# ─────────────────────────────────────────────────────────────────────────────
# E. XGBOOST — ENTRAÎNEMENT ET PRÉDICTION
# ─────────────────────────────────────────────────────────────────────────────

FEATURES = [
    "rx_corr",
    "delta_R_1h",
    "delta_R_6h",
    "vitesse_CR_1h",
    "tendance_6h",
    "temp_lisse",
    "temp_moy_6h",
    "temps_immersion_h",
    "delta_R_absolu",
    "section_perdue_pct",
]

PARAMS_XGB = {
    "n_estimators":      500,
    "max_depth":         4,
    "learning_rate":     0.05,
    "subsample":         0.8,
    "colsample_bytree":  0.8,
    "reg_alpha":         0.1,   # L1
    "reg_lambda":        1.0,   # L2
    "min_child_weight":  3,
    "random_state":      42,
    "n_jobs":            -1,
}


def preparer_dataset(dfs: list[pd.DataFrame], target: str) -> tuple:
    """Concatène plusieurs DataFrames de runs et retourne X, y propres."""
    df_all = pd.concat(dfs, ignore_index=True)
    df_all = df_all.dropna(subset=FEATURES + [target])
    X = df_all[FEATURES]
    y = df_all[target]
    return X, y


def entrainer_modele(X: pd.DataFrame, y: pd.Series, target_name: str) -> xgb.XGBRegressor:
    """Walk-forward cross-validation + entraînement final."""
    tscv = TimeSeriesSplit(n_splits=4)
    scores = {"MAE": [], "RMSE": [], "R2": []}

    print(f"\n  [XGBoost] Entraînement — cible : {target_name}")
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        m = xgb.XGBRegressor(**PARAMS_XGB)
        m.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        y_pred = m.predict(X_val)
        scores["MAE"].append(mean_absolute_error(y_val, y_pred))
        scores["RMSE"].append(np.sqrt(mean_squared_error(y_val, y_pred)))
        scores["R2"].append(r2_score(y_val, y_pred))
        print(f"    Fold {fold+1} | MAE={scores['MAE'][-1]:.4f} "
              f"RMSE={scores['RMSE'][-1]:.4f} R²={scores['R2'][-1]:.4f}")

    print(f"  → Moyenne : MAE={np.mean(scores['MAE']):.4f} "
          f"RMSE={np.mean(scores['RMSE']):.4f} R²={np.mean(scores['R2']):.4f}")

    # Entraînement final sur tout le dataset
    modele_final = xgb.XGBRegressor(**PARAMS_XGB)
    modele_final.fit(X, y)
    return modele_final, scores


def sauvegarder_modele(modele, path: str):
    joblib.dump(modele, path)
    print(f"  [modèle] Sauvegardé → {path}")


def charger_modele(path: str):
    return joblib.load(path)


# ─────────────────────────────────────────────────────────────────────────────
# F. ALERTES
# ─────────────────────────────────────────────────────────────────────────────

SEUILS = {
    "CR_mm_an":  {"info": 1.0,  "warning": 5.0,  "critique": 15.0},
    "RUL_h":     {"info": 24.0, "warning": 8.0,  "critique": 2.0},
}


def evaluer_alertes(CR_pred: float, RUL_pred: float) -> dict:
    """Retourne le niveau d'alerte et la dose recommandée d'AC PROTECT 106."""
    niveau = "OK"
    dose_pct = 0.0

    if CR_pred > SEUILS["CR_mm_an"]["critique"] or RUL_pred < SEUILS["RUL_h"]["critique"]:
        niveau  = "CRITIQUE"
        dose_pct = 1.0     # 1% v/v
    elif CR_pred > SEUILS["CR_mm_an"]["warning"] or RUL_pred < SEUILS["RUL_h"]["warning"]:
        niveau  = "WARNING"
        dose_pct = 0.5
    elif CR_pred > SEUILS["CR_mm_an"]["info"] or RUL_pred < SEUILS["RUL_h"]["info"]:
        niveau  = "INFO"
        dose_pct = 0.1

    return {
        "niveau":        niveau,
        "dose_AC106_pct": dose_pct,
        "CR_pred":       round(CR_pred, 4),
        "RUL_pred_h":    round(RUL_pred, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# G. VISUALISATION
# ─────────────────────────────────────────────────────────────────────────────

def visualiser_run(df: pd.DataFrame, titre: str = "Run"):
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    t = df["timestamp_h"]

    axes[0].plot(t, df["rx_ohm"],   alpha=0.3, label="R brute", color="gray")
    axes[0].plot(t, df["rx_corr"],  label="R compensée (thermique)", color="royalblue")
    axes[0].set_ylabel("Résistance (Ω)")
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    axes[1].plot(t, df["CR_lisse"], label="CR (mm/an)", color="crimson")
    axes[1].set_ylabel("Taux de corrosion (mm/an)")
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    axes[2].plot(t, df["temp_lisse"], label="Température (°C)", color="orange")
    axes[2].set_ylabel("Température (°C)")
    axes[2].set_xlabel("Temps (h)")
    axes[2].legend(); axes[2].grid(True, alpha=0.3)

    fig.suptitle(titre, fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"plots/{titre.replace(' ', '_')}.png", dpi=150)
    plt.show()
    print(f"  [plot] Sauvegardé → plots/{titre.replace(' ', '_')}.png")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def traiter_run(path_csv: str, ph_run: float = 1.0,
                dose_inhibiteur: float = 0.0) -> pd.DataFrame:
    """Pipeline complet sur un fichier CSV de run."""
    print(f"\n{'='*60}")
    print(f"  Run : {path_csv}  |  pH={ph_run}  |  AC106={dose_inhibiteur}% v/v")
    print(f"{'='*60}")

    df = charger_csv(path_csv)
    print(f"  {len(df)} mesures chargées ({df['timestamp_h'].max():.1f}h)")

    df = nettoyer_signal(df)
    df = compenser_thermique(df)
    df = calculer_CR(df)
    df = feature_engineering(df)
    df = calculer_RUL(df)

    # Métadonnées run
    df["ph_run"]           = ph_run
    df["dose_inhibiteur"]  = dose_inhibiteur

    return df


def main():
    import os
    os.makedirs("models", exist_ok=True)
    os.makedirs("plots",  exist_ok=True)

    parser = argparse.ArgumentParser(description="Pipeline Corrosion ML")
    parser.add_argument("--csv",   type=str, required=True, help="Fichier CSV du run")
    parser.add_argument("--mode",  type=str, default="train",
                        choices=["train", "predict", "analyse"])
    parser.add_argument("--model", type=str, default="models/xgb_cr.pkl")
    parser.add_argument("--ph",    type=float, default=1.0)
    parser.add_argument("--dose",  type=float, default=0.0,
                        help="Dose AC PROTECT 106 (% v/v)")
    args = parser.parse_args()

    df = traiter_run(args.csv, ph_run=args.ph, dose_inhibiteur=args.dose)

    if args.mode == "analyse":
        # Analyse seule (pas de ML) — utile pendant la phase de collecte
        print(f"\n  CR moyen       : {df['CR_lisse'].mean():.4f} mm/an")
        print(f"  CR max         : {df['CR_lisse'].max():.4f} mm/an")
        print(f"  RUL estimé     : {df['RUL_h'].iloc[-1]:.2f} h")
        print(f"  Section perdue : {df['section_perdue_pct'].iloc[-1]:.2f}%")
        if args.dose > 0:
            ads = detecter_adsorption(df)
            print(f"  Adsorption     : {ads}")
        visualiser_run(df, titre=f"Run {args.csv}")

    elif args.mode == "train":
        print("\n  Mode entraînement (run unique) — pour multi-runs, adapter le script")
        X, y_cr  = preparer_dataset([df], "CR_lisse")
        X, y_rul = preparer_dataset([df], "RUL_h")

        modele_cr,  _ = entrainer_modele(X, y_cr,  "CR (mm/an)")
        modele_rul, _ = entrainer_modele(X, y_rul, "RUL (h)")

        sauvegarder_modele(modele_cr,  "models/xgb_cr.pkl")
        sauvegarder_modele(modele_rul, "models/xgb_rul.pkl")
        visualiser_run(df, titre="Run entraînement")

    elif args.mode == "predict":
        modele_cr  = charger_modele("models/xgb_cr.pkl")
        modele_rul = charger_modele("models/xgb_rul.pkl")

        df_clean = df.dropna(subset=FEATURES)
        X = df_clean[FEATURES]

        cr_pred  = modele_cr.predict(X)
        rul_pred = modele_rul.predict(X)

        df_clean = df_clean.copy()
        df_clean["CR_pred"]  = cr_pred
        df_clean["RUL_pred"] = rul_pred

        # Alerte sur la dernière mesure
        alerte = evaluer_alertes(cr_pred[-1], rul_pred[-1])
        print(f"\n  ── ALERTE ──────────────────────────────")
        print(f"  Niveau    : {alerte['niveau']}")
        print(f"  CR prédit : {alerte['CR_pred']} mm/an")
        print(f"  RUL prédit: {alerte['RUL_pred_h']} h")
        print(f"  Dose AC106: {alerte['dose_AC106_pct']}% v/v")
        print(f"  ────────────────────────────────────────")

        df_clean.to_csv("output/predictions.csv", sep=";", index=False)
        visualiser_run(df_clean, titre="Run prédiction")


if __name__ == "__main__":
    main()
