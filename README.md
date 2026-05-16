# Système intégré de maintenance prédictive de la corrosion par apprentissage automatique

> Mémoire de fin d'études Master 2 — ESTL Douala  
> Spécialité : Maintenance Industrielle et Productique  
> Auteur : Ricky Parfait BATOUMBI IKOND — Matricule 0111 II17  
> Encadrement professionnel : M. FEZEU (COTCO) | Supervision : Dr. TCHAWE

---

## Contexte : transition Industrie 3.0 → 4.0

COTCO (Cameroon Oil Transportation Company) dispose de sondes ER (Electrical Resistance) commerciales (Cosasco, Roxar) câblées à un DCS — état Industrie 3.0 : surveillance par seuils, maintenance calendaire, analyse silotée.

Ce projet démontre qu'avec les données historiques issues de ces sondes, il est possible d'ajouter une **couche prédictive ML** sans remplacer l'infrastructure existante — saut logiciel vers l'Industrie 4.0.

Le prototype est **doublement transposable** :
- **(a) Industriel** : brancher le pipeline ML sur les sondes ER existantes de COTCO
- **(b) PME africaines** : déploiement autonome avec la sonde ER instrumentée ESP32 décrite ici

---

## Architecture du système

```
ESP32 (HX711 + DS18B20 + pont Wheatstone — sonde ER)
   │  HTTPS POST toutes les 30s
   ▼
Supabase (cr_measurements, cr_runs, cr_predictions, cr_alerts)
   │
   ▼
Pipeline Python (Pandas + XGBoost + SHAP)
   │  --run-id UUID
   ▼
Dashboard Streamlit
   ├─ Diagnostic 5 régimes (stable / accélération / passivation / adsorption / pré-rupture)
   ├─ Prédiction CR (mm/an) + RUL (heures)
   ├─ Alertes graduées vert / orange / rouge
   └─ Si alerte critique → POST API REST
                              ▼
                         GLPI (CMMS open-source — alternative PME à SAP PM)
                           ├─ Tickets / OT / Changes
                           └─ KPIs : MTBF, MTTR, η inhibition
```

---

## Structure du repo

```
predictive-maintenance-corrosion/
├── firmware/
│   └── corrosion_monitor/
│       └── corrosion_monitor.ino   ← ESP32 : mesure ER + POST Supabase
├── pipeline/
│   └── corrosion_pipeline.py       ← pipeline ML (--run-id UUID)
├── src/
│   ├── etl/
│   │   ├── fetch_supabase.py
│   │   ├── build_dataset_ml.py
│   │   └── merge_all_sources.py
│   ├── integrations/
│   │   └── glpi_api.py             ← POST ticket GLPI via API REST
│   └── cli/
│       ├── start_run.py            ← démarre un run RTF
│       ├── stop_run.py             ← clôture le run
│       └── set_run_id.py           ← configure run_id dans ESP32 NVS
├── dashboard/
│   └── app.py                      ← Streamlit : dashboard + Start/Stop run
├── docker/
│   └── docker-compose.yml          ← GLPI + MariaDB pour démo locale
├── models/
│   └── .gitkeep                    ← modèles entraînés sur runs RTF réels (non committés)
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

Copier `.env.example` → `.env` et remplir les credentials Supabase.

---

## Utilisation

### 1. Démarrer un run RTF

```bash
python src/cli/start_run.py
# → génère un run_id UUID et l'enregistre dans cr_runs
```

### 2. Lancer le dashboard

```bash
streamlit run dashboard/app.py
# → sélecteur de run, compteur live (TTL 30s), boutons Start/Stop
```

### 3. Entraîner le pipeline ML sur un run

```bash
python pipeline/corrosion_pipeline.py --run-id <UUID>
# → lit cr_measurements, entraîne XGBoost CR + RUL, écrit cr_predictions
```

### 4. GLPI local (démo CMMS)

```bash
cd docker
docker compose up -d
# → GLPI accessible sur http://localhost:8080
```

---

## Protocole expérimental — Runs RTF

| Run | Milieu | Inhibiteur | Objectif |
|-----|--------|------------|----------|
| 1 | Detar Plus (HCl 5-15% + H₃PO₄ 10-30%, pH≈1) | Aucun | Baseline corrosion libre |
| 2 | Detar Plus | Imidazoline 0,1% v/v | Efficacité inhibition faible dose |
| 3 | Detar Plus | Imidazoline 0,5% v/v | Efficacité inhibition haute dose |
| 4 | Detar Plus | Aucun (repeat) | Reproductibilité |

Validation ML : TimeSeriesSplit n=4 (respect de la causalité temporelle).  
Interprétabilité : SHAP (top-3 features par prédiction → ticket GLPI).

---

## Intégration CMMS — Positionnement GLPI vs SAP PM

Pour COTCO, l'intégration industrielle cible serait **SAP PM** (Plant Maintenance) via interface OData/BAPI. Le prototype démontre la faisabilité de l'interconnexion ML→CMMS avec **GLPI**, alternative open-source adaptée aux PME africaines à budget contraint. La transposabilité vers SAP PM est garantie par l'usage d'un standard REST identique.

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Capteur | ESP32 + HX711 (24-bit) + DS18B20 (1-Wire) + pont Wheatstone |
| Backend | Supabase (PostgreSQL + REST) |
| ML | XGBoost, SHAP, TimeSeriesSplit |
| Frontend | Streamlit Community Cloud |
| CMMS | GLPI (API REST, Docker local) |
| Langage | Python 3.10, C++ (Arduino) |

---

*Prototype académique ESTL Douala — données issues de runs RTF réels sur sonde ER instrumentée*
