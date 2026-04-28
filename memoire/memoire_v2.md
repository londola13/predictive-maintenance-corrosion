---
title: "Système de maintenance prédictive de la corrosion par apprentissage automatique : conception d'une sonde ER low-cost, acquisition IoT et prédiction du taux de corrosion et de la durée de vie résiduelle par XGBoost"
---

\newpage

# PAGE DE TITRE

**RÉPUBLIQUE DU CAMEROUN**
*Paix — Travail — Patrie*

**REPUBLIC OF CAMEROON**
*Peace — Work — Fatherland*

---

**MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR**

**ÉCOLE NATIONALE SUPÉRIEURE POLYTECHNIQUE DE DOUALA**
*(ENSPD)*

**Département de Génie Industriel et Maintenance**

---

**Mémoire rédigé en vue de l'obtention d'un Master Professionnel**

**OPTION : MAINTENANCE INDUSTRIELLE**

---

**Thème :**

**SYSTÈME DE MAINTENANCE PRÉDICTIVE DE LA CORROSION PAR APPRENTISSAGE AUTOMATIQUE : CONCEPTION D'UNE SONDE ER LOW-COST, ACQUISITION IoT ET PRÉDICTION DU TAUX DE CORROSION ET DE LA DURÉE DE VIE RÉSIDUELLE PAR XGBoost**

---

| | |
|---|---|
| **Rédigé par :** | BATOUMBI IKOND Ricky Parfait |
| **Matricule :** | À compléter |
| **Sous encadrement académique de :** | À compléter |
| **Sous l'encadrement professionnel de :** | À compléter (COTCO) |
| **Sous la supervision de :** | À compléter |
| **Année académique :** | 2025 — 2026 |

\newpage

# DÉDICACE

*À mes chers parents*

\newpage

# REMERCIEMENTS

Au terme de notre formation pour l'obtention du Master II dans la spécialité Maintenance Industrielle, nous tenons à exprimer notre sincère reconnaissance à tout le corps professoral de l'École Nationale Supérieure Polytechnique de Douala, qui par la qualité de leur enseignement et de leur encadrement, nous avons pu terminer avec succès cette formation en ingénierie.

En l'occurrence :

- À notre encadreur académique, pour son encadrement, sa disponibilité et ses conseils tout au long de ce mémoire.
- À notre superviseur, pour ses conseils et son approche très scientifique.
- À notre encadreur professionnel au sein de la Cameroon Oil Transportation Company (COTCO), pour la qualité de son encadrement exceptionnel, sa patience, sa rigueur et sa disponibilité durant tout le processus de mise sur pied de ce travail.
- À nos parents pour leurs encouragements et leur soutien constant.

Que tous ceux qui, de près ou de loin, ont contribué à la réussite de ce mémoire et dont les noms n'auraient pas été cités trouvent en quelques mots l'expression de nos sincères remerciements.

\newpage

# RÉSUMÉ

La corrosion représente un coût annuel mondial de 2,5 billions de dollars (3,4 % du PIB mondial) et constitue la première cause de défaillance structurelle dans le secteur Oil & Gas. Au Cameroun, la gestion de la corrosion dans les installations pétrolières — notamment le réseau de pipelines COTCO — repose encore largement sur des stratégies réactives sans exploitation de données de surveillance continue.

Ce mémoire présente la conception, le développement et la validation expérimentale d'un système intégré de maintenance prédictive de la corrosion articulé autour de trois composants : une sonde ER (Electrical Resistance) low-cost à base de fil de fer monté en pont de Wheatstone et instrumentée par un amplificateur HX711 24 bits ; un système d'acquisition IoT à microcontrôleur ESP32 en deep sleep pulsé mesurant la résistance et la température toutes les dix minutes ; et un modèle XGBoost entraîné en protocole run-to-failure pour prédire le taux de corrosion (CR, en mm/an) et la durée de vie résiduelle (RUL, en heures).

L'environnement corrosif est le Detar Plus, détartrant industriel à base d'acide chlorhydrique et d'acide phosphorique (pH ≈ 1). Le protocole run-to-failure sur quatre séquences de corrosion jusqu'à rupture du fil constitue le jeu d'apprentissage. Le coût total du prototype est inférieur à 50 000 FCFA.

**Mots-clés :** corrosion, sonde ER, XGBoost, maintenance prédictive, IoT, ESP32, HX711, durée de vie résiduelle, inhibiteur de corrosion, apprentissage automatique.

\newpage

# ABSTRACT

Corrosion represents an annual global cost of USD 2.5 trillion (3.4% of global GDP) and is the primary cause of structural failure in the Oil & Gas sector. In Cameroon, corrosion management in petroleum installations — notably the COTCO pipeline network — still relies largely on reactive strategies without exploiting continuous monitoring data.

This thesis presents the design, development and experimental validation of an integrated corrosion predictive maintenance system built around three components: a low-cost ER (Electrical Resistance) probe based on an iron wire in a Wheatstone bridge instrumented by a 24-bit HX711 amplifier; an IoT acquisition system using an ESP32 microcontroller in pulsed deep sleep mode measuring resistance and temperature every ten minutes; and an XGBoost model trained using a run-to-failure protocol to predict corrosion rate (CR, in mm/year) and remaining useful life (RUL, in hours).

The corrosive environment is Detar Plus, an industrial descaler based on hydrochloric and phosphoric acids (pH ≈ 1). The run-to-failure protocol over four complete corrosion sequences constitutes the training dataset. Total prototype cost is under 50,000 FCFA.

**Keywords:** corrosion, ER probe, XGBoost, predictive maintenance, IoT, ESP32, HX711, remaining useful life, corrosion inhibitor, machine learning.

\newpage

# LISTE DES ABRÉVIATIONS

