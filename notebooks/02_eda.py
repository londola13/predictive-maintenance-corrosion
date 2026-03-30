"""
EDA — Analyse exploratoire des données corrosion pipeline
Jour 2 — génère les visualisations dans notebooks/figures/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('notebooks/figures', exist_ok=True)

df = pd.read_csv('data/raw/synthetic_corrosion.csv')

print("=" * 60)
print("APERÇU DU DATASET")
print("=" * 60)
print(f"Shape : {df.shape}")
print(f"\nTypes :\n{df.dtypes}")
print(f"\nValeurs manquantes :\n{df.isnull().sum()}")
print(f"\nStats descriptives :\n{df.describe().round(3)}")
print(f"\nDistribution risque :\n{df['risque'].value_counts()}")

# ── Figure 1 : Distribution des variables numériques ─────────────────────────
fig, axes = plt.subplots(3, 4, figsize=(18, 12))
fig.suptitle('Distribution des variables', fontsize=16, fontweight='bold')
num_cols = df.select_dtypes(include=np.number).columns
for ax, col in zip(axes.flatten(), num_cols):
    ax.hist(df[col], bins=40, color='steelblue', edgecolor='white', alpha=0.85)
    ax.set_title(col, fontsize=10)
    ax.set_xlabel('')
for ax in axes.flatten()[len(num_cols):]:
    ax.set_visible(False)
plt.tight_layout()
plt.savefig('notebooks/figures/01_distributions.png', dpi=150)
plt.close()
print("\n[OK] figures/01_distributions.png")

# ── Figure 2 : Heatmap corrélations ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 9))
corr = df.select_dtypes(include=np.number).corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlGn',
            center=0, ax=ax, linewidths=0.5)
ax.set_title('Matrice de corrélation', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('notebooks/figures/02_correlation.png', dpi=150)
plt.close()
print("[OK] figures/02_correlation.png")

# ── Figure 3 : Taux de corrosion vs variables clés ───────────────────────────
key_vars = ['temperature', 'pco2', 'pH', 'vitesse_fluide']
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Taux de corrosion vs Variables clés', fontsize=14, fontweight='bold')
colors = {'Faible': '#2ecc71', 'Moyen': '#f39c12', 'Élevé': '#e74c3c'}
for ax, var in zip(axes.flatten(), key_vars):
    for risk, grp in df.groupby('risque'):
        ax.scatter(grp[var], grp['taux_corrosion'],
                   c=colors.get(risk, 'gray'), label=risk,
                   alpha=0.4, s=15)
    ax.set_xlabel(var)
    ax.set_ylabel('Taux corrosion (mm/an)')
    ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig('notebooks/figures/03_corrosion_vs_features.png', dpi=150)
plt.close()
print("[OK] figures/03_corrosion_vs_features.png")

# ── Figure 4 : Distribution risque + RUL ─────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
# Pie
counts = df['risque'].value_counts()
ax1.pie(counts, labels=counts.index, autopct='%1.1f%%',
        colors=['#2ecc71', '#f39c12', '#e74c3c'],
        startangle=90, explode=[0.03]*3)
ax1.set_title('Répartition des niveaux de risque', fontweight='bold')
# RUL distribution
ax2.hist(df['rul'], bins=50, color='steelblue', edgecolor='white', alpha=0.85)
ax2.axvline(df['rul'].mean(), color='red', linestyle='--',
            label=f"Moyenne : {df['rul'].mean():.1f} ans")
ax2.set_xlabel('RUL (années)')
ax2.set_ylabel('Fréquence')
ax2.set_title('Distribution du RUL (Remaining Useful Life)', fontweight='bold')
ax2.legend()
plt.tight_layout()
plt.savefig('notebooks/figures/04_risque_rul.png', dpi=150)
plt.close()
print("[OK] figures/04_risque_rul.png")

# ── Figure 5 : Impact inhibiteur ─────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
df.groupby('inhibiteur')['taux_corrosion'].plot(kind='hist', ax=ax1,
    bins=40, alpha=0.7, legend=True)
ax1.set_xlabel('Taux de corrosion (mm/an)')
ax1.set_title('Impact inhibiteur sur taux de corrosion', fontweight='bold')
ax1.legend(['Sans inhibiteur (0)', 'Avec inhibiteur (1)'])
df.boxplot(column='taux_corrosion', by='risque', ax=ax2,
           color={'boxes':'steelblue','whiskers':'gray','medians':'red','caps':'gray'})
ax2.set_title('Taux corrosion par niveau de risque', fontweight='bold')
ax2.set_xlabel('Niveau de risque')
ax2.set_ylabel('Taux (mm/an)')
plt.suptitle('')
plt.tight_layout()
plt.savefig('notebooks/figures/05_inhibiteur_boxplot.png', dpi=150)
plt.close()
print("[OK] figures/05_inhibiteur_boxplot.png")

# ── Corrélations avec la cible ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("CORRÉLATIONS avec taux_corrosion (tri décroissant)")
print("=" * 60)
corr_target = df.select_dtypes(include=np.number).corr()['taux_corrosion'].drop('taux_corrosion')
print(corr_target.sort_values(ascending=False).round(4).to_string())

print("\n✅ EDA terminée. Figures dans notebooks/figures/")
