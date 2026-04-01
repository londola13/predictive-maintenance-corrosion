# Guide de déploiement — Stage COTCO Kribi
## Maintenance Prédictive Corrosion — Système ML

**Auteur :** Ricky Parfait
**Formation :** M2 ENSPD Douala — Spécialité Corrosion/Érosion Oil & Gas
**Site :** Station de Réduction de Pression de Kribi — Pipeline Chad-Cameroun

---

## Checklist rapide

```
Jour 1  [ ] Rencontrer responsable IT + ingénieur PI
        [ ] Tester accès PI Server (lecture seule suffit)
        [ ] Exporter 48h de données (test)
        [ ] Lancer validate_tags.py sur l'export test

Jour 2  [ ] Corriger le mapping tags si nécessaire
        [ ] Exporter 6-24 mois de données
        [ ] Récupérer 3-5 rapports UT récents (PDF)
        [ ] Récupérer analyses labo (Excel, 6 derniers mois)

Jour 3  [ ] Lancer activate_fusion.sh
        [ ] Vérifier que le dashboard tourne avec données réelles
        [ ] Comparer prédictions CR avec les valeurs UT connues
```

---

## Jour 1 — Accès PI Server

### Qui contacter en priorité
1. **Ingénieur PI Server** (ou IT Opérations) : demander un export CSV des tags DCS
2. **Ingénieur Corrosion** : demander les rapports UT des CML et analyses labo récentes
3. **Superviseur maintenance** : présenter l'outil et expliquer l'objectif

### Demande à formuler à l'ingénieur PI

> "Bonjour, dans le cadre de mon mémoire M2, j'ai besoin d'exporter les données
> des instruments de la station de Kribi sur les 6-12 derniers mois.
> Voici la liste des 20 tags nécessaires, au pas horaire, en format CSV.
> Une lecture seule est suffisante — je n'ai pas besoin d'écrire dans le PI."

**Fichier à remettre à l'ingénieur PI :** `stage_kit/pi_export_template.csv`
Ce fichier montre exactement le format et les noms de colonnes attendus.

### Tags DCS à exporter (priorité décroissante)

| Priorité | Tag     | Description                    | Plage normale  |
|----------|---------|--------------------------------|----------------|
| P1       | TI-1001 | Température entrée (°C)        | 35-65°C        |
| P1       | PI-2001 | Pression entrée (bar)          | 65-100 bar     |
| P1       | AI-4001 | CO₂ (% mol)                    | 0.5-5%         |
| P1       | AI-4003 | BSW (%)                        | 0.5-30%        |
| P1       | CI-5003 | Résiduel inhibiteur (mg/L)     | 20-80 mg/L     |
| P2       | FI-3001 | Débit volumique (m³/h)         | 200-800 m³/h   |
| P2       | AI-4002 | H₂S (ppm)                      | 0-500 ppm      |
| P2       | AI-4004 | Sable (ppm)                    | 0-200 ppm      |
| P2       | CI-5001 | Sonde ER amont (mm/an)         | 0-0.5 mm/an    |
| P2       | CI-5004 | Potentiel CP (mV/CSE)          | -850 à -1100   |
| P3       | Reste   | Tous les autres tags du tableau| Voir config.yaml|

### Format PI Server souhaité

```
Timestamp,TI-1001,TI-1002,...,CI-5004
2024-01-01 00:00:00,52.3,28.1,...,-920
2024-01-01 01:00:00,51.8,27.9,...,-915
```

- **Pas de temps :** 1 heure (le parser resample automatiquement)
- **Durée minimum :** 6 mois (~ 4 380 lignes) — idéal 12-24 mois
- **Format :** CSV (UTF-8 ou Latin-1)
- **Qualité PI :** inclure la colonne "quality" si disponible (le parser filtre "Good" automatiquement)

---

## Jour 2 — Corriger le mapping (si nécessaire)

### Étape 1 : Tester le mapping

```bash
python stage_kit/validate_tags.py data/enterprise/pi_export_test.csv
```

### Cas 1 : 100% reconnus → Parfait, passer à Jour 3

### Cas 2 : Tags partiellement reconnus

Si COTCO PI utilise `TI1001` au lieu de `TI-1001`, éditer :
`src/parsers/parse_pi_csv.py` — section `COTCO_TAG_MAPPING` :

```python
COTCO_TAG_MAPPING = {
    # Remplacer les noms selon l'export COTCO réel
    "TI1001": "T_mean",       # était "TI-1001"
    "PI2001": "P_mean",       # était "PI-2001"
    # etc.
}
```

### Cas 3 : Noms totalement différents (ex: T_KRIBI_INLET_01)

Demander à l'ingénieur PI le **"tag list"** complet de la station.
Mapper manuellement chaque tag dans `COTCO_TAG_MAPPING`.

