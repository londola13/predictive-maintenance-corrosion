"""
train_xgboost.py
----------------
Entraînement XGBoost pour prédiction du taux de corrosion.

Validation : Walk-forward (temporelle) — jamais aléatoire.
Optimisation : Optuna (100 trials).
Interprétabilité : SHAP values.
Benchmark : comparaison vs De Waard seul.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

try:
    import xgboost as xgb
    XGB_OK = True
except ImportError:
    XGB_OK = False
    print("[WARN] xgboost non installé — pip install xgboost")

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_OK = True
except ImportError:
    OPTUNA_OK = False
    print("[WARN] optuna non installé — pip install optuna")

try:
    import shap
    SHAP_OK = True
except ImportError:
    SHAP_OK = False

from src.features.compute_features import get_feature_matrix


TARGET = "CR_mesure"
MODEL_PATH = Path("models/xgboost_cotco.pkl")


def train(
    df: pd.DataFrame,
    n_trials: int = 100,
    n_folds: int = 4,
    date_col: str = "date",
) -> tuple:
    """
    Entraîne XGBoost avec walk-forward validation + Optuna.

    Args:
        df       : dataset hybride (toutes sources)
        n_trials : nombre d'essais Optuna
        n_folds  : nombre de folds walk-forward
        date_col : colonne temporelle pour le split

    Returns:
        (model, metrics_dict, feature_names)
    """
    if not XGB_OK:
        raise ImportError("xgboost requis : pip install xgboost")

    # Préparer X, y
    df_clean = df.dropna(subset=[TARGET]).copy()
    X, feature_names = get_feature_matrix(df_clean)
    y = df_clean[TARGET].values

    # Pondérations par source
    poids = df_clean["poids"].values if "poids" in df_clean.columns else np.ones(len(df_clean))

    print(f"\n[XGBoost] Entraînement : {len(X)} lignes | {len(feature_names)} features")
    print(f"  CR target  moy={y.mean():.4f} | std={y.std():.4f} | "
          f"[{y.min():.4f}, {y.max():.4f}] mm/an")

    # Walk-forward folds
    folds = _walk_forward_folds(X, y, poids, df_clean, date_col, n_folds)

    # Optimisation Optuna
    if OPTUNA_OK and n_trials > 0:
        print(f"\n[Optuna] Optimisation hyperparamètres ({n_trials} trials)...")
        best_params = _optimiser_optuna(folds, n_trials)
    else:
        best_params = _params_defaut()
        print("[XGBoost] Paramètres par défaut (Optuna non disponible)")

    # Entraînement final sur 100% des données
    model = xgb.XGBRegressor(**best_params, random_state=42, verbosity=0)
    model.fit(X, y, sample_weight=poids)

    # Validation finale walk-forward
    metrics = _evaluer_walk_forward(folds, best_params)

    # Benchmark vs De Waard
    if "CR_deWaard" in df_clean.columns:
        mae_dw = np.mean(np.abs(df_clean["CR_deWaard"].values - y))
        metrics["mae_deWaard"] = mae_dw
        metrics["amelioration_vs_deWaard_pct"] = (
            (mae_dw - metrics["mae"]) / mae_dw * 100
        )
        print(f"\n  Benchmark DeWaard MAE : {mae_dw:.4f}")
        print(f"  XGBoost MAE          : {metrics['mae']:.4f}")
        print(f"  Amélioration         : +{metrics['amelioration_vs_deWaard_pct']:.1f}%")

    # Cohérence physique
    metrics["coherence_physique"] = _test_coherence_physique(model, feature_names)

    # SHAP
    shap_importance = {}
    if SHAP_OK:
        shap_importance = _calculer_shap(model, X, feature_names)
        metrics["shap_importance"] = shap_importance

    # Sauvegarder
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n[XGBoost] Modèle sauvegardé : {MODEL_PATH}")
    _afficher_metriques(metrics)

    return model, metrics, feature_names


def predict(X: pd.DataFrame, model=None) -> np.ndarray:
    """Prédit le taux de corrosion pour un ou plusieurs CML."""
    if model is None:
        model = joblib.load(MODEL_PATH)
    X_feat, _ = get_feature_matrix(X)
    return np.clip(model.predict(X_feat), 0.001, 5.0)


# ── Walk-forward validation ───────────────────────────────────────────────────

def _walk_forward_folds(X, y, poids, df, date_col, n_folds):
    """Découpe en folds temporels : train=passé, test=futur."""
    folds = []
    n = len(X)

    if date_col in df.columns:
        df_sorted = df.sort_values(date_col)
        sorted_idx = df_sorted.index
        X = X.loc[sorted_idx]
        y = y[sorted_idx.get_indexer(sorted_idx)]
        poids = poids[sorted_idx.get_indexer(sorted_idx)]

    fold_size = n // (n_folds + 1)
    for i in range(1, n_folds + 1):
        train_end = fold_size * i
        test_end  = fold_size * (i + 1)
        folds.append({
            "X_train": X.iloc[:train_end],
            "y_train": y[:train_end],
            "w_train": poids[:train_end],
            "X_test":  X.iloc[train_end:test_end],
            "y_test":  y[train_end:test_end],
        })

    return folds


def _evaluer_walk_forward(folds, params):
    """Évalue les métriques sur tous les folds."""
    maes, r2s, mapes = [], [], []

    for fold in folds:
        model_fold = xgb.XGBRegressor(**params, random_state=42, verbosity=0)
        model_fold.fit(
            fold["X_train"], fold["y_train"],
            sample_weight=fold["w_train"]
        )
        y_pred = np.clip(model_fold.predict(fold["X_test"]), 0.001, 5.0)
        y_true = fold["y_test"]

        mae  = np.mean(np.abs(y_true - y_pred))
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - y_true.mean()) ** 2)
        r2   = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-6))) * 100

        maes.append(mae)
        r2s.append(r2)
        mapes.append(mape)

    return {
        "mae":  float(np.mean(maes)),
        "r2":   float(np.mean(r2s)),
        "mape": float(np.mean(mapes)),
        "mae_std": float(np.std(maes)),
    }


# ── Optuna ────────────────────────────────────────────────────────────────────

def _optimiser_optuna(folds, n_trials):
    """Optimise les hyperparamètres XGBoost via Optuna."""

    def objective(trial):
        params = {
            "n_estimators":      trial.suggest_int("n_estimators", 100, 1000),
            "max_depth":         trial.suggest_int("max_depth", 3, 8),
            "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha":         trial.suggest_float("reg_alpha", 1e-5, 10, log=True),
            "reg_lambda":        trial.suggest_float("reg_lambda", 1e-5, 10, log=True),
            "min_child_weight":  trial.suggest_int("min_child_weight", 1, 10),
        }
        metrics = _evaluer_walk_forward(folds, params)
        return metrics["mae"]  # Minimiser MAE

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    print(f"[Optuna] Meilleur MAE : {study.best_value:.4f}")
    print(f"[Optuna] Meilleurs params : {study.best_params}")

    return study.best_params


def _params_defaut():
    return {
        "n_estimators": 500,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    }


# ── Tests cohérence physique ──────────────────────────────────────────────────

def _test_coherence_physique(model, feature_names) -> dict:
    """
    Vérifie que les prédictions suivent les lois physiques via tests contrôlés.
    On fait varier UNE variable à la fois (ceteris paribus) pour éviter
    que la corrélation soit masquée par d'autres variables aléatoires.

    1. CR augmente avec T (température)
    2. CR augmente avec pCO2
    3. CR diminue avec inhib (inhibiteur)
    """
    from src.data.generate_synthetic_cotco import generer_dataset_cotco
    from src.features.compute_features import compute_all_features, get_feature_matrix

    # Base : conditions moyennes fixes
    df_base = generer_dataset_cotco(n_points=1, seed=999)
    base = df_base.iloc[0].to_dict()

    n_pts = 50
    coherence = {}

    # Test 1 : CR augmente avec T (T varie, tout le reste fixé à la médiane)
    rows_T = []
    for T in np.linspace(35, 75, n_pts):
        r = base.copy()
        r["T_mean"] = T
        r["T_aval"] = T - 20
        rows_T.append(r)
    df_T = compute_all_features(pd.DataFrame(rows_T))
    X_T, _ = get_feature_matrix(df_T)
    preds_T = model.predict(X_T)
    corr_T = np.corrcoef(np.linspace(35, 75, n_pts), preds_T)[0, 1]
    coherence["CR_croissant_avec_T"] = corr_T > 0
    coherence["corr_T"] = round(corr_T, 3)

    # Test 2 : CR augmente avec pCO2 (CO2_pct varie, tout le reste fixé)
    rows_co2 = []
    for co2 in np.linspace(0.5, 5.0, n_pts):
        r = base.copy()
        r["CO2_pct"] = co2
        rows_co2.append(r)
    df_co2 = compute_all_features(pd.DataFrame(rows_co2))
    X_co2, _ = get_feature_matrix(df_co2)
    preds_co2 = model.predict(X_co2)
    corr_pco2 = np.corrcoef(np.linspace(0.5, 5.0, n_pts), preds_co2)[0, 1]
    coherence["CR_croissant_avec_pCO2"] = corr_pco2 > 0
    coherence["corr_pCO2"] = round(corr_pco2, 3)

    # Test 3 : CR diminue avec inhib (inhib_mean varie, tout le reste fixé)
    rows_inhib = []
    for inhib in np.linspace(5, 80, n_pts):
        r = base.copy()
        r["inhib_mean"] = inhib
        rows_inhib.append(r)
    df_inhib = compute_all_features(pd.DataFrame(rows_inhib))
    X_inhib, _ = get_feature_matrix(df_inhib)
    preds_inhib = model.predict(X_inhib)
    corr_inhib = np.corrcoef(np.linspace(5, 80, n_pts), preds_inhib)[0, 1]
    coherence["CR_decroissant_avec_inhib"] = corr_inhib < 0
    coherence["corr_inhib"] = round(corr_inhib, 3)

    passed = sum([v for v in coherence.values() if isinstance(v, bool)])
    print(f"\n[Coherence physique] {passed}/3 tests passes")
    for k, v in coherence.items():
        if isinstance(v, bool):
            print(f"  {'[OK]' if v else '[KO]'} {k}")

    return coherence


# ── SHAP ─────────────────────────────────────────────────────────────────────

def _calculer_shap(model, X, feature_names) -> dict:
    """Calcule et retourne les importances SHAP."""
    try:
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X)
        importance = np.abs(shap_vals).mean(axis=0)
        shap_dict = dict(zip(feature_names, importance.tolist()))
        shap_sorted = dict(sorted(shap_dict.items(), key=lambda x: x[1], reverse=True))
        print(f"\n[SHAP] Top 5 variables :")
        for feat, imp in list(shap_sorted.items())[:5]:
            print(f"  {feat:<30} {imp:.4f}")
        return shap_sorted
    except Exception as e:
        print(f"[WARN] SHAP : {e}")
        return {}


def _afficher_metriques(metrics):
    print(f"\n{'='*45}")
    print(f"  MÉTRIQUES XGBoost (walk-forward)")
    print(f"  MAE  : {metrics.get('mae', '?'):.4f} mm/an")
    print(f"  R²   : {metrics.get('r2', '?'):.4f} (objectif > 0.85)")
    print(f"  MAPE : {metrics.get('mape', '?'):.2f}% (objectif < 15%)")
    print(f"  MAE std : {metrics.get('mae_std', '?'):.4f}")
    print(f"{'='*45}")
