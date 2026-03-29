# Maintenance Prédictive — Corrosion & Érosion/Corrosion

> Mémoire de fin d'études Master 2 | Pipelines pétroliers

## Objectif
Prototype fonctionnel de maintenance prédictive basé sur le modèle physique de **de Waard-Milliams** (corrosion CO2), enrichi par des modèles ML (XGBoost, Random Forest).  
Architecture conçue pour intégrer facilement les données réelles d'une entreprise.

---

## Structure

```
predictive-maintenance-corrosion/
├── data/
│   ├── raw/              ← données brutes publiques
│   ├── processed/        ← données nettoyées
│   └── enterprise/       ← dossier plug-and-play données entreprise
├── notebooks/            ← EDA et expérimentations
├── models/               ← modèles entraînés (.pkl)
├── src/
│   ├── generate_synthetic_data.py   ← génération données (de Waard-Milliams)
│   ├── data_loader.py               ← chargeur générique public + entreprise
│   ├── features.py                  ← feature engineering
│   ├── train.py                     ← entraînement 3 modèles
│   └── predict.py                   ← inférence
├── dashboard/
│   └── app.py                       ← Dashboard Streamlit
└── requirements.txt
```

---

## Installation

```bash
git clone https://github.com/londola13/predictive-maintenance-corrosion.git
cd predictive-maintenance-corrosion
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Utilisation

```bash
# 1. Générer les données synthétiques
python src/generate_synthetic_data.py

# 2. Entraîner les modèles
python src/train.py

# 3. Lancer le dashboard
streamlit run dashboard/app.py
```

## Modèles

| Modèle | Algorithme | Cible |
|---|---|---|
| Régression | XGBoost | Taux de corrosion (mm/an) |
| Classification | Random Forest | Risque (Faible/Moyen/Élevé) |
| RUL | XGBoost | Remaining Useful Life (ans) |

## Intégration données entreprise

Déposer les fichiers CSV/Excel dans `data/enterprise/` puis relancer `python src/train.py`.  
Le modèle se recalibre automatiquement sur les conditions réelles.

---

*Prototype — données publiques (de Waard-Milliams + PHMSA + NASA CMAPSS)*