> **Règle pratique :** Si moins de 10 des 20 tags sont reconnus, c'est normal.
> Le parser fonctionne avec les tags disponibles (colonnes manquantes = NaN, ignorées).
> Minimum viable : TI-1001, PI-2001, AI-4001, AI-4003, CI-5003 (5 tags P1).

---

## Données UT — Rapports d'inspection

### Ce qu'il faut récupérer
- Rapports PDF des mesures d'épaisseur par ultrasons (UT)
- Minimum : 2 mesures par CML (pour calculer le taux de corrosion réel)
- Idéal : toutes les mesures depuis 2020 sur les CML critiques

### Format attendu dans les PDFs
Le parser `parse_ut_pdf.py` détecte automatiquement :
- Numéro CML (ex: CML-001, CML-K01, KR-001...)
- Date de mesure
- Épaisseur mesurée (mm)
- Épaisseur nominale (mm)
- Technique (UT standard, PAUT, ToFD...)

### Commande pour parser les PDFs

```bash
# Placer les PDFs dans :
data/enterprise/ut_reports/

# Parser automatiquement :
python -c "
from src.parsers.parse_ut_pdf import parse_ut_folder
df = parse_ut_folder('data/enterprise/ut_reports/')
df.to_csv('data/enterprise/ut_parsed.csv', index=False)
print(df)
"
```

---

## Données labo — Analyses chimiques

### Ce qu'il faut récupérer
- Analyses eau de production mensuelles (pH, chlorures, fer dissous, SRB)
- Historique minimum 6 mois — idéal 2 ans

### Template Excel attendu

Utiliser le fichier : `stage_kit/labo_template.xlsx`
Ou demander le fichier Excel existant du labo — le parser détecte automatiquement
les colonnes pH, Cl⁻, Fe²⁺, inhibiteur, SRB, H₂S dissous (50+ variantes de noms).

### Commande pour parser le fichier labo

```bash
python -c "
from src.parsers.parse_labo_excel import parse_labo_excel
df = parse_labo_excel('data/enterprise/labo_analyses.xlsx')
print(df)
"
```

---

## Jour 3 — Activation du mode Fusion

Une fois les 3 types de données disponibles :

```bash
# Option 1 : Script automatique complet
bash stage_kit/activate_fusion.sh data/enterprise/pi_export.csv

# Option 2 : Manuelle étape par étape
python stage_kit/validate_tags.py data/enterprise/pi_export.csv   # 1. Valider
python src/run_pipeline.py --mode fusion --retrain                 # 2. Entraîner
python -m streamlit run dashboard/app.py                           # 3. Dashboard
```

### Structure attendue dans data/enterprise/

```
data/enterprise/
  pi_export.csv          ← Export PI Server (obligatoire)
  labo_analyses.xlsx     ← Analyses labo (optionnel, améliore les features)
  ut_reports/            ← PDFs rapports UT (optionnel, calcul CR réel)
    rapport_UT_2024_01.pdf
    rapport_UT_2024_07.pdf
    ...
```

> **Minimum viable :** Seulement `pi_export.csv` suffit pour activer le mode fusion.
> Les données UT et labo enrichissent le modèle mais ne sont pas bloquantes.

---

## Interpréter les premières prédictions

### Ce qui va probablement se passer
1. **Concordance WeibullAFT** : devrait passer de 0.50 → 0.65-0.80 (données réelles)
2. **MAE XGBoost** : peut monter temporairement (normal — données réelles vs synthétiques)
3. **Classes de risque** : certains CML classés "Critique" sur synthétique peuvent tomber à "Modéré" (ou vice versa) — c'est le but

### Vérification de cohérence (à faire le premier jour)

```python
# Comparer les prédictions avec les mesures UT connues
# (si vous avez au moins 2 rapports UT avec les épaisseurs)
python -c "
from src.models.decision_engine import evaluer_cml
# Tester avec un CML dont vous connaissez la vraie CR
result = evaluer_cml(
    CML_ID='CML-001',
    CR_predit=0.08,  # mm/an
    RL_median=18.0,  # ans
)
print(result)
"
```

---

## Problèmes fréquents

| Problème | Cause probable | Solution |
|----------|---------------|----------|
| Toutes colonnes NaN après parse_pi | Noms tags différents | Lancer validate_tags.py |
| Pipeline.error ImportError | venv non activé | `venv\Scripts\activate` |
| WeibullAFT error "not enough events" | Trop peu de données UT | Augmenter la durée d'export PI |
| CR prédit très éloigné de la UT | Données PI de mauvaise qualité | Vérifier les plages physiques dans le rapport de complétude |
| Dashboard vide | Modèles pas re-entraînés | `run_pipeline.py --mode fusion --retrain` |

---

## Contact et support

Problème technique : consulter les issues GitHub
`https://github.com/londola13/predictive-maintenance-corrosion`

Encadrant mémoire : contacter directement (email ENSPD)