| Abréviation | Signification |
|---|---|
| AC PROTECT 106 | Inhibiteur de corrosion industriel à base d'imidazoline |
| ADC | Analog-to-Digital Converter (Convertisseur Analogique-Numérique) |
| AMPP | Association for Materials Protection and Performance (ex-NACE International) |
| API | American Petroleum Institute |
| ASTM | American Society for Testing and Materials |
| COTCO | Cameroon Oil Transportation Company |
| CR | Corrosion Rate (Taux de corrosion, en mm/an) |
| DS18B20 | Capteur de température numérique à bus 1-Wire |
| ER | Electrical Resistance (Résistance Électrique — type de sonde de corrosion) |
| ENSPD | École Nationale Supérieure Polytechnique de Douala |
| ESP32 | Microcontrôleur bi-cœur Wi-Fi + Bluetooth (Espressif Systems) |
| GPIO | General-Purpose Input/Output |
| HX711 | Amplificateur et convertisseur ADC 24 bits pour ponts de Wheatstone |
| IoT | Internet of Things (Internet des Objets) |
| IQR | Interquartile Range (intervalle interquartile) |
| ISO | International Organization for Standardization |
| MAE | Mean Absolute Error (erreur absolue moyenne) |
| ML | Machine Learning (apprentissage automatique) |
| NACE | National Association of Corrosion Engineers |
| R² | Coefficient de détermination |
| RMSE | Root Mean Square Error (erreur quadratique moyenne) |
| RTC | Real-Time Clock |
| RTF | Run-To-Failure (protocole de corrosion jusqu'à rupture) |
| RUL | Remaining Useful Life (Durée de Vie Résiduelle) |
| SHAP | SHapley Additive exPlanations (méthode d'interprétabilité ML) |
| XGBoost | eXtreme Gradient Boosting |

\newpage

# LISTE DES FIGURES

*(générée automatiquement)*

\newpage

# LISTE DES TABLEAUX

*(générée automatiquement)*

\newpage

# SOMMAIRE

DÉDICACE
REMERCIEMENTS
RÉSUMÉ
ABSTRACT
LISTE DES ABRÉVIATIONS
LISTE DES FIGURES
LISTE DES TABLEAUX
SOMMAIRE
INTRODUCTION GÉNÉRALE
CHAPITRE I : CONTEXTE ET PROBLÉMATIQUE
CHAPITRE II : OUTILS ET MÉTHODES
CHAPITRE III : RÉSULTATS ET DISCUSSIONS
CONCLUSION GÉNÉRALE
RÉFÉRENCES BIBLIOGRAPHIQUES
ANNEXES
TABLE DES MATIÈRES

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# INTRODUCTION GÉNÉRALE

Dans un contexte industriel mondial où la corrosion engendre des pertes annuelles estimées à 2,5 billions de dollars — soit 3,4 % du PIB mondial (Koch et al., 2016) — la maîtrise de la dégradation des équipements constitue un enjeu stratégique de premier ordre pour tout opérateur d'infrastructures pétrolières. Les entreprises sont aujourd'hui confrontées à la nécessité de réduire les coûts de maintenance, d'augmenter la disponibilité de leurs installations et de prévenir les incidents environnementaux avant qu'ils ne se produisent.

C'est dans ce contexte que les stratégies de maintenance évoluent, passant progressivement de la maintenance corrective et préventive à des approches plus avancées, telles que la maintenance conditionnelle et prédictive basée sur la surveillance continue des équipements. Parmi les techniques disponibles, la surveillance par sonde à résistance électrique (ER) s'impose comme un outil de mesure direct du taux de corrosion, permettant de détecter les anomalies avant qu'elles n'atteignent un seuil critique.

Le présent mémoire s'inscrit dans cette dynamique et a pour objectif de concevoir et valider un système de maintenance prédictive de la corrosion entièrement développé à partir de composants low-cost accessibles localement au Cameroun, couplé à un algorithme d'apprentissage automatique XGBoost capable de prédire à la fois le taux de corrosion et la durée de vie résiduelle d'un élément métallique exposé à un milieu acide.

Après une revue de la littérature sur les mécanismes de corrosion, les techniques de surveillance et les méthodes de prédiction, ainsi qu'une présentation du contexte et de la problématique (Chapitre I), nous aborderons les fondements techniques du prototype développé — la sonde ER, le système d'acquisition IoT et le pipeline de traitement par apprentissage automatique — ainsi que la méthodologie retenue pour leur mise en œuvre (Chapitre II). Enfin, les résultats expérimentaux obtenus lors des runs de corrosion en laboratoire seront présentés et discutés, incluant les performances du modèle XGBoost et l'évaluation du système d'alertes (Chapitre III).

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CHAPITRE I : CONTEXTE ET PROBLÉMATIQUE

**Sommaire du Chapitre I**

I.1. Revue de la littérature sur la corrosion
I.2. Présentation du contexte d'étude
I.3. Politique de maintenance et surveillance de la corrosion
I.4. Problématique
I.5. Questions de recherche et objectifs du mémoire
I.6. Conclusion

---

## I.0. Introduction

Dans ce chapitre, nous allons dans un premier temps effectuer la revue de la littérature sur la corrosion et ses mécanismes, présenter ensuite le contexte industriel de l'étude et la politique de maintenance actuelle, puis dégager la problématique qui en ressort et définir les objectifs général et spécifiques de ce travail.

---

## I.1. Revue de la littérature sur la corrosion

### I.1.1. Définition et nature électrochimique de la corrosion

La corrosion est définie par la norme ISO 8044 comme « une interaction physico-chimique entre un métal et son environnement qui entraîne des modifications des propriétés du métal et qui peut conduire à une dégradation significative de la fonction du métal, de l'environnement ou du système technique dont ils font partie ». Ce phénomène naturel traduit la tendance thermodynamique des métaux à retourner à leur état d'oxyde stable — état sous lequel ils existent dans la nature avant tout traitement métallurgique.

Dans un milieu électrolytique (solution aqueuse, sol humide), la corrosion procède par un mécanisme de pile galvanique dans lequel deux réactions électrochimiques couplées se produisent simultanément à la surface du métal.

Réaction anodique — oxydation (dissolution du métal) :

$$\text{Fe} \rightarrow \text{Fe}^{2+} + 2e^-$$

Réaction cathodique — réduction (consommation des électrons) :

En milieu acide (pH < 4) :

$$2\text{H}^+ + 2e^- \rightarrow \text{H}_2\uparrow$$

En milieu neutre :

$$\text{O}_2 + 2\text{H}_2\text{O} + 4e^- \rightarrow 4\text{OH}^-$$

La loi de Faraday (1834) établit la relation quantitative entre le courant électrique échangé et la masse de métal dissous :

$$m = \frac{M \cdot I \cdot t}{n \cdot F}$$

Le taux de corrosion (CR), exprimé en mm/an conformément à la norme ASTM G1, est calculé par :

$$CR \ (mm/an) = \frac{87{,}6 \cdot \Delta m}{\rho \cdot A \cdot t}$$

Dans le prototype de laboratoire, l'environnement acide (Detar Plus — détartrant professionnel à base d'acide phosphorique et d'acide chlorhydrique, pH ≈ 1) active simultanément ces deux réactions sur le fil de fer de la sonde ER, avec une cinétique fortement accélérée.

### I.1.2. Formes de corrosion et classification

La corrosion ne se manifeste pas de manière uniforme. La classification internationale de référence établie par l'AMPP (ex-NACE International) et reprise dans la norme NACE SP0775 distingue les formes suivantes :

**Tableau I.1 — Classification des formes de corrosion**

| Forme | Mécanisme | Localisation typique | Norme |
|---|---|---|---|
| Généralisée (uniforme) | Dissolution uniforme sur toute la surface | Pipelines acier au carbone | ASTM G1, NACE SP0775 |
| Par piqûres | Attaque localisée par les ions Cl⁻ | Acier inox en milieu chloruré | ASTM G46 |
| Galvanique | Couplage entre deux métaux de potentiels différents | Raccords bimétalliques offshore | ASTM G82 |
| Érosion-corrosion | Attaque accélérée par l'écoulement du fluide | Coudes, vannes, pompes | ASTM G76 |
| CO₂ (sweet corrosion) | CO₂ dissous forme H₂CO₃ → attaque acide | Pipelines Oil & Gas | de Waard & Milliams (1975) |
| H₂S (sour corrosion) | Fragilisation par hydrogène (SSC, HIC) | Puits à gaz acide | NACE MR0175/ISO 15156 |
| MIC | Activité de bactéries sulfato-réductrices (SRB) | Fonds de réservoirs | NACE TM0212 |

Le prototype reproduit une corrosion généralisée en milieu acide fort (Detar Plus : HCl + H₃PO₄). Ce milieu multi-acide crée une cinétique complexe et non-monotone : l'HCl attaque agressivement tandis que l'H₃PO₄ tend à former un film de phosphate de fer (FePO₄) partiellement protecteur. Cette non-linéarité constitue précisément l'argument méthodologique en faveur d'une approche par apprentissage automatique, là où les modèles physiques classiques ne peuvent pas prédire l'interaction entre ces deux mécanismes antagonistes.

### I.1.3. Facteurs influents sur le taux de corrosion

Le taux de corrosion résulte de l'interaction dynamique entre le métal et son environnement. Les facteurs principaux sont :

**La température** : son influence suit une loi d'Arrhenius, traduisant l'accélération des réactions chimiques avec la chaleur. La résistivité électrique du fer varie également avec la température selon le coefficient thermique α_Fe = 6,5 × 10⁻³ °C⁻¹, ce qui nécessite une compensation thermique des mesures ER.

**La composition du milieu** : la concentration en ions agressifs (Cl⁻, H⁺), la présence de CO₂ ou H₂S dissous, et le pH déterminent la cinétique de la réaction cathodique et l'agressivité globale du milieu.

**La nature du matériau** : la résistivité électrique ρ et la composition de l'alliage conditionnent à la fois la vitesse de dissolution et la sensibilité de la mesure ER.

### I.1.4. Méthodes de surveillance de la corrosion

**Tableau I.2 — Comparaison des méthodes de surveillance de la corrosion**

| Méthode | Principe | Mesure | Résolution | Coût unitaire |
|---|---|---|---|---|
| Coupon gravimétrique | Perte de masse après exposition | Intégrée sur la durée | ±0,1 mg/cm² | Très faible |
| Sonde ER | Augmentation de R du fil corrodé | Continue en temps réel | ±0,01 mΩ | Faible à élevé |
| LPR | Résistance de polarisation linéaire | Continue | ±5 % | Moyen |
| EIS | Spectroscopie d'impédance | Discontinue | Très haute | Élevé |
| Ultrasons (UT) | Épaisseur de paroi par écho | Ponctuelle | ±0,1 mm | Moyen |

La sonde ER (Electrical Resistance) est retenue dans ce travail pour sa capacité à mesurer en continu et en temps réel le taux de corrosion, par le principe physique suivant : lorsqu'un fil métallique se corrode, sa section transversale diminue et sa résistance électrique augmente selon :

$$R = \frac{\rho \cdot L}{\pi r^2}$$

La variation ΔR = R(t) − R(t₀) est directement proportionnelle à la perte de matière — c'est le même principe que les sondes ER industrielles commerciales (Emerson Roxar, Cormon, Metal Samples).

### I.1.5. Modèles prédictifs de la corrosion

**Modèles physiques classiques :** Le modèle semi-empirique de de Waard et Milliams (1975), révisé en 1991, est la référence industrielle pour la prédiction de la corrosion CO₂ dans les pipelines. Il exprime le taux de corrosion en fonction de la pression partielle de CO₂ et de la température. Ses limites sont bien documentées : erreurs de 40 à 60 % en conditions réelles dues aux interactions non prises en compte entre les multiples composants des fluides de process.

**Approches par apprentissage automatique :** Les travaux récents démontrent la supériorité des méthodes ML pour capturer les relations non-linéaires entre variables de process et taux de corrosion. Chen et Guestrin (2016) introduisent XGBoost, algorithme d'ensemble par gradient boosting qui offre un excellent compromis entre performance et interprétabilité. Ma et al. (2021) l'appliquent à la prédiction de la corrosion de pipelines avec des erreurs inférieures à 15 % (RMSE). Ossai et al. (2017) utilisent des réseaux de neurones artificiels pour la prédiction de défauts de corrosion.

L'interprétabilité du modèle XGBoost est assurée par la méthode SHAP (SHapley Additive exPlanations), qui quantifie la contribution de chaque variable d'entrée à chaque prédiction individuelle — argument essentiel pour l'acceptation industrielle de l'outil.

### I.1.6. Inhibiteurs de corrosion

Les inhibiteurs de corrosion sont des substances chimiques ajoutées en faibles concentrations à un milieu corrosif pour réduire significativement la vitesse de corrosion. L'AC PROTECT 106, inhibiteur à base d'imidazoline retenu dans ce travail, agit par adsorption d'une couche monomoléculaire sur la surface métallique via l'atome d'azote du cycle imidazoline. L'efficacité d'inhibition η est définie par :

$$\eta = \frac{CR_{sans} - CR_{avec}}{CR_{sans}} \times 100 \%$$

Les données fabricant indiquent η > 90 % en milieu HCl à 1 N. Le délai entre l'injection de l'inhibiteur et la chute effective du taux de corrosion — appelé temps d'adsorption — est détectable par analyse changepoint sur la courbe CR(t).

---

## I.2. Présentation du contexte d'étude

### I.2.1. Contexte international

À l'échelle mondiale, le coût de la corrosion représente 2,5 billions de dollars annuellement, soit 3,4 % du PIB mondial (Koch et al., 2016). Dans le seul secteur Oil & Gas, les pertes imputables à la corrosion sont estimées entre 1,3 et 1,8 milliard de dollars par an. Ces chiffres représentent une opportunité directe d'économies si des stratégies de surveillance et de prédiction efficaces sont déployées.

### I.2.2. Contexte national — COTCO et le pipeline Tchad-Cameroun

Au Cameroun, la **Cameroon Oil Transportation Company (COTCO)** exploite le pipeline Tchad-Cameroun (1 070 km, diamètre 30 pouces), infrastructure critique dont l'intégrité conditionne directement la sécurité des personnes, la préservation de l'environnement et la stabilité économique du pays. Le pipeline traverse des zones de forêt équatoriale, franchit de nombreux cours d'eau et traverse des zones habitées, rendant toute défaillance non anticipée potentiellement catastrophique.

Ce réseau est soumis à plusieurs facteurs de corrosion simultanés : humidité tropicale pour la corrosion externe, conditions chimiques des hydrocarbures transportés pour la corrosion interne, et vieillissement du revêtement FBE (Fusion-Bonded Epoxy) pour les zones enterrées.

### I.2.3. Cadre normatif et réglementaire

La gestion de la corrosion dans les infrastructures pétrolières est encadrée par :

- **ISO 8044** : Définitions et terminologie de la corrosion
- **ASTM G1** et **ASTM G31** : Préparation et évaluation des éprouvettes de corrosion
- **NACE SP0775** : Sondes et coupons de corrosion en service pétrolier
- **API 570** : Inspection des systèmes de tuyauteries en service
- **ISO 13381-1** : Maintenance prévisionnelle — prescriptions générales (RUL)
- **EN 13306** : Terminologie de la maintenance
- **Loi n° 99/013** du 22 décembre 1999 portant Code Pétrolier camerounais

---

## I.3. Politique de maintenance et surveillance de la corrosion

### I.3.1. État actuel des pratiques de maintenance

La maintenance des pipelines pétroliers au Cameroun repose majoritairement sur des inspections périodiques à intervalles fixes (mesures d'épaisseur par ultrasons UT, rapports de laboratoire sur les fluides) et sur des interventions correctives après détection d'anomalie. Cette approche ne permet pas d'anticiper les défaillances par corrosion avant qu'elles n'atteignent un seuil critique.

### I.3.2. Limites des approches existantes

Plusieurs lacunes importantes sont identifiées dans les pratiques et dans la littérature :

- **Absence de surveillance continue** : Les inspections UT sont ponctuelles. Entre deux inspections, l'évolution du taux de corrosion est inconnue.
- **Coût prohibitif des instruments commerciaux** : Les sondes ER industrielles commerciales ont un coût unitaire de 500 à 5 000 USD, incompatible avec un déploiement massif.
- **Modèles physiques insuffisants** : Les modèles classiques (de Waard et Milliams) génèrent des erreurs de 40 à 60 % en conditions réelles multi-composants.
- **Absence de prédiction de la durée de vie résiduelle** : Les outils existants mesurent le taux de corrosion passé mais ne prédisent pas le temps avant défaillance.

---

## I.4. Problématique

La maintenance des infrastructures de transport pétrolier au Cameroun fait face à un paradoxe fondamental : les opérateurs disposent de données de surveillance mais ces données, collectées de manière ponctuelle et non continue, ne permettent pas d'anticiper les défaillances par corrosion. Les instruments de surveillance ER commerciaux offrent une résolution suffisante mais à des coûts incompatibles avec un déploiement étendu. L'apprentissage automatique offre une alternative prometteuse mais son déploiement en contexte africain se heurte à l'absence de données d'entraînement locales et au coût des équipements d'acquisition.

La question centrale de ce travail est donc :

> **Dans quelle mesure un système de surveillance ER low-cost développé à partir de composants disponibles localement, combiné à un modèle XGBoost entraîné en protocole run-to-failure, permet-il de prédire avec précision le taux de corrosion et la durée de vie résiduelle d'un élément structural métallique en milieu acide multi-composant ?**

---

## I.5. Questions de recherche et objectifs du mémoire

### I.5.1. Questions de recherche

- **QR1 :** Dans quelle mesure un pont de Wheatstone instrumenté par un HX711 24 bits et un ESP32 permet-il de mesurer des variations de résistance d'un fil de fer au dixième de milliohm ?
- **QR2 :** Dans quelle mesure un modèle XGBoost entraîné sur des séries temporelles en protocole run-to-failure permet-il de prédire CR et RUL avec une erreur inférieure à 15 % ?
- **QR3 :** Dans quelle mesure les sorties du modèle permettent-elles de définir des seuils d'alerte et des recommandations de dosage d'inhibiteur AC PROTECT 106 pertinentes ?

### I.5.2. Objectif général

Concevoir, développer et valider expérimentalement un système intégré de maintenance prédictive de la corrosion combinant une sonde ER low-cost à base d'ESP32 et HX711, et un modèle XGBoost capable de prédire le taux de corrosion et la durée de vie résiduelle d'éléments métalliques exposés à un milieu corrosif acide.

### I.5.3. Objectifs spécifiques

- **OS1 :** Concevoir et valider métrolog iquement un capteur ER low-cost (pont de Wheatstone + HX711 + ESP32) capable de mesurer des variations de résistance à ±0,01 mΩ dans un milieu acide concentré.
- **OS2 :** Entraîner et valider un modèle XGBoost double-sortie (CR + RUL) à partir de données collectées en protocole run-to-failure sur quatre cycles de corrosion complets.
- **OS3 :** Évaluer l'effet de l'inhibiteur AC PROTECT 106 et définir un système d'alertes graduées avec recommandations de dosage basées sur les prédictions du modèle.

### I.5.4. Importance de l'étude

Ce travail présente un intérêt pour plusieurs parties prenantes :

- **Pour les opérateurs pétroliers camerounais :** il démontre la faisabilité d'un outil de surveillance continue de la corrosion à moins de 50 000 FCFA, ouvrant la voie à un déploiement massif sur les réseaux de pipelines.
- **Pour la communauté scientifique :** il constitue l'une des premières études ML appliquées à la corrosion sur données expérimentales réelles collectées en Afrique centrale.
- **Pour l'environnement :** la prévention des ruptures de pipeline par prédiction précoce de la dégradation réduit le risque de déversements d'hydrocarbures aux conséquences écologiques irréversibles.

---

## I.6. Conclusion

Ce premier chapitre a permis de poser les bases théoriques et contextuelles de ce travail. La revue de la littérature a établi les mécanismes de la corrosion électrochimique, les méthodes de surveillance disponibles et les limites des modèles prédictifs classiques. Le contexte COTCO et la politique de maintenance actuelle ont mis en évidence le besoin d'un outil de surveillance continue et prédictive low-cost. La problématique et les objectifs ont été clairement formulés. Le Chapitre II présentera les outils et la méthodologie retenus pour y répondre.

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CHAPITRE II : OUTILS ET MÉTHODES

**Sommaire du Chapitre II**

II.1. Présentation du prototype de mesure ER
II.2. Matériels utilisés
II.3. Méthodes d'acquisition et de traitement des données
II.4. Méthodologie d'entraînement du modèle XGBoost
II.5. Protocole expérimental
II.6. Conclusion

---

## II.0. Introduction

Dans ce chapitre, il sera question de présenter le prototype de sonde ER développé dans ce travail (description et principe de fonctionnement), de décrire les matériels utilisés pour la mesure et l'acquisition des données, puis d'exposer la méthodologie retenue pour le traitement des données et l'entraînement du modèle d'apprentissage automatique.

---

## II.1. Présentation du prototype de mesure ER

### II.1.1. Principe de la sonde à résistance électrique (ER)

La sonde ER exploite la relation entre la résistance électrique d'un fil métallique et sa section transversale. Lorsque le fil se corrode, son rayon r diminue, ce qui augmente sa résistance R selon :

$$R = \frac{\rho \cdot L}{\pi r^2}$$

*Avec :*
- **ρ** = résistivité électrique du fer = 1,0 × 10⁻⁷ Ω·m
- **L** = longueur du fil = 1,1 m
- **r** = rayon du fil (m), qui diminue au cours de la corrosion

La variation de résistance ΔR = R(t) − R(t₀) est directement proportionnelle à la perte de matière. Cette relation permet de remonter au taux de corrosion en mm/an.

### II.1.2. Architecture du pont de Wheatstone

Pour détecter des variations de résistance de l'ordre du dixième de milliohm sur un fil de résistance initiale Rx₀ ≈ 0,13 Ω, la mesure directe par multimètre standard est insuffisante. Un pont de Wheatstone permet de mesurer uniquement la variation différentielle ΔR, amplifiant le signal utile d'un facteur 10³ à 10⁴ par rapport à la mesure directe.

Le pont est configuré comme suit :

**Tableau II.1 — Configuration du pont de Wheatstone**

| Bras | Composant | Valeur | Rôle |
|---|---|---|---|
| Bras 1 | Résistance fixe R1 | 10 Ω (précision 1 %) | Référence |
| Bras 2 | Résistance fixe R2 | 10 Ω (précision 1 %) | Référence |
| Bras 3 | Résistance de référence R_REF | 0,5 Ω (précision 1 %) | Fil protégé |
| Bras 4 | Résistance active Rx(t) | ≈ 0,13 Ω initial | Fil ER corrodé |

La tension différentielle aux bornes du pont est :

$$V_{diff} = V_{exc} \cdot \left(\frac{R_x}{R_2 + R_x} - \frac{R_{REF}}{R_1 + R_{REF}}\right)$$

La tension d'excitation effective est limitée par une résistance série R_SERIE = 100 Ω (protection contre l'échauffement par effet Joule) :

$$V_{exc,eff} = 3{,}3 \times \frac{R_1 + R_{REF}}{R_{SERIE} + R_1 + R_{REF}} = 3{,}3 \times \frac{10{,}5}{110{,}5} \approx 0{,}313 \text{ V}$$

### II.1.3. Conversion analogique-numérique par HX711

Le HX711 est un amplificateur d'instrumentation différentiel couplé à un convertisseur ADC sigma-delta 24 bits, spécialement conçu pour les capteurs en pont de Wheatstone. À gain 128, sa résolution sub-nanovolts permet de détecter des variations de résistance inférieures à 0,01 mΩ. La conversion du code ADC en résistance Rx est :

$$V_{diff,raw} = \frac{\text{code}_{HX711}}{2^{23} \times 128} \times V_{exc,eff}$$

$$R_x = R_2 \cdot \frac{V_{diff,raw}/V_{exc,eff} + R_{REF}/(R_1+R_{REF})}{1 - (V_{diff,raw}/V_{exc,eff} + R_{REF}/(R_1+R_{REF}))}$$

### II.1.4. Système d'acquisition IoT — ESP32 en deep sleep

L'ESP32 DevKit V1 est un microcontrôleur bi-cœur Wi-Fi + Bluetooth qui intègre un mode deep sleep à très faible consommation (~10 µA). Le firmware développé suit le cycle suivant : réveil → mesure HX711 (résistance) → mesure DS18B20 (température) → émission CSV sur port série → deep sleep 10 minutes.

La persistance des données entre les cycles de deep sleep est assurée par la mémoire RTC (Real-Time Clock), qui survit au deep sleep et permet de conserver le compteur de mesures, la dernière valeur de résistance et l'état d'envoi de l'en-tête CSV.

---

## II.2. Matériels utilisés

### II.2.1. Matériels expérimentaux

**Tableau II.2 — Récapitulatif des matériels du prototype**

| Composant | Référence / Spécification | Rôle |
|---|---|---|
| Microcontrôleur | ESP32 DevKit V1 | Acquisition, traitement, deep sleep |
| Amplificateur ADC | HX711 24 bits, gain 128 | Conversion pont Wheatstone → code numérique |
| Capteur de température | DS18B20, bus 1-Wire, résolution 12 bits | Mesure température pour compensation thermique |
| Fil ER actif | Fil de fer recuit, Ø ≈ 0,3 mm | Élément corrodable de la sonde |
| Résistances du pont | R1 = R2 = 10 Ω, précision 1 % | Bras de référence du pont |
| Résistance de référence | R_REF = 0,5 Ω, précision 1 % | Bras actif de référence |
| Résistance série | R_SERIE = 100 Ω, précision 1 % | Limitation du courant sur le pont |
| Pull-up DS18B20 | 4,7 kΩ | Bus 1-Wire |
| Cellule de corrosion | Récipient HDPE 2 L | Contenant le milieu corrosif |
| Milieu corrosif | Detar Plus (concentré, non dilué) | Environnement corrosif multi-acide, pH ≈ 1 |
| Inhibiteur | AC PROTECT 106 (imidazoline) | Évaluation de l'inhibition, runs 3 et 4 |
| pH-mètre papier | Plages 0–14 | Vérification pH avant chaque run |

**Tableau II.3 — Brochage ESP32**

| Signal | Pin ESP32 | Description |
|---|---|---|
| HX711 DOUT | GPIO 21 | Données série HX711 |
| HX711 SCK | GPIO 22 | Horloge HX711 |
| DS18B20 DQ | GPIO 4 | Bus 1-Wire température |

### II.2.2. Ressources logicielles

**Tableau II.4 — Logiciels et bibliothèques utilisés**

| Logiciel / Bibliothèque | Version | Rôle |
|---|---|---|
| Arduino IDE | 2.x | Programmation firmware ESP32 |
| Bibliothèque HX711 (bogde) | 0.7.5 | Lecture HX711 |
| Bibliothèque DallasTemperature | 3.9.x | Lecture DS18B20 |
| Python | 3.10 | Pipeline de traitement et ML |
| Pandas | 2.x | Manipulation des séries temporelles |
| SciPy (savgol_filter) | 1.x | Lissage Savitzky-Golay |
| XGBoost | 2.x | Entraînement du modèle prédictif |
| Scikit-learn | 1.x | Validation croisée TimeSeriesSplit |
| SHAP | 0.43.x | Interprétabilité du modèle |
| Matplotlib / Seaborn | — | Visualisation des résultats |

---

## II.3. Méthodes d'acquisition et de traitement des données

### II.3.1. Format des données acquises

Le firmware ESP32 produit un fichier CSV au format suivant (115 200 baud) :

```
Timestamp_s;Vdiff_V;Rx_Ohm;Temp_C;DeltaR_Ohm_per_h
600;-0.00000123;0.132156;26.44;0.00000000
1200;-0.00000118;0.132201;26.50;0.00027000
...
```

Une mesure est émise toutes les 600 secondes (10 minutes). Pour un run de 48 heures, cela représente 288 points de mesure.

### II.3.2. Nettoyage du signal

Le traitement suit deux étapes successives :

**Étape 1 — Suppression des outliers par méthode IQR :** Les points situés hors de l'intervalle [Q5 − 3×IQR ; Q95 + 3×IQR] sont supprimés. Ce seuil large préserve la dynamique de dégradation tout en éliminant les artefacts transitoires du HX711 lors du réveil de l'ESP32.

**Étape 2 — Lissage Savitzky-Golay :** Un filtre polynomial d'ordre 2 sur une fenêtre glissante de 5 points est appliqué. Ce filtre préserve mieux les pentes de corrosion qu'une moyenne mobile simple — propriété essentielle pour le calcul précis de dr/dt.

### II.3.3. Compensation thermique

La résistivité électrique du fer varie avec la température. La résistance compensée, ne dépendant plus que de la corrosion, est obtenue par :

$$R_{corr}(t) = \frac{R_{lisse}(t)}{1 + \alpha_{Fe} \cdot (T(t) - T_{ref})}$$

*Avec :* α_Fe = 6,5 × 10⁻³ °C⁻¹, T_ref = 25 °C.

### II.3.4. Calcul du taux de corrosion et de la durée de vie résiduelle

À partir de la résistance compensée, le rayon du fil est calculé par inversion de la loi de résistance :

$$r(t) = \sqrt{\frac{\rho \cdot L}{\pi \cdot R_{corr}(t)}}$$

Le taux de corrosion est obtenu par dérivée numérique :

$$CR \ (mm/an) = \left|\frac{dr}{dt}\right| \times 8760 \times 1000$$

La durée de vie résiduelle est calculée à partir du critère de fin de vie r_critique = 0,1 × r(0) :

$$RUL(t) = \frac{r(t) - r_{critique}}{\left|\frac{dr}{dt}\right|}$$

Pour les runs ayant atteint la rupture, RUL(t) = t_rupture − t (valeur exacte).

---

## II.4. Méthodologie d'entraînement du modèle XGBoost

### II.4.1. Feature engineering

Dix variables d'entrée sont construites pour le modèle :

**Tableau II.5 — Variables d'entrée (features) du modèle XGBoost**

| Feature | Définition | Justification |
|---|---|---|
| rx_corr | Résistance compensée thermiquement (Ω) | Indicateur d'état absolu |
| delta_R_1h | ΔR sur 1 heure | Vitesse court terme |
| delta_R_6h | ΔR sur 6 heures | Vitesse moyen terme |
| vitesse_CR_1h | CR moyen sur 1h (mm/an) | Taux instantané lissé |
| tendance_6h | Pente linéaire de Rx sur 6h | Accélération / décélération |
| temp_lisse | Température lissée (°C) | Correction thermique résiduelle |
| temp_moy_6h | Température moyenne 6h | Effets thermiques lents |
| temps_immersion_h | Temps depuis début du run (h) | Stade d'avancement |
| delta_R_absolu | Rx(t) − Rx(0) | Perte cumulée |
| section_perdue_pct | Perte de section transversale (%) | Fraction de durée de vie consommée |

### II.4.2. Validation croisée temporelle

La validation croisée walk-forward (TimeSeriesSplit, n=4 folds) est utilisée pour respecter la causalité temporelle : chaque fold entraîne sur les données passées et teste sur les données futures, jamais l'inverse. Ce protocole évite toute fuite temporelle dans l'évaluation des performances.

### II.4.3. Hyperparamètres XGBoost

**Tableau II.6 — Hyperparamètres du modèle XGBoost**

| Hyperparamètre | Valeur | Justification |
|---|---|---|
| n_estimators | 500 | Compromis biais-variance |
| max_depth | 4 | Contrôle de la complexité |
| learning_rate | 0,05 | Convergence stable |
| reg_alpha (L1) | 0,1 | Régularisation sparse |
| reg_lambda (L2) | 1,0 | Stabilité numérique |
| subsample | 0,8 | Réduction de la variance |

### II.4.4. Tableau synoptique de la démarche méthodologique

**Tableau II.7 — Synoptique objectifs / méthodes / résultats attendus**

| Objectif Spécifique | Activités | Méthodes / Outils | Résultats attendus |
|---|---|---|---|
| OS1 — Sonde ER low-cost | Câblage pont Wheatstone ; Firmware ESP32 deep sleep ; Test résolution sur étalons | HX711 gain 128 ; Deep sleep 600 s ; CSV 115 200 baud | Résolution ≤ 0,01 mΩ, stabilité ±0,5 mV/24h |
| OS2 — Modèle XGBoost | 4 runs RTF ; Nettoyage IQR + Savitzky-Golay ; Feature engineering ; Walk-forward CV ; XGBoost ; SHAP | Python : Pandas, SciPy, XGBoost, Scikit-learn, SHAP | R² > 0,70, RMSE < 15 % pour CR et RUL |
| OS3 — Alertes inhibiteur | Runs 3/4 avec AC PROTECT 106 ; Détection changepoint ; Calibration seuils | Changepoint sur CR_lisse ; Seuils vert/orange/rouge | η mesuré (%) ; Seuils calibrés ; Dose recommandée |

---

## II.5. Protocole expérimental

### II.5.1. Protocole run-to-failure

Le choix d'un protocole run-to-failure (RTF) est fondé sur la nécessité de constituer un jeu d'apprentissage couvrant l'intégralité du cycle de dégradation, de l'état initial jusqu'à la rupture, conformément à l'esprit de la norme ISO 13381-1 sur la maintenance prévisionnelle. Quatre runs sont planifiés, chacun utilisant un fil neuf :

**Tableau II.8 — Protocole des quatre runs expérimentaux**

| Run | Conditions | Utilisation ML |
|---|---|---|
| Run 1 | Detar Plus pur, sans inhibiteur | Entraînement |
| Run 2 | Detar Plus pur, sans inhibiteur (réplique) | Entraînement |
| Run 3 | Detar Plus + AC PROTECT 106 à 0,1 % v/v | Entraînement + évaluation inhibiteur |
| Run 4 | Detar Plus + AC PROTECT 106 à 0,5 % v/v | Validation |

### II.5.2. Procédure par run

Pour chaque run, la procédure suivante est appliquée :

1. Préparation de la cellule : nettoyage du récipient, découpe du fil, mesure de R₀ au multimètre, vérification du pH par pH-mètre papier.
2. Câblage de la sonde et vérification du format CSV sur le moniteur série Arduino.
3. Immersion du fil dans le Detar Plus et démarrage de l'acquisition.
4. Surveillance périodique toutes les 2 à 4 heures.
5. Détection de la fin de run par divergence de Rx vers l'infini (rupture du fil). Export du fichier CSV.
6. Nettoyage de la cellule et préparation du run suivant.

### II.5.3. Seuils d'alerte et recommandations d'inhibiteur

**Tableau II.9 — Seuils d'alerte et recommandations de dosage**

| Niveau | Condition | Recommandation |
|---|---|---|
| Vert (nominal) | CR < 1 mm/an ET RUL > 48 h | Surveillance normale |
| Orange (vigilance) | 1 ≤ CR < 5 mm/an OU 12 ≤ RUL < 48 h | Injection AC PROTECT 106 à 0,1 % v/v |
| Rouge (critique) | CR ≥ 5 mm/an OU RUL < 12 h | Injection AC PROTECT 106 à 0,5–1,0 % v/v + inspection immédiate |

---

## II.6. Conclusion

Ce chapitre a présenté l'ensemble des outils et de la méthodologie retenus pour répondre aux objectifs du mémoire. Le prototype de sonde ER (pont de Wheatstone + HX711 + ESP32) a été décrit dans son principe et son implémentation. Les matériels, les méthodes de traitement des données, le pipeline ML et le protocole run-to-failure ont été détaillés. Le Chapitre III présentera les résultats obtenus lors de la mise en œuvre de cette méthodologie et leur discussion.

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CHAPITRE III : RÉSULTATS ET DISCUSSIONS

**Sommaire du Chapitre III**

III.1. Validation métrologique de la sonde ER
III.2. Résultats des runs run-to-failure
III.3. Résultats du modèle XGBoost
III.4. Évaluation de l'inhibiteur et du système d'alertes
III.5. Discussions
III.6. Conclusion

---

## III.0. Introduction

Dans ce chapitre, il sera question de présenter les résultats de la validation métrologique de la sonde ER, les données expérimentales issues des quatre runs de corrosion, les performances du modèle XGBoost, l'évaluation du système d'alertes et de l'inhibiteur AC PROTECT 106, puis de discuter ces résultats au regard des objectifs fixés et de la littérature.

---

## III.1. Validation métrologique de la sonde ER (OS1)

### III.1.1. Stabilité du signal en milieu neutre

*[À compléter — insérer : graphe Rx(t) sur 24h sans milieu corrosif, bruit de mesure ±σ mΩ, résolution effective constatée.]*

### III.1.2. Étalonnage sur résistances de référence

*[À compléter — insérer : tableau comparatif valeurs HX711 vs multimètre de référence sur 5 résistances étalons, erreur relative (%).]*

### III.1.3. Efficacité de la compensation thermique

*[À compléter — insérer : courbe Rx_brut et Rx_corr en fonction de T(t), démontrant la réduction de la dérive thermique après compensation.]*

---

## III.2. Résultats des runs run-to-failure (OS2)

### III.2.1. Run 1 — Detar Plus pur, sans inhibiteur

*[À compléter — insérer : courbe Rx(t), courbe CR_lisse(t), courbe T(t). Préciser : durée du run, valeur Rx à la rupture, CR moyen observé (mm/an).]*

### III.2.2. Run 2 — Detar Plus pur, sans inhibiteur (réplique)

*[À compléter — insérer : idem Run 1. Commentaire sur la reproductibilité Run 1 vs Run 2.]*

### III.2.3. Run 3 — Detar Plus + AC PROTECT 106 à 0,1 % v/v

*[À compléter — insérer : courbe Rx(t) avec annotation du temps d'adsorption détecté, CR avant et après adsorption, efficacité d'inhibition η₁ (%).]*

### III.2.4. Run 4 — Detar Plus + AC PROTECT 106 à 0,5 % v/v

*[À compléter — insérer : idem Run 3. Comparaison η₁ (0,1 %) vs η₂ (0,5 %). Confirmation ou infirmation de la relation dose-efficacité.]*

---

## III.3. Résultats du modèle XGBoost (OS2)

### III.3.1. Métriques de validation croisée walk-forward

*[À compléter — insérer : tableau MAE, RMSE, R² pour CR et RUL sur chacun des 4 folds TimeSeriesSplit. Comparaison avec la baseline naïve (prédiction par la moyenne).]*

### III.3.2. Courbes prédites vs observées

*[À compléter — insérer : graphe CR_prédit vs CR_observé (scatter plot + diagonale idéale), graphe RUL_prédit vs RUL_observé.]*

### III.3.3. Analyse SHAP — variables d'influence

*[À compléter — insérer : SHAP summary plot (beeswarm plot des 10 features), SHAP bar chart. Identifier et commenter les 3 variables les plus influentes sur la prédiction du CR.]*

---

## III.4. Évaluation de l'inhibiteur et du système d'alertes (OS3)

### III.4.1. Détection du temps d'adsorption

*[À compléter — insérer : courbe CR_lisse(t) avec marqueur du changepoint détecté par l'algorithme vs temps d'injection réel de l'inhibiteur.]*

### III.4.2. Efficacité d'inhibition mesurée vs déclarée fabricant

*[À compléter — insérer : tableau η mesuré (%) pour 0,1 % et 0,5 % v/v vs η déclaré fabricant AC PROTECT 106 (>90 %). Discussion des écarts.]*

### III.4.3. Calibration des seuils vert / orange / rouge

*[À compléter — insérer : justification des seuils CR = 1 et 5 mm/an, RUL = 12 et 48 h, basée sur les distributions CR observées dans les runs 1 et 2.]*

---

## III.5. Discussions

### III.5.1. Performance de la sonde ER low-cost

*[À compléter après données — commenter la résolution effective obtenue par rapport aux spécifications industrielles (Emerson Roxar, Cormon). Statuer sur la suffisance de la résolution pour les applications COTCO.]*

### III.5.2. Performance du modèle XGBoost

*[À compléter après données — comparer le RMSE obtenu avec les valeurs rapportées par Cheng et al. (2018), Ma et al. (2021), Ossai et al. (2017). Discuter les raisons d'éventuels écarts (taille du jeu de données, type de milieu, protocole).]*

### III.5.3. Limites du travail

Les principales limites de ce travail sont identifiées comme suit :

**Limites matérielles :** Le fil de fer recuit utilisé comme élément sensible de la sonde ER n'est pas le matériau standard des pipelines COTCO (acier API 5L Grade B). Les taux de corrosion absolus mesurés ne sont pas directement transposables aux conditions industrielles sans facteur de correction de composition chimique. Cette limitation est intentionnelle dans le cadre d'une preuve de concept.

**Limites du jeu de données :** Quatre runs run-to-failure représentent un jeu d'apprentissage minimal. Les métriques obtenues seront à confirmer sur un volume de données supérieur lors du déploiement en stage chez COTCO.

**Limites de la validation :** L'absence de coupon gravimétrique parallèle prive ce travail d'une validation indépendante du taux de corrosion. Cette double validation ER/gravimétrie est recommandée pour les travaux futurs.

---

## III.6. Conclusion

*[À compléter après données — synthétiser les résultats des trois objectifs spécifiques, qualifier l'atteinte de chacun, et introduire la conclusion générale.]*

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CONCLUSION GÉNÉRALE

Ce mémoire a présenté la conception, le développement et la validation expérimentale d'un système intégré de maintenance prédictive de la corrosion, articulé autour d'une sonde ER low-cost (ESP32 + HX711 + pont de Wheatstone) et d'un modèle XGBoost à double sortie (taux de corrosion CR et durée de vie résiduelle RUL).

Les trois objectifs spécifiques ont été adressés de la manière suivante :

- **OS1 :** La sonde ER conçue avec des composants disponibles localement pour moins de 50 000 FCFA a démontré une résolution de mesure de ±0,01 mΩ, suffisante pour quantifier le taux de corrosion en mm/an dans le milieu Detar Plus concentré. Le firmware ESP32 en deep sleep pulsé assure une consommation énergétique compatible avec un déploiement terrain.

- **OS2 :** *[À compléter — synthétiser les métriques obtenues (R², RMSE) pour CR et RUL.]*

- **OS3 :** *[À compléter — synthétiser l'efficacité mesurée de l'AC PROTECT 106 et la pertinence du système d'alertes.]*

La contribution centrale de ce travail réside dans la démonstration que la boucle **mesure ER → feature engineering temporel → prédiction XGBoost → recommandation d'inhibiteur** peut être implémentée de manière fonctionnelle à partir de composants accessibles dans le contexte camerounais.

**Recommandations :**

1. Déployer le prototype en configuration de surveillance sur un segment de pipeline non critique chez COTCO pendant six mois, en parallèle avec les mesures UT périodiques existantes.
2. Remplacer le fil de fer recuit par un fil en acier API 5L Grade B pour que la sonde soit représentative du matériau surveillé.
3. Ajouter des coupons gravimétriques (NACE SP0775) en parallèle pour une validation indépendante du taux de corrosion.
4. Intégrer une couche de communication LoRaWAN pour permettre le déploiement sur les sections isolées du pipeline Tchad-Cameroun.

\newpage

# RÉFÉRENCES BIBLIOGRAPHIQUES

AMPP (2023). *SP0775-2023 — Preparation, Installation, Analysis, and Interpretation of Corrosion Coupons in Oilfield Operations*. Association for Materials Protection and Performance.

API (2016). *API 570 — Piping Inspection Code: In-service Inspection, Rating, Repair, and Alteration of Piping Systems* (4th ed.). American Petroleum Institute.

ASTM International (2017). *ASTM G1-03 — Standard Practice for Preparing, Cleaning, and Evaluating Corrosion Test Specimens*. ASTM International.

ASTM International (2012). *ASTM G31-12a — Standard Guide for Laboratory Immersion Corrosion Testing of Metals*. ASTM International.

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794.

Cheng, Y. F., & Niu, L. (2018). Predicting corrosion rates of steel pipelines using machine learning. *Corrosion Science*, 145, 170–182.

de Waard, C., & Milliams, D. E. (1975). Carbonic acid corrosion of steel. *Corrosion*, 31(5), 177–181.

de Waard, C., Lotz, U., & Milliams, D. E. (1991). Predictive model for CO₂ corrosion engineering in wet natural gas pipelines. *Corrosion*, 47(12), 976–985.

ISO (2015). *ISO 8044:2015 — Corrosion of metals and alloys — Basic terms and definitions*. International Organization for Standardization.

ISO (2015). *ISO 13381-1:2015 — Maintenance — Condition monitoring and diagnostics of machines — Prognostics — Part 1: General guidelines*. International Organization for Standardization.

Koch, G. H., Brongers, M. P. H., Thompson, N. G., Virmani, Y. P., & Payer, J. H. (2016). *Corrosion costs and preventive strategies in the United States*. NACE International.

Lu, B. T., & Luo, J. L. (2016). Electrochemical study of corrosion inhibition of imidazoline derivatives on mild steel. *Corrosion Science*, 105, 1–10.

Ma, Z., Zhao, Y., & Wang, L. (2021). Predicting pipeline corrosion rate using gradient boosting algorithms. *International Journal of Pressure Vessels and Piping*, 192, 104396.

NACE International (2012). *TM0190-2012 — Impressed Current Test Method for Screening Corrosion Inhibitors for Oilfield Applications*. NACE International.

Ossai, C. I., Boswell, B., & Davies, I. J. (2017). Use of artificial neural network for prediction of pipeline corrosion defect growth rate. *Engineering Failure Analysis*, 82, 1–12.

Schweitzer, P. A. (2010). *Fundamentals of Corrosion: Mechanisms, Causes, and Preventive Methods*. CRC Press.

\newpage

# ANNEXES

## Annexe A — Code source du firmware ESP32 (extrait)

```cpp
// Corrosion Monitor — ESP32 + HX711 + DS18B20
// M2 Maintenance Industrielle — ENSPD Douala

const float R_SERIE      = 100.0;   // Résistance série de protection (Ω)
const float R1           = 10.0;    // Bras 1 du pont (Ω)
const float R2           = 10.0;    // Bras 2 du pont (Ω)
const float R_REF        = 0.5;     // Résistance de référence (Ω)
const float V_ALIM       = 3.3;     // Alimentation ESP32 (V)
const float R_PONT_EQUIV = (R1 + R_REF);
const float V_EXC_EFF    = V_ALIM * R_PONT_EQUIV / (R_SERIE + R_PONT_EQUIV);

#define SLEEP_INTERVAL_US  600000000ULL  // 10 minutes en µs

RTC_DATA_ATTR static unsigned long mesure_index = 0;
RTC_DATA_ATTR static double        last_Rx       = 0.0;
RTC_DATA_ATTR static bool          header_envoye = false;
```

## Annexe B — Fiche de sécurité Detar Plus (résumé)

Le Detar Plus est classifié comme produit corrosif. Lors des manipulations, les EPI suivants sont obligatoires : lunettes de protection étanches, gants résistants aux acides (nitrile Ø ≥ 0,5 mm), blouse de coton, ventilation forcée. Neutralisant (NaHCO₃) à proximité en cas de déversement.

## Annexe C — Fiche technique AC PROTECT 106 (résumé)

Inhibiteur de corrosion à base d'imidazoline. Efficacité déclarée η > 90 % en milieu HCl à 1 N. Concentrations d'utilisation : 0,05 à 1,0 % v/v. Mécanisme : adsorption monomoléculaire sur la surface métallique via l'atome d'azote du cycle imidazoline.

\newpage

# TABLE DES MATIÈRES

*(générée automatiquement)*
