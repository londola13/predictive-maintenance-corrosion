"""
03_modeling.py — Jour 3
-----------------------
Entraînement complet des 3 modèles + SHAP.
Compatible Google Colab et local.

Exécuter depuis la racine du projet :
    python notebooks/03_modeling.py

Google Colab :
    !git clone https://github.com/londola13/predictive-maintenance-corrosion
    %cd predictive-maintenance-corrosion
    !pip install -r requirements.txt
    !python notebooks/03_modeling.py
"""

import sys, os, json, warnings
warnings.filterwarnings('ignore')

# Racine du projet
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
import shap

from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                             r2_score, classification_report,
                             confusion_matrix, ConfusionMatrixDisplay)
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBRegressor

from data_loader import load_synthetic
from features import preprocess

# ─────────────────────────────────────────────────────────
# 0. Préparation — dossiers + données
# ─────────────────────────────────────────────────────────
os.makedirs('models', exist_ok=True)
os.makedirs('notebooks/figs', exist_ok=True)

if not os.path.exists('data/raw/synthetic_corrosion.csv'):
    print("Génération des données synthétiques...")
    import subprocess
    subprocess.run([sys.executable, 'src/generate_synthetic_data.py'], check=True)

df = load_synthetic()
print(f"Dataset : {df.shape[0]} lignes x {df.shape[1]} colonnes")
print(df['risque'].value_counts().to_string())

# ─────────────────────────────────────────────────────────
# 1. Régression — taux de corrosion (XGBoost)
# ─────────────────────────────────────────────────────────
print("\n=== Modèle 1 : Régression taux de corrosion (XGBoost) ===")
X_tr, X_te, y_tr, y_te, feat_cols = preprocess(df, 'taux_corrosion')

model_reg = XGBRegressor(
    n_estimators=300, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, random_state=42
)
model_reg.fit(X_tr, y_tr)
p_reg = model_reg.predict(X_te)

r2_reg   = r2_score(y_te, p_reg)
mae_reg  = mean_absolute_error(y_te, p_reg)
rmse_reg = np.sqrt(mean_squared_error(y_te, p_reg))
print(f"R2={r2_reg:.4f}  MAE={mae_reg:.4f} mm/an  RMSE={rmse_reg:.4f}")

joblib.dump(model_reg, 'models/model_regression.pkl')
print("-> Sauvegarde : models/model_regression.pkl")

# Figure : prédit vs réel
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(y_te[:500], p_reg[:500], alpha=0.4, s=12, color='steelblue')
lim = [0, max(float(y_te.max()), float(p_reg.max()))]
ax.plot(lim, lim, 'r--', lw=1.5, label='Idéal')
ax.set_xlabel('Taux réel (mm/an)')
ax.set_ylabel('Taux prédit (mm/an)')
ax.set_title(f'Régression corrosion — R2={r2_reg:.3f}')
ax.legend()
plt.tight_layout()
plt.savefig('notebooks/figs/01_regression_scatter.png', dpi=150)
plt.close()

# ─────────────────────────────────────────────────────────
# 2. Classification — risque (Random Forest)
# ─────────────────────────────────────────────────────────
print("\n=== Modèle 2 : Classification risque (Random Forest) ===")
X_tr_c, X_te_c, y_tr_c, y_te_c, _ = preprocess(df, 'risque')
le = joblib.load('models/encoder_risque.pkl')

model_clf = RandomForestClassifier(
    n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
)
model_clf.fit(X_tr_c, y_tr_c)
p_clf = model_clf.predict(X_te_c)
print(classification_report(y_te_c, p_clf, target_names=le.classes_))

joblib.dump(model_clf, 'models/model_classification.pkl')
print("-> Sauvegarde : models/model_classification.pkl")

# Matrice de confusion
cm = confusion_matrix(y_te_c, p_clf)
fig, ax = plt.subplots(figsize=(5, 4))
ConfusionMatrixDisplay(cm, display_labels=le.classes_).plot(
    ax=ax, colorbar=False, cmap='Blues'
)
ax.set_title('Matrice de confusion — Risque')
plt.tight_layout()
plt.savefig('notebooks/figs/02_confusion_matrix.png', dpi=150)
plt.close()

# ─────────────────────────────────────────────────────────
# 3. Régression — RUL (XGBoost)
# ─────────────────────────────────────────────────────────
print("\n=== Modèle 3 : RUL — Remaining Useful Life (XGBoost) ===")
X_tr_r, X_te_r, y_tr_r, y_te_r, _ = preprocess(df, 'rul')

model_rul = XGBRegressor(
    n_estimators=300, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, random_state=42
)
model_rul.fit(X_tr_r, y_tr_r)
p_rul = model_rul.predict(X_te_r)

r2_rul   = r2_score(y_te_r, p_rul)
mae_rul  = mean_absolute_error(y_te_r, p_rul)
rmse_rul = np.sqrt(mean_squared_error(y_te_r, p_rul))
print(f"R2={r2_rul:.4f}  MAE={mae_rul:.4f} ans  RMSE={rmse_rul:.4f}")

joblib.dump(model_rul, 'models/model_rul.pkl')
print("-> Sauvegarde : models/model_rul.pkl")

# ─────────────────────────────────────────────────────────
# 4. SHAP — Explicabilité (modèle régression)
# ─────────────────────────────────────────────────────────
print("\n=== SHAP — Importance des features ===")
explainer = shap.TreeExplainer(model_reg)
shap_vals = explainer.shap_values(X_te[:300])

# Bar chart
plt.figure(figsize=(8, 5))
shap.summary_plot(shap_vals, X_te[:300], feature_names=feat_cols,
                  plot_type='bar', show=False)
plt.title('SHAP — Importance variables (Régression corrosion)')
plt.tight_layout()
plt.savefig('notebooks/figs/03_shap_bar.png', dpi=150, bbox_inches='tight')
plt.close()

# Beeswarm
plt.figure(figsize=(8, 5))
shap.summary_plot(shap_vals, X_te[:300], feature_names=feat_cols, show=False)
plt.tight_layout()
plt.savefig('notebooks/figs/04_shap_beeswarm.png', dpi=150, bbox_inches='tight')
plt.close()

# Export JSON pour le dashboard
mean_shap = np.abs(shap_vals).mean(axis=0)
shap_dict = dict(sorted(
    {feat_cols[i]: float(mean_shap[i]) for i in range(len(feat_cols))}.items(),
    key=lambda x: x[1], reverse=True
))
with open('models/shap_importance.json', 'w', encoding='utf-8') as f:
    json.dump(shap_dict, f, indent=2)
print("-> models/shap_importance.json sauvegardé")

# ─────────────────────────────────────────────────────────
# 5. Résumé final
# ─────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print("  RÉSUMÉ — PERFORMANCES MODÈLES")
print(f"{'='*55}")
print(f"  Régression corrosion  R2={r2_reg:.4f}  MAE={mae_reg:.4f} mm/an")
print(f"  RUL                   R2={r2_rul:.4f}  MAE={mae_rul:.4f} ans")
print(f"  Classification risque -> voir rapport ci-dessus")
print(f"{'='*55}")
print("\n  Figures  -> notebooks/figs/")
print("  Modèles  -> models/*.pkl")
print("  SHAP     -> models/shap_importance.json")
print("\n  Lancer le dashboard :")
print("  streamlit run dashboard/app.py")
