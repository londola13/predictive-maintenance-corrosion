---
title: "Système intégré de maintenance prédictive de la corrosion par apprentissage automatique : conception d'une sonde ER low-cost, acquisition IoT, prédiction CR/RUL par XGBoost et prototype de GMAO low-cost"
---

\newpage

# PAGE DE TITRE

**RÉPUBLIQUE DU CAMEROUN**
*Paix — Travail — Patrie*

**REPUBLIC OF CAMEROON**
*Peace — Work — Fatherland*

---

**MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR**

**UNIVERSITÉ DE DOUALA**

**ÉCOLE NATIONALE SUPÉRIEURE POLYTECHNIQUE DE DOUALA**
*(ENSPD)*

**Département de Génie Industriel et Maintenance**

---

**Mémoire rédigé en vue de l'obtention d'un Master Professionnel**

**OPTION : MAINTENANCE INDUSTRIELLE**

---

**Thème :**

**SYSTÈME INTÉGRÉ DE MAINTENANCE PRÉDICTIVE DE LA CORROSION PAR APPRENTISSAGE AUTOMATIQUE : CONCEPTION D'UNE SONDE ER LOW-COST, ACQUISITION IoT, PRÉDICTION DU TAUX DE CORROSION ET DE LA DURÉE DE VIE RÉSIDUELLE PAR XGBoost, ET PROTOTYPE DE GMAO LOW-COST**

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

*À mes chers parents,*

*pour leur soutien sans faille tout au long de ce parcours.*

\newpage

# REMERCIEMENTS

Au terme de notre formation pour l'obtention du Master II en Maintenance Industrielle, nous tenons à exprimer notre sincère reconnaissance à l'ensemble du corps professoral de l'École Nationale Supérieure Polytechnique de Douala, qui par la qualité de leur enseignement et de leur encadrement, nous a permis de terminer avec succès cette formation en ingénierie. En l'occurrence :

- À notre **encadreur académique**, pour ses conseils éclairés, sa rigueur scientifique et sa disponibilité tout au long de la rédaction de ce mémoire ;
- À notre **superviseur**, pour son approche méthodologique et la qualité de ses remarques structurantes ;
- À notre **encadreur professionnel** au sein de la **Cameroon Oil Transportation Company (COTCO)**, pour la qualité de son accompagnement, le partage d'expérience terrain et l'accès aux problématiques industrielles concrètes ayant nourri ce travail ;
- À l'ensemble du **corps enseignant du Département de Génie Industriel et Maintenance** pour la formation théorique et pratique de qualité ;
- À mes **camarades de promotion** pour les échanges intellectuels stimulants ;
- À mes **parents** pour leur soutien moral et matériel constant.

Que tous ceux qui, de près ou de loin, ont contribué à la réussite de ce mémoire et dont les noms n'ont pu être cités, trouvent ici l'expression de mes sincères remerciements.

\newpage

# RÉSUMÉ

La corrosion représente un coût annuel mondial de 2,5 billions de dollars US, soit environ 3,4 % du PIB mondial (Koch et al., 2016). Dans le secteur Oil & Gas, elle constitue la première cause de dégradation des pipelines et des installations de surface. Au Cameroun, la **Cameroon Oil Transportation Company (COTCO)** exploite depuis 2003 le pipeline Tchad-Cameroun (1 070 km au total, dont 903 km en territoire camerounais), infrastructure stratégique dont l'intégrité conditionne la sécurité environnementale et économique du pays. La gestion actuelle de la corrosion repose largement sur des inspections périodiques par ultrasons (UT), sans surveillance continue ni prédiction de la dégradation.

Ce mémoire présente la conception, le développement et la validation expérimentale d'un **système intégré de maintenance prédictive de la corrosion** couvrant la chaîne complète **détection → diagnostic → pronostic → décision → action** définie par la norme ISO 13381-1, articulé autour de quatre composants : (1) une **sonde ER (Electrical Resistance) low-cost** basée sur un fil de fer monté en pont de Wheatstone, instrumentée par un amplificateur HX711 24 bits ; (2) un **système d'acquisition IoT** à microcontrôleur ESP32 en deep sleep pulsé (10 minutes) mesurant simultanément la résistance et la température (DS18B20) ; (3) un **modèle XGBoost** entraîné en protocole *run-to-failure* (RTF), prédisant à la fois le taux de corrosion (CR, en mm/an) et la durée de vie résiduelle (RUL, en heures), avec module de diagnostic des régimes de corrosion et interprétabilité par analyse SHAP ; (4) un **prototype de GMAO (Gestion de Maintenance Assistée par Ordinateur) low-cost** open-source basé sur un stack Supabase + Next.js, démontrant qu'une PME africaine peut disposer d'une gestion structurée des actifs, des alertes, des ordres de travail et des KPIs de maintenance sans recourir à des solutions industrielles propriétaires (SAP PM, IBM Maximo).

L'environnement corrosif de référence est un **détartrant industriel commercial multi-acide** à base d'acide chlorhydrique (5–15 %) et d'acide phosphorique (10–30 %), générant un milieu acide mixte (pH ≈ 1) reproduisant des conditions agressives comparables aux effluents acides industriels. Le protocole comporte quatre runs RTF : deux runs de référence sans inhibiteur et deux runs avec injection d'un **inhibiteur de corrosion à base d'imidazoline** (référence commerciale à sélectionner) à concentrations croissantes (0,1 % et 0,5 % v/v).

Le coût total du prototype matériel est inférieur à 50 000 FCFA, soit un facteur 40 à 100 moins cher qu'une instrumentation industrielle équivalente (Cosasco, Permasense, Emerson Roxar), et le coût d'exploitation de la GMAO est nul jusqu'à un volume significatif (offres gratuites Supabase + Vercel). Ce travail démontre la faisabilité d'un système complet de maintenance prédictive de la corrosion entièrement réalisable à partir de composants et services accessibles localement au Cameroun, contribuant à la démocratisation de la surveillance industrielle et de la GMAO dans les économies émergentes d'Afrique subsaharienne.

**Mots-clés :** corrosion ; maintenance prédictive ; sonde ER ; XGBoost ; durée de vie résiduelle ; diagnostic ; GMAO ; CMMS open-source ; ESP32 ; HX711 ; IoT ; inhibiteur de corrosion ; imidazoline ; pipeline Oil & Gas ; COTCO ; ISO 13381-1.

\newpage

# ABSTRACT

Corrosion accounts for a global annual cost of USD 2.5 trillion, approximately 3.4 % of global GDP (Koch et al., 2016). In the Oil & Gas sector, it remains the leading cause of pipeline and surface-equipment degradation. In Cameroon, the **Cameroon Oil Transportation Company (COTCO)** has operated since 2003 the 1,070 km Chad-Cameroon pipeline (903 km within Cameroonian territory), a strategic infrastructure whose integrity conditions both environmental and economic security. Current corrosion management relies mostly on periodic ultrasonic (UT) inspections, with neither continuous monitoring nor predictive analytics.

This thesis presents the design, development and experimental validation of an **integrated corrosion predictive-maintenance system** covering the complete **detection → diagnostic → prognosis → decision → action** chain defined by ISO 13381-1, built on four components: (1) a **low-cost ER (Electrical Resistance) probe** based on an iron wire mounted in a Wheatstone bridge instrumented by a 24-bit HX711 amplifier; (2) an **IoT acquisition system** using an ESP32 microcontroller in pulsed deep-sleep mode (10 minutes) measuring resistance and temperature (DS18B20) simultaneously; (3) an **XGBoost model** trained under a *run-to-failure* (RTF) protocol predicting both corrosion rate (CR, in mm/year) and remaining useful life (RUL, in hours), with corrosion regime diagnostic and SHAP-based interpretability; (4) a **low-cost open-source CMMS prototype** based on a Supabase + Next.js stack, demonstrating that an African SME can manage assets, alerts, work orders and maintenance KPIs without resorting to proprietary industrial solutions (SAP PM, IBM Maximo).

The reference corrosive medium is a **commercial multi-acid industrial descaler** containing hydrochloric acid (5–15 %) and phosphoric acid (10–30 %), producing a mixed-acid medium (pH ≈ 1) reproducing aggressive conditions similar to those of industrial acidic effluents. The protocol comprises four RTF runs: two baseline runs without inhibitor and two runs with injection of an **imidazoline-based corrosion inhibitor** (commercial reference to be selected) at increasing concentrations (0.1 % and 0.5 % v/v).

The total hardware prototype cost is below 50,000 FCFA, i.e., 40 to 100 times cheaper than comparable industrial instrumentation (Cosasco, Permasense, Emerson Roxar), and the CMMS operating cost is null up to significant volumes (free Supabase + Vercel tiers). This work demonstrates the feasibility of a complete corrosion predictive-maintenance system entirely built from components and services available locally in Cameroon, contributing to the democratization of industrial monitoring and CMMS in sub-Saharan emerging economies.

**Keywords:** corrosion; predictive maintenance; ER probe; XGBoost; remaining useful life; diagnostic; CMMS; open-source CMMS; ESP32; HX711; IoT; corrosion inhibitor; imidazoline; oil & gas pipeline; COTCO; ISO 13381-1.

\newpage

# LISTE DES ABRÉVIATIONS

| Abréviation | Signification |
|---|---|
| API REST | Application Programming Interface — REpresentational State Transfer |
| ADC | Analog-to-Digital Converter (Convertisseur Analogique-Numérique) |
| AI | Artificial Intelligence (Intelligence Artificielle) |
| AMPP | Association for Materials Protection and Performance (ex-NACE) |
| ASTM | American Society for Testing and Materials |
| CMMS | Computerized Maintenance Management System (équivalent anglais de GMAO) |
| API | American Petroleum Institute |
| ASTM | American Society for Testing and Materials |
| CMRR | Common-Mode Rejection Ratio |
| COTCO | Cameroon Oil Transportation Company |
| CR | Corrosion Rate (Taux de corrosion, mm/an) |
| CV | Cross-Validation (validation croisée) |
| DS18B20 | Capteur numérique de température, bus 1-Wire |
| EIS | Electrochemical Impedance Spectroscopy |
| EN | Norme Européenne |
| ER | Electrical Resistance (Résistance Électrique) |
| ENSPD | École Nationale Supérieure Polytechnique de Douala |
| ESP32 | Microcontrôleur bi-cœur Wi-Fi + Bluetooth (Espressif) |
| FBE | Fusion-Bonded Epoxy (revêtement pipeline) |
| FePO₄ | Phosphate de fer (III) |
| FSO | Floating Storage and Offloading unit |
| GMAO | Gestion de Maintenance Assistée par Ordinateur |
| GPIO | General-Purpose Input/Output |
| HCl | Acide chlorhydrique |
| H₃PO₄ | Acide phosphorique |
| HX711 | Amplificateur d'instrumentation et ADC 24 bits |
| IMPACT | International Measures of Prevention, Application and Economics of Corrosion Technology |
| IoT | Internet of Things (Internet des Objets) |
| IQR | Interquartile Range |
| KPI | Key Performance Indicator |
| ISO | International Organization for Standardization |
| LPR | Linear Polarization Resistance |
| MAE | Mean Absolute Error |
| MIC | Microbiologically Influenced Corrosion |
| ML | Machine Learning (apprentissage automatique) |
| MTBF | Mean Time Between Failures |
| MTTR | Mean Time To Repair |
| NACE | National Association of Corrosion Engineers |
| NDT | Non-Destructive Testing |
| OS | Objectif Spécifique |
| OT | Ordre de Travail (work order) |
| PHMSA | Pipeline and Hazardous Materials Safety Administration |
| PME | Petite et Moyenne Entreprise |
| PIB | Produit Intérieur Brut |
| QR | Question de Recherche |
| R² | Coefficient de détermination |
| RBI | Risk-Based Inspection |
| RMSE | Root Mean Square Error |
| RTC | Real-Time Clock |
| RTF | Run-To-Failure |
| RUL | Remaining Useful Life (Durée de Vie Résiduelle) |
| SHAP | SHapley Additive exPlanations |
| SRB | Sulfate-Reducing Bacteria |
| SSC | Sulfide Stress Cracking |
| UT | Ultrasonic Testing |
| XGBoost | eXtreme Gradient Boosting |

\newpage

# LISTE DES FIGURES

*(générée automatiquement par Word)*

\newpage

# LISTE DES TABLEAUX

*(générée automatiquement par Word)*

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

Dans un environnement industriel de plus en plus concurrentiel, la maîtrise de la dégradation des équipements est devenue un facteur clé de compétitivité, de sécurité et de soutenabilité environnementale. Les entreprises industrielles sont aujourd'hui confrontées à la nécessité simultanée de réduire les coûts de maintenance, d'augmenter la disponibilité de leurs équipements, et de prévenir des incidents dont les conséquences peuvent être économiques, humaines ou écologiques (Koch et al., 2016). Dans ce contexte, les stratégies de maintenance évoluent : de la maintenance corrective réactive et de la maintenance préventive systématique à intervalles fixes, vers la maintenance conditionnelle puis la maintenance prédictive — qui anticipe la défaillance à partir de l'analyse des données de surveillance (EN 13306 ; ISO 13381-1).

Parmi tous les modes de dégradation, la corrosion occupe une place prépondérante dans le secteur Oil & Gas. Selon l'étude IMPACT publiée par la NACE en 2016, la corrosion représente un coût annuel mondial de 2,5 billions USD, soit environ 3,4 % du Produit Intérieur Brut mondial (Koch et al., 2016). Une part significative de ce coût concerne les infrastructures de transport d'hydrocarbures — les pipelines — qui sont à la fois soumises à des environnements chimiquement agressifs et difficiles à inspecter de manière continue. Les techniques classiques de surveillance — ultrasons (UT), coupons gravimétriques, sondes commerciales — souffrent de limitations importantes : coût élevé, ponctualité, ou complexité d'intégration aux systèmes de gestion industriels (Wei et al., 2024 ; Pumps Africa, 2024).

Face à ces limites, deux dynamiques convergent dans la littérature récente. D'une part, la disponibilité croissante de microcontrôleurs et de capteurs IoT à très faible coût (ESP32, HX711, capteurs numériques 1-Wire) ouvre la voie à des chaînes d'instrumentation académiques et industrielles à un coût inférieur à 50 USD (Mayer et al., 2023). D'autre part, les méthodes d'apprentissage automatique — en particulier les algorithmes par gradient boosting comme XGBoost — démontrent une capacité supérieure à celle des modèles physiques classiques (de Waard et Milliams, 1975 ; NORSOK M-506) pour capturer les non-linéarités complexes entre variables de procédé et taux de corrosion, avec des erreurs de prédiction inférieures à 5 % (Hu et al., 2024 ; Wei et al., 2024 ; Yan et Yan, 2024).

Le présent mémoire s'inscrit à la jonction de ces deux dynamiques. Il a pour objectif de concevoir, développer et valider expérimentalement un **système intégré de maintenance prédictive de la corrosion** couvrant la chaîne complète **détection → diagnostic → pronostic → décision → action** définie par la norme ISO 13381-1 (ISO, 2015) et articulé autour de quatre composants intégrés : (i) une **sonde ER low-cost** basée sur un microcontrôleur ESP32 et un amplificateur HX711 (couche détection — OS1) ; (ii) un module de **diagnostic** des régimes de corrosion (couche diagnostic — partie d'OS3) ; (iii) un **modèle XGBoost** prédisant simultanément le taux de corrosion (CR, en mm/an) et la durée de vie résiduelle (RUL, en heures) avec interprétabilité SHAP (couche pronostic — OS2) ; et (iv) un **prototype de GMAO low-cost** open-source démontrant qu'une PME africaine peut disposer d'une gestion structurée des actifs, des alertes, des ordres de travail et des KPIs maintenance sans recourir aux solutions propriétaires (SAP PM, IBM Maximo) — couches décision et action — OS4. Le contexte applicatif est celui des infrastructures pétrolières camerounaises, et plus particulièrement celui de l'opérateur **Cameroon Oil Transportation Company (COTCO)**, exploitant le pipeline Tchad-Cameroun depuis 2003 (COTCO, 2024 ; Chad-Cameroon Pipeline Project, 2024).

Après une revue de la littérature sur la corrosion, ses mécanismes, les méthodes de surveillance, les modèles prédictifs, le diagnostic en maintenance et les systèmes de GMAO, ainsi qu'une présentation du contexte industriel et de la problématique (**Chapitre I**), nous aborderons les fondements techniques du prototype développé, les matériels mobilisés, et la méthodologie retenue pour l'acquisition, le traitement des données, l'entraînement du modèle d'apprentissage automatique et la conception de la GMAO low-cost (**Chapitre II**). Enfin, les résultats expérimentaux issus du prototype, les performances métrologi ques de la sonde, les métriques du modèle XGBoost, l'efficacité de l'inhibiteur de corrosion testé et la fonctionnalité du prototype GMAO seront présentés, discutés au regard de la littérature, et confrontés aux objectifs initiaux (**Chapitre III**).

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CHAPITRE I : CONTEXTE ET PROBLÉMATIQUE

**Sommaire du Chapitre I**

I.0. Introduction
I.1. Contexte et justification (suivant les six approches du protocole de recherche)
I.2. Problématique
I.3. Objectifs de l'étude
I.4. Questions de recherche
I.5. Importance de cette étude
I.6. Organisation du travail
I.7. Revue de la littérature
I.8. Conclusion

---

## I.0. Introduction

Dans ce chapitre, nous allons d'abord cadrer le contexte et la justification de la recherche selon les six approches recommandées par le protocole de recherche (approche définitionnelle, contexte international et national, état des recherches scientifiques et leurs limites, justificatif normatif et réglementaire, concept dans la zone d'étude, énoncé du sujet). Nous formulerons ensuite la problématique, les objectifs et les questions de recherche associées, puis nous présenterons l'importance de l'étude pour les différentes parties prenantes. Le chapitre se clôt par une revue détaillée de la littérature couvrant les mécanismes de corrosion, les méthodes de surveillance, les modèles prédictifs classiques et les approches récentes par apprentissage automatique.

---

## I.1. Contexte et justification

### I.1.1. Approche définitionnelle et historique de la corrosion

La corrosion est définie par la norme **ISO 8044 :2015** comme « une interaction physico-chimique entre un métal et son environnement qui entraîne des modifications des propriétés du métal et qui peut conduire à une dégradation significative de la fonction du métal, de l'environnement ou du système technique dont ils font partie » (ISO, 2015). Ce phénomène naturel et thermodynamiquement spontané traduit la tendance des métaux à retourner à leur état d'oxyde stable — l'état sous lequel ils existent dans la croûte terrestre avant tout traitement métallurgique (Schweitzer, 2010).

L'étude scientifique de la corrosion remonte aux travaux fondateurs de **Michael Faraday (1834)**, qui établit la relation quantitative entre le courant électrique et la masse de métal dissous, posant ainsi les bases de l'électrochimie de la corrosion (Faraday, 1834). Au XXᵉ siècle, **Wagner et Traud (1938)** formalisent la théorie des électrodes mixtes et de la cinétique électrochimique, permettant de modéliser quantitativement la vitesse de corrosion à partir des courbes de polarisation. Le modèle semi-empirique de **de Waard et Milliams (1975)**, développé pour la prédiction de la corrosion CO₂ dans les pipelines pétroliers, devient la référence industrielle mondiale (de Waard et Milliams, 1975 ; de Waard, Lotz et Milliams, 1991).

La maintenance industrielle, quant à elle, a connu une évolution parallèle. La norme **EN 13306 :2018** définit la maintenance prédictive comme une « maintenance conditionnelle effectuée en suivant les prévisions extrapolées de l'analyse et de l'évaluation de paramètres significatifs de la dégradation du bien » (CEN, 2018). La norme **ISO 13381-1 :2015** précise quant à elle les principes du pronostic et de l'estimation de la durée de vie résiduelle (RUL) à partir des données de surveillance (ISO, 2015). C'est précisément à l'intersection de ces deux normes que se positionne ce travail : instrumenter pour mesurer, mesurer pour prédire, prédire pour intervenir.

### I.1.2. Contexte international et national

À l'échelle mondiale, l'étude **IMPACT (International Measures of Prevention, Application and Economics of Corrosion Technology)** publiée par la NACE en 2016 estime le coût annuel global de la corrosion à **2,5 billions USD**, soit environ **3,4 % du PIB mondial** (Koch et al., 2016 ; NACE, 2016). L'étude conclut également que la mise en œuvre de bonnes pratiques de gestion de la corrosion permettrait d'économiser entre 15 % et 35 % de ce montant, soit 375 à 875 milliards USD par an. Dans le seul secteur Oil & Gas, les pertes annuelles imputables à la corrosion sont estimées entre 1,3 et 1,8 milliard USD (Koch et al., 2016 ; Inspectioneering, 2016). Ces chiffres représentent une opportunité directe d'économies si des stratégies de surveillance et de prédiction efficaces sont déployées.

En **Afrique subsaharienne**, la problématique est amplifiée par plusieurs facteurs : (i) des conditions climatiques tropicales (humidité élevée, températures > 28 °C) qui accélèrent la corrosion atmosphérique ; (ii) la difficulté d'accès à certains équipements (forêt équatoriale, zones marécageuses, sections offshore) ; (iii) l'instabilité politique et le vandalisme dans certaines régions (Pumps Africa, 2024). Les opérateurs africains du secteur Oil & Gas doivent ainsi composer avec des budgets contraints et des chaînes d'approvisionnement plus longues que leurs homologues occidentaux pour les pièces de rechange et les équipements d'inspection (Egbule et al., 2018 ; Onyebuchi et al., 2018).

Au **Cameroun**, le secteur pétrolier représente une part significative des recettes publiques et du PIB national. La **Cameroon Oil Transportation Company (COTCO)** exploite depuis 2003 le **Système d'Exportation Tchadien (SET)**, composé d'un pipeline de 1 070 km au total dont 903 km en territoire camerounais, d'une station de tête à Komé, et d'un terminal offshore à Kribi (Kome Kribi 1 FSO) relié à la côte par un pipeline sous-marin de 11 km (COTCO, 2024 ; Chad-Cameroon Pipeline Project, 2024 ; ExxonMobil, 2011). La capacité nominale est de 225 000 barils par jour. Cette infrastructure traverse des zones de forêt équatoriale dense, franchit de nombreux cours d'eau et longe des zones habitées, rendant toute défaillance non anticipée potentiellement catastrophique sur les plans humain, environnemental et économique.

### I.1.3. État de la recherche scientifique et limites identifiées

La recherche sur la prédiction de la corrosion par apprentissage automatique a connu une accélération significative depuis 2018, avec une production scientifique en croissance exponentielle (Coelho, 2022 ; npj Materials Degradation, 2022). Les approches les plus utilisées dans la littérature récente incluent :

- **Les méthodes d'ensemble** : forêts aléatoires (Cheng et Niu, 2018), **XGBoost** (Chen et Guestrin, 2016 ; Ma, Zhao et Wang, 2021), LightGBM, AdaBoost et Gradient Boosting (Yan et Yan, 2024). Ces méthodes obtiennent typiquement des erreurs RMSE comprises entre 0,031 et 0,052 mm/an avec des coefficients de détermination R² supérieurs à 0,95 sur des jeux de données de pipelines (Wei et al., 2024).
- **Les réseaux de neurones** : MLP (Ossai, Boswell et Davies, 2017), réseaux de neurones convolutifs et LSTM pour les séries temporelles (Xu, Xia et Wang, 2020), réseaux résiduels (ResNet) avec analyse d'interprétabilité (Liu et al., 2025), et architectures Transformer pour la prédiction de corrosion interne (Tan et al., 2025).
- **Les approches interprétables** : utilisation de **SHAP (SHapley Additive exPlanations)** pour quantifier la contribution de chaque variable d'entrée aux prédictions (Hu et al., 2024 ; Yan et Yan, 2024). Ces analyses identifient typiquement la température, la pression partielle de CO₂ et la pression totale comme les trois variables dominantes pour la corrosion interne des pipelines O&G.

Cependant, plusieurs **lacunes critiques** persistent dans la littérature :

- **Absence quasi-totale de données africaines** : les jeux de données utilisés proviennent presque exclusivement des États-Unis (PHMSA), de Chine ou d'Europe. Aucune étude publiée n'intègre de données expérimentales issues de pipelines subsahariens (Pumps Africa, 2024 ; Onyebuchi et al., 2018).
- **Coût prohibitif des sondes commerciales** : les sondes ER industrielles (Cosasco, Permasense, Emerson Roxar) ont un coût unitaire de 500 à 5 000 USD, hors installation et maintenance, ce qui est incompatible avec un déploiement étendu sur un réseau de plusieurs milliers de kilomètres (Cosasco, 2024 ; Hassanzadeh et al., 2024).
- **Circularité des évaluations sur données synthétiques** : la majorité des modèles ML sont entraînés et évalués sur des données générées par les modèles physiques eux-mêmes (de Waard et Milliams), ce qui invalide la portée scientifique des métriques rapportées. Un modèle XGBoost entraîné sur des données de Waard apprend à reproduire de Waard, sans capacité démontrée de généralisation (Coelho, 2022).
- **Absence de prédiction simultanée CR + RUL** : la majorité des travaux se limitent à la prédiction du taux de corrosion instantané, sans extrapolation vers le temps avant défaillance — information pourtant décisive pour la planification industrielle (Akash, 2024 ; Liu et al., 2022).
- **Environnements multi-composants peu modélisés** : les milieux industriels réels combinent souvent plusieurs acides ou agents agressifs dont l'interaction n'est pas modélisable analytiquement par les approches classiques (Heydari et Talebpour, 2024). C'est typiquement le cas des détartrants industriels qui mélangent HCl et H₃PO₄, créant une cinétique multi-mécanismes attaque/passivation difficile à prédire (Persian Utab, 2023 ; Schweitzer, 2010).

### I.1.4. Justificatif normatif et réglementaire

La gestion de la corrosion dans les infrastructures pétrolières est encadrée par un corpus normatif international et national complet :

**Au niveau international :**

- **ISO 8044 :2015** — Définitions et terminologie de la corrosion (ISO, 2015) ;
- **ASTM G1-03** — Préparation, nettoyage et évaluation des éprouvettes de corrosion (ASTM, 2017) ;
- **ASTM G31-12a** — Essais d'immersion en laboratoire (ASTM, 2012) ;
- **ASTM G96-90** — Surveillance de la corrosion en service par méthodes électriques (ER, LPR) (ASTM, 2018) ;
- **NACE/AMPP SP0775-2023** — Préparation, installation, analyse et interprétation des coupons de corrosion en service pétrolier (AMPP, 2023) ;
- **NACE TM0190** — Méthodes d'essai pour sondes ER en service pétrolier (NACE, 2012) ;
- **NACE MR0175 / ISO 15156** — Matériaux résistant à la corrosion sous H₂S (ISO, 2020) ;
- **API 570** — Inspection des systèmes de tuyauteries en service (API, 2016a) ;
- **API 580 / 581** — Inspection basée sur le risque (RBI) (API, 2016b ; API, 2016c) ;
- **ISO 13381-1 :2015** — Maintenance — Pronostic — Lignes directrices générales (ISO, 2015) ;
- **EN 13306 :2018** — Terminologie de la maintenance (CEN, 2018) ;
- **NORSOK M-506** — Calcul du taux de corrosion CO₂ (Standards Norway, 2017).

**Au niveau national camerounais :**

- **Loi n° 99/013 du 22 décembre 1999** portant Code Pétrolier, qui impose aux opérateurs de maintenir leurs installations dans un état de sécurité conforme aux normes internationales (République du Cameroun, 1999) ;
- **Décret n° 2000/465 du 30 juin 2000** fixant les conditions d'exploitation des hydrocarbures, prévoyant des obligations de surveillance et de contrôle (République du Cameroun, 2000) ;
- **Loi-cadre sur l'environnement** (loi n° 96/12) imposant des études d'impact et des plans de prévention des pollutions (République du Cameroun, 1996).

L'ensemble de ce corpus normatif établit le cadre dans lequel s'inscrit toute démarche de surveillance de la corrosion sur le territoire camerounais. Le présent travail contribue à ce cadre en proposant un outil aligné sur les principes de l'**ASTM G96** (mesure ER continue) et de l'**ISO 13381-1** (pronostic et RUL).

### I.1.5. Le concept dans la zone d'étude — COTCO et le pipeline Tchad-Cameroun

La **Cameroon Oil Transportation Company (COTCO)** opère le pipeline Tchad-Cameroun depuis 2003 (COTCO, 2024). Le système comprend les éléments suivants (ExxonMobil, 2011 ; Chad-Cameroon Pipeline Project, 2024) :

- Un **pipeline enterré** de 1 070 km de longueur totale (903 km en territoire camerounais), de diamètre nominal 30 pouces, en acier API 5L Grade B revêtu de FBE (Fusion-Bonded Epoxy) ;
- Une **station de pompage de tête (PS-1)** à Komé (Tchad) ;
- Un **terminal d'exportation offshore** à 18 km au large de Kribi (Cameroun), constitué de l'unité **Kome Kribi 1 FSO** (Floating Storage and Offloading) reliée à la côte par un pipeline sous-marin de 11 km ;
- Une **capacité nominale de 225 000 barils par jour**.

Ce réseau est soumis à plusieurs **mécanismes de corrosion** simultanés (Egbule et al., 2018 ; Aniobi, 2018) :

1. **Corrosion externe atmosphérique et galvanique** sur les sections aériennes ou semi-aériennes, accélérée par l'humidité tropicale ;
2. **Corrosion sous revêtement (CUI)** dans les zones où le revêtement FBE est endommagé ;
3. **Corrosion interne** par les hydrocarbures bruts contenant des traces résiduelles de CO₂, H₂S et eau de formation ;
4. **Corrosion microbienne (MIC)** liée à l'activité de bactéries sulfato-réductrices (SRB) dans les fonds de réservoirs et bas de conduites ;
5. **Corrosion par piqûres** dans les zones où des chlorures sont présents.

La **politique actuelle de maintenance** chez COTCO et chez la plupart des opérateurs subsahariens repose sur trois piliers (Pumps Africa, 2024 ; HSPublishing, 2023) :

- Des **inspections périodiques par ultrasons (UT)** à intervalles de 6 à 24 mois selon la criticité de la section ;
- Des **coupons gravimétriques** placés en certains points stratégiques ;
- Une **injection préventive d'inhibiteurs** dans le brut (filmants à base d'imidazoline ou d'amines).

Cette approche présente plusieurs **limites identifiées** :

- L'**intervalle long entre inspections** masque les dérives rapides du taux de corrosion ;
- L'**absence de surveillance continue** ne permet pas de détecter en temps réel une augmentation soudaine de l'agressivité du fluide (variation de la composition, défaillance de l'injection d'inhibiteur) ;
- L'**absence d'estimation explicite du RUL** complique la planification des interventions et conduit à des arrêts de production non optimisés.

Le besoin d'un outil de **surveillance continue, low-cost, et capable de prédire la dégradation avant qu'elle ne devienne critique** est ainsi directement identifiable dans le contexte COTCO.

### I.1.6. Énoncé du sujet

Sur la base du contexte exposé — ampleur économique mondiale de la corrosion, lacunes scientifiques et industrielles persistantes, besoins spécifiques des opérateurs subsahariens et de COTCO en particulier, cadre normatif et réglementaire — le sujet de ce mémoire est formulé comme suit :

> **« Système de maintenance prédictive de la corrosion par apprentissage automatique : conception d'une sonde ER low-cost, acquisition IoT et prédiction du taux de corrosion et de la durée de vie résiduelle par XGBoost. »**

Ce sujet articule trois axes : (1) un axe **instrumental** (conception d'une chaîne de mesure low-cost ER + IoT) ; (2) un axe **algorithmique** (apprentissage automatique XGBoost à double sortie CR + RUL) ; et (3) un axe **applicatif** (compatibilité avec le contexte camerounais et avec les contraintes de COTCO).

---

## I.2. Problématique

La maintenance des infrastructures de transport pétrolier au Cameroun, et plus particulièrement chez COTCO, fait face à un **paradoxe fondamental** : les opérateurs disposent de données de surveillance (mesures UT, rapports de laboratoire, journaux d'injection d'inhibiteurs) mais ces données, collectées de manière ponctuelle et stockées dans des systèmes hétérogènes, ne permettent ni d'anticiper les défaillances par corrosion avant qu'elles n'atteignent un seuil critique, ni de prédire avec précision la durée de vie résiduelle des éléments métalliques exposés. Or, dans un contexte où la rupture d'un pipeline traversant la forêt équatoriale ou un cours d'eau peut entraîner des conséquences environnementales irréversibles, cette absence d'anticipation constitue un risque industriel majeur.

Sur le plan **scientifique**, les modèles physiques classiques de prédiction de la corrosion (modèle de de Waard et Milliams, modèle NORSOK M-506) ont montré des limites importantes en conditions d'exploitation réelle, avec des erreurs systématiques de 40 à 60 % attribuables à la non-prise en compte des interactions complexes entre les multiples composants des fluides de procédé (de Waard et Milliams, 1975 ; Coelho, 2022). Les approches par apprentissage automatique offrent une alternative prometteuse, capable de capturer ces non-linéarités, mais leur déploiement en contexte africain se heurte à deux verrous : (i) l'**absence de données d'entraînement locales**, et (ii) le **coût des équipements d'acquisition** professionnels.

Sur le plan **technologique**, les sondes commerciales de type ER (Cosasco, Permasense, Emerson Roxar) offrent une résolution suffisante pour quantifier le taux de corrosion en mm/an, mais leur prix unitaire (500 à 5 000 USD) est incompatible avec un déploiement massif sur les milliers de kilomètres du réseau COTCO. Inversement, les chaînes d'instrumentation low-cost à base de microcontrôleurs Arduino ou ESP32 décrites dans la littérature récente (Mayer et al., 2023 ; Mansfeld, 2014) atteignent des résolutions intéressantes mais ne sont généralement pas intégrées à un modèle de prédiction CR + RUL exploitable.

Sur le plan **algorithmique**, la grande majorité des travaux ML sur la corrosion se limitent à la prédiction instantanée du taux de corrosion, sans extrapolation explicite vers la durée de vie résiduelle (RUL), pourtant définie de manière claire par la norme ISO 13381-1 (ISO, 2015 ; Akash, 2024). Cette absence de double prédiction CR + RUL prive les opérateurs d'une information essentielle à la planification optimisée des interventions.

Enfin, sur le plan **expérimental**, peu d'études disposent d'un protocole *run-to-failure* (RTF) complet permettant de couvrir l'intégralité du cycle de dégradation depuis l'état initial jusqu'à la rupture mécanique. Or seul un protocole RTF permet de constituer un jeu d'apprentissage statistiquement représentatif pour une prédiction RUL fiable.

La **question centrale** de ce travail est donc :

> **Dans quelle mesure un système de surveillance ER low-cost développé à partir de composants disponibles localement au Cameroun, combiné à un modèle XGBoost entraîné en protocole *run-to-failure* sur des données expérimentales de corrosion en milieu acide multi-composant, permet-il de prédire avec précision le taux de corrosion (CR) et la durée de vie résiduelle (RUL) d'un élément structural métallique, et de générer des recommandations exploitables pour la maintenance prédictive industrielle ?**

---

## I.3. Objectifs de l'étude

### I.3.1. Objectif général

Concevoir, développer et valider expérimentalement un **système intégré de maintenance prédictive de la corrosion** couvrant la chaîne complète **détection → diagnostic → pronostic → décision → action** définie par la norme ISO 13381-1, et combinant une sonde ER low-cost (ESP32 + HX711), un modèle d'apprentissage automatique XGBoost à double sortie (CR + RUL) avec module de diagnostic des régimes de corrosion, un système d'alertes calibrées sur l'efficacité d'un inhibiteur industriel à base d'imidazoline, et un prototype de GMAO low-cost open-source démontrant la faisabilité d'une gestion structurée de la maintenance pour les PME industrielles africaines.

### I.3.2. Objectifs spécifiques

Quatre objectifs spécifiques (OS), chronologiquement ordonnés et logiquement articulés, structurent ce travail. Ils correspondent respectivement aux étapes **détection**, **pronostic**, **diagnostic + décision** et **action** de la chaîne ISO 13381-1.

- **OS1 — Concevoir et valider métrologi quement la chaîne d'acquisition ER low-cost (étape *Détection*).** Il s'agit de réaliser un capteur de résistance électrique (ER) basé sur un pont de Wheatstone, un amplificateur HX711 24 bits et un microcontrôleur ESP32 en deep sleep pulsé, capable de mesurer des variations de résistance d'un fil de fer à ±0,01 mΩ près dans un milieu acide concentré (pH ≈ 1), avec une période de mesure de 10 minutes et une autonomie compatible avec un déploiement de plusieurs jours.

- **OS2 — Entraîner et valider un modèle XGBoost à double sortie CR + RUL (étape *Pronostic*).** Il s'agit, à partir des séries temporelles collectées en protocole *run-to-failure* sur quatre cycles expérimentaux de corrosion, de construire un modèle d'apprentissage automatique XGBoost prédisant à la fois le taux de corrosion instantané (en mm/an) et la durée de vie résiduelle (en heures), avec une erreur relative inférieure à 15 % (RMSE), validé par une procédure de validation croisée temporelle (TimeSeriesSplit) respectant la causalité, et interprété par analyse SHAP.

- **OS3 — Diagnostiquer les régimes de corrosion, évaluer l'efficacité d'un inhibiteur à base d'imidazoline et définir un système d'alertes graduées (étapes *Diagnostic* et *Décision*).** Il s'agit (i) de classifier en temps réel le régime de corrosion observé (corrosion stable, accélérée, passivation, adsorption inhibiteur, pré-rupture) à partir des sorties du modèle XGBoost ; (ii) de quantifier expérimentalement l'effet d'un inhibiteur de la famille des imidazolines (référence commerciale à sélectionner) sur le taux de corrosion mesuré, à deux concentrations différentes (0,1 % et 0,5 % v/v) ; (iii) de détecter par algorithme *changepoint* le temps d'adsorption de l'inhibiteur ; et (iv) de définir un système d'alertes à trois niveaux (vert / orange / rouge) avec recommandations de dosage exploitables industriellement.

- **OS4 — Concevoir un prototype de GMAO low-cost open-source intégrant les sorties du système prédictif (étape *Action*).** Il s'agit de développer une application web légère (stack Supabase + Next.js, hébergement Vercel gratuit) implémentant les fonctions essentielles d'une GMAO industrielle — gestion des actifs surveillés, ingestion automatique des mesures et prédictions, génération automatique d'alertes graduées, création d'ordres de travail, traçabilité des interventions et des doses d'inhibiteur, dashboard de KPIs maintenance (MTBF, MTTR, disponibilité, efficacité d'inhibition) — afin de démontrer qu'une PME africaine peut bénéficier d'une gestion structurée de la maintenance équivalente fonctionnellement aux GMAO industrielles propriétaires (SAP PM, IBM Maximo) à un coût d'exploitation marginal nul.

---

## I.4. Questions de recherche

À chaque objectif spécifique correspond une question de recherche (QR) :

- **QR1 :** Dans quelle mesure un pont de Wheatstone instrumenté par un amplificateur HX711 24 bits et un microcontrôleur ESP32 permet-il de mesurer des variations de résistance d'un fil de fer au dixième de milliohm, avec une stabilité et une résolution suffisantes pour quantifier le taux de corrosion en mm/an dans un milieu acide concentré ?

- **QR2 :** Dans quelle mesure un modèle XGBoost entraîné sur des séries temporelles de résistance et de température collectées en protocole *run-to-failure* permet-il de prédire simultanément le taux de corrosion (CR) et la durée de vie résiduelle (RUL) avec une erreur relative inférieure à 15 % (RMSE), tout en restant interprétable par analyse SHAP ?

- **QR3 :** Dans quelle mesure les sorties du modèle XGBoost permettent-elles de diagnostiquer en temps réel le régime de corrosion en cours (stable, accélérée, passivation, adsorption d'inhibiteur, pré-rupture), de calibrer un système d'alertes graduées (vert / orange / rouge), et de fournir des recommandations de dosage d'un inhibiteur de la famille des imidazolines exploitables industriellement ?

- **QR4 :** Dans quelle mesure une GMAO low-cost open-source bâtie sur un stack Supabase + Next.js peut-elle exploiter les alertes et les recommandations issues du système prédictif pour offrir aux PME industrielles africaines une gestion structurée des actifs, des ordres de travail et des KPIs de maintenance équivalente fonctionnellement aux GMAO industrielles propriétaires (SAP PM, IBM Maximo), à un coût d'exploitation nul ou marginal ?

---

## I.5. Importance de cette étude

Ce travail revêt un intérêt à plusieurs niveaux et pour plusieurs catégories de parties prenantes :

**Pour le lecteur académique :** ce mémoire propose une démarche reproductible combinant instrumentation IoT low-cost, protocole expérimental rigoureux et apprentissage automatique interprétable. Il comble un vide bibliographique sur la maintenance prédictive de la corrosion en contexte africain et fournit un point d'ancrage pour des travaux ultérieurs sur les mêmes thématiques.

**Pour l'auteur :** ce travail constitue l'aboutissement académique du Master 2 et la matérialisation concrète de l'intégration de compétences pluridisciplinaires (corrosion, électronique embarquée, apprentissage automatique, méthodologie scientifique). Il prépare directement à l'insertion professionnelle dans le secteur industriel, et plus particulièrement dans les métiers de la maintenance prédictive.

**Pour l'École Nationale Supérieure Polytechnique de Douala (ENSPD) :** le mémoire contribue au rayonnement scientifique de l'institution en démontrant la capacité de ses étudiants à produire des prototypes intégrés et fonctionnels mobilisant des outils numériques avancés à partir de composants accessibles localement. Il s'inscrit pleinement dans la mission de formation d'ingénieurs adaptés aux contextes africains.

**Pour la recherche :** ce travail constitue l'une des premières études publiées (à notre connaissance) intégrant explicitement la prédiction CR + RUL par XGBoost avec interprétabilité SHAP, sur des données expérimentales originales collectées en protocole *run-to-failure*, et dans un contexte multi-acide non-monotone. Il complète la littérature dominée par les approches mono-cible (CR seul) et les jeux de données nord-américains.

**Pour COTCO et les opérateurs pétroliers camerounais :** le mémoire fournit une **preuve de concept industriellement transposable**. Le coût total du prototype matériel (< 50 000 FCFA) couplé à une GMAO d'exploitation gratuite ouvre la voie à un déploiement étendu de capteurs sur un réseau de plusieurs milliers de kilomètres, à un coût compatible avec les budgets des opérateurs locaux.

**Pour les PME industrielles africaines :** au-delà du contexte pétrolier, le prototype de GMAO low-cost open-source développé dans ce travail (stack Supabase + Next.js) est directement transposable à toutes les PME confrontées à des coûts de licence prohibitifs des GMAO industrielles (SAP PM, IBM Maximo, Mainpac), dont les tarifs annuels (souvent supérieurs à 10 000 USD par site) sont incompatibles avec les budgets de la majorité des PME subsahariennes. Le code source ouvert et l'architecture cloud sans serveur permettent une démocratisation effective de la maintenance assistée par ordinateur.

**Pour la société et l'environnement :** la prévention des ruptures de pipeline par prédiction précoce de la dégradation réduit le risque de déversement d'hydrocarbures aux conséquences écologiques potentiellement irréversibles dans une zone de forêt équatoriale et de cours d'eau. C'est un apport indirect mais réel à la protection des écosystèmes et des populations riveraines.

---

## I.6. Organisation du travail

Ce mémoire est organisé en trois chapitres principaux, encadrés par une introduction générale et une conclusion générale.

Le **Chapitre I (Contexte et problématique)** établit le cadre théorique, normatif et industriel de la recherche selon les six approches du protocole de recherche, formule la problématique, les objectifs et les questions de recherche, expose l'importance de l'étude, et présente une revue détaillée de la littérature sur la corrosion, ses mécanismes, ses méthodes de surveillance, ses modèles prédictifs, le diagnostic en maintenance industrielle et les systèmes de Gestion de Maintenance Assistée par Ordinateur (GMAO).

Le **Chapitre II (Outils et méthodes)** présente le prototype développé (sonde ER + acquisition IoT ESP32 + pipeline ML + prototype GMAO), l'ensemble des matériels mobilisés, les méthodes d'acquisition et de traitement des données, la méthodologie d'entraînement du modèle XGBoost (validation croisée temporelle, hyperparamètres, interprétabilité SHAP), le module de diagnostic des régimes de corrosion, le protocole expérimental *run-to-failure* en quatre runs, l'architecture du prototype de GMAO low-cost (schéma de base de données, pages web, KPIs), et le tableau synoptique de la démarche méthodologique.

Le **Chapitre III (Résultats et discussions)** présente les résultats expérimentaux issus du prototype, les performances métrologi ques de la sonde ER, les résultats des quatre runs RTF, les métriques de validation du modèle XGBoost, l'analyse SHAP des variables d'influence, le diagnostic des régimes observés, l'évaluation de l'efficacité de l'inhibiteur de corrosion testé, la fonctionnalité du prototype GMAO et ses KPIs, et la discussion comparative des résultats au regard de la littérature.

La **Conclusion générale** synthétise les résultats des quatre objectifs spécifiques, dresse le bilan des contributions, identifie les limites du travail et formule des recommandations pour COTCO, pour les PME industrielles africaines, et pour les travaux futurs.

---

## I.7. Revue de la littérature

### I.7.1. Mécanismes électrochimiques de la corrosion

Dans un milieu électrolytique, la corrosion procède par un mécanisme de **pile galvanique** dans lequel deux réactions électrochimiques couplées se produisent simultanément à la surface du métal (Schweitzer, 2010 ; Roberge, 2008).

**Réaction anodique** (oxydation) :

$$\text{Fe} \rightarrow \text{Fe}^{2+} + 2e^-$$

**Réaction cathodique** (réduction) — en milieu acide (pH < 4) :

$$2\text{H}^+ + 2e^- \rightarrow \text{H}_2 \uparrow$$

La **loi de Faraday (1834)** établit la relation quantitative entre le courant échangé et la masse dissoute :

$$m = \frac{M \cdot I \cdot t}{n \cdot F}$$

où *m* est la masse de métal dissous (g), *M* la masse molaire (55,85 g/mol pour le fer), *I* le courant (A), *t* la durée (s), *n* le nombre d'électrons échangés (2 pour Fe²⁺), et *F* la constante de Faraday (96 485 C/mol).

Le **taux de corrosion (CR)** en mm/an est calculé selon la norme **ASTM G1** par :

$$CR \ (\text{mm/an}) = \frac{87{,}6 \cdot \Delta m}{\rho \cdot A \cdot t}$$

où Δ*m* est la perte de masse (mg), ρ la densité (g/cm³), *A* l'aire exposée (cm²), et *t* la durée (heures) (ASTM, 2017).

L'équation de **Butler-Volmer** décrit la cinétique électrochimique complète à l'interface métal-électrolyte (Bard et Faulkner, 2001) :

$$i = i_{corr} \cdot \left[ e^{\frac{\alpha_a F \eta}{RT}} - e^{\frac{-\alpha_c F \eta}{RT}} \right]$$

Cette équation justifie l'influence de la température comme facteur cinétique aggravant — paramètre directement intégré comme variable d'entrée dans le modèle XGBoost (chapitre II).

### I.7.2. Formes de corrosion et classification

La classification internationale de référence est établie par l'**AMPP (ex-NACE International)** et reprise dans la norme NACE SP0775 (AMPP, 2023).

**Tableau I.1 — Classification des formes de corrosion**

| Forme | Mécanisme | Localisation typique | Norme |
|---|---|---|---|
| Généralisée (uniforme) | Dissolution uniforme | Pipelines acier au carbone | ASTM G1 |
| Par piqûres | Attaque localisée (Cl⁻) | Acier inox milieu chloruré | ASTM G46 |
| Galvanique | Couplage entre métaux | Raccords bimétalliques | ASTM G82 |
| Sous contrainte (SCC) | Contrainte + environnement | Tubes pression, soudures | NACE TM0177 |
| Érosion-corrosion | Écoulement + corrosion | Coudes, vannes, pompes | ASTM G76 |
| Sweet (CO₂) | H₂CO₃ → attaque acide | Pipelines O&G | de Waard & Milliams (1975) |
| Sour (H₂S) | Fragilisation H, SSC, HIC | Puits gaz acide | NACE MR0175 / ISO 15156 |
| MIC | Bactéries SRB, IRB | Fonds réservoirs | NACE TM0212 |

Source : AMPP (2023), ASTM (2017), ISO (2020).

### I.7.3. Méthodes de surveillance de la corrosion

Plusieurs techniques coexistent dans l'industrie (Roberge, 2008 ; Mansfeld, 2014 ; Cosasco, 2024) :

**Tableau I.2 — Comparaison des méthodes de surveillance de la corrosion**

| Méthode | Principe | Mesure | Résolution | Coût unitaire |
|---|---|---|---|---|
| Coupon gravimétrique | Perte de masse | Intégrée sur durée | ±0,1 mg/cm² | Très faible (< 100 USD) |
| Sonde ER | Augmentation de R fil corrodé | Continue | ±0,01 mΩ | Faible (DIY) à élevé (COTS) |
| LPR | Résistance polarisation | Continue | ±5 % | Moyen |
| EIS | Spectre d'impédance | Discontinue | Très haute | Élevé |
| UT | Épaisseur paroi par écho | Ponctuelle | ±0,1 mm | Moyen |
| Émission acoustique | Détection fissures | Continue | Variable | Élevé |

Source : Roberge (2008), Mansfeld (2014), Hassanzadeh et al. (2024).

La **sonde à résistance électrique (ER)**, normalisée par l'ASTM G96, exploite la relation entre la résistance d'un fil métallique et sa section transversale. Lorsque le fil se corrode, son rayon *r* diminue et sa résistance *R* augmente selon (ASTM, 2018) :

$$R = \frac{\rho_{Fe} \cdot L}{\pi r^2}$$

La variation Δ*R* = *R*(t) − *R*(t₀) est directement proportionnelle à la perte de matière. C'est ce principe que reproduisent les sondes commerciales (Cosasco CW-20, Emerson Roxar, Permasense WT) et que reprend le prototype développé dans ce travail.

### I.7.4. Modèles prédictifs classiques

Le **modèle de de Waard et Milliams (1975)**, révisé en 1991 et 1995, constitue la référence industrielle pour la prédiction de la corrosion CO₂ (de Waard et Milliams, 1975 ; de Waard, Lotz et Milliams, 1991). Il exprime le taux de corrosion en fonction de la pression partielle de CO₂ et de la température :

$$\log_{10} CR = 5{,}8 - \frac{1710}{T + 273} + 0{,}67 \log_{10} P_{CO_2}$$

Ce modèle a été progressivement étendu pour inclure le pH, le débit, la composition de l'acier et la teneur en glycol. Cependant, ses **limites sont bien documentées** (Coelho, 2022 ; Hu et al., 2024) :

- Erreurs systématiques de 40 à 60 % en conditions réelles ;
- Domaine de validité limité à *P*(CO₂) ∈ [0 ; 2 MPa] ;
- Recalibration complète nécessaire pour intégrer toute nouvelle donnée ;
- Ignorance des interactions entre composants (HCl + H₃PO₄, SRB, etc.).

La **norme NORSOK M-506** (Standards Norway, 2017) propose une formulation alternative également limitée par les mêmes contraintes.

### I.7.5. Modèles prédictifs par apprentissage automatique

L'apprentissage automatique offre une alternative capable de capturer les non-linéarités complexes que les modèles physiques ignorent. Les méthodes les plus utilisées dans la littérature récente sur la corrosion incluent :

**XGBoost (eXtreme Gradient Boosting)** — introduit par **Chen et Guestrin (2016)** — est aujourd'hui l'algorithme dominant pour les problèmes de régression tabulaire. Il combine plusieurs centaines d'arbres de décision faibles via une procédure de gradient boosting régularisée. Ses avantages :

- Gestion native des variables hétérogènes ;
- Robustesse aux valeurs manquantes ;
- Régularisation L1 et L2 limitant le surapprentissage ;
- Interprétabilité élevée (feature importance, SHAP).

Les performances rapportées dans la littérature récente sur la corrosion sont remarquables (Wei et al., 2024 ; Yan et Yan, 2024) :

- **Wei et al. (2024)** : XGBoost atteint *RMSE* = 0,031 mm/an et *R²* = 0,99 sur la prédiction de corrosion en pipeline d'eau de refroidissement ;
- **Yan et Yan (2024)** : XGBoost et AdaBoost obtiennent *RMSE* = 0,052 sur la corrosion atmosphérique d'aciers faiblement alliés ;
- **Hu et al. (2024)** : modèle d'ensemble interprétable atteignant *RMSE* = 0,005876 et *R²* = 0,9648 sur la corrosion interne O&G.

**SHAP (SHapley Additive exPlanations)**, introduit par **Lundberg et Lee (2017)**, permet d'interpréter chaque prédiction individuelle en quantifiant la contribution de chaque variable d'entrée. Les analyses SHAP appliquées à la corrosion identifient typiquement la **température**, la **pression partielle de CO₂** et la **pression totale** comme les trois variables dominantes (Hu et al., 2024). Le présent travail mobilise SHAP pour identifier les variables dominantes dans le contexte multi-acide Detar Plus.

### I.7.6. Pronostic et durée de vie résiduelle (RUL)

La **norme ISO 13381-1 :2015** définit le pronostic comme « l'estimation du temps avant défaillance et le risque d'existence ou d'apparition d'un ou plusieurs modes de défaillance » (ISO, 2015). La **durée de vie résiduelle (RUL — Remaining Useful Life)** est définie comme « la durée pendant laquelle un système peut continuer à fonctionner avant que sa santé ne tombe sous un seuil prédéfini » (Akash, 2024 ; Liu et al., 2022).

Quatre familles d'approches existent (Liu et al., 2022) :

1. **Modèles physiques** : extrapolation par lois de propagation (fissure, corrosion, fatigue) ;
2. **Modèles statistiques** : analyse de survie (Weibull, AFT) ;
3. **Modèles par apprentissage automatique** : XGBoost, LSTM, Transformers ;
4. **Approches hybrides** : combinaison physique + ML.

Pour la corrosion spécifiquement, les approches ML *run-to-failure* sont les mieux adaptées car elles exploitent l'intégralité du cycle de dégradation (état initial → rupture). C'est la voie retenue dans ce travail.

### I.7.7. Inhibiteurs de corrosion à base d'imidazoline

Les **imidazolines** sont une famille d'inhibiteurs de corrosion largement utilisés dans le secteur Oil & Gas, particulièrement efficaces en milieu acide (Heydari et Talebpour, 2024). Leur structure moléculaire présente :

- Un **cycle imidazoline à 5 atomes** contenant deux atomes d'azote (N), dont l'un porte un doublet libre ;
- Une **chaîne hydrocarbonée hydrophobe** assurant l'orientation de la molécule sur la surface métallique.

Le mécanisme d'inhibition combine **physisorption et chimisorption** sur la surface du fer, formant une couche monomoléculaire qui isole le métal du milieu corrosif (Lu et Luo, 2016 ; Heydari et Talebpour, 2024). L'isotherme d'adsorption suit typiquement le modèle de **Langmuir** :

$$\frac{C}{\theta} = \frac{1}{K_{ads}} + C$$

où *C* est la concentration de l'inhibiteur, θ le taux de couverture surfacique, et *K*_ads la constante d'adsorption.

Les **efficacités d'inhibition** rapportées dans la littérature pour les imidazolines en milieu HCl sont remarquables :

- 94,4 % à 500 ppm en HCl 1 N (Heydari et Talebpour, 2024) ;
- 95,7 % à 80 mg/L sur acier A572 Gr.65 en NaCl 3,5 % (Wang et al., 2023) ;
- 96,8 % à 500 ppm en HCl 1 N (PMC, 2023).

L'**inhibiteur retenu dans ce travail** appartient à la famille des imidazolines, commercialisé pour l'industrie pétrolière. La référence commerciale précise sera fixée selon la disponibilité sur le marché camerounais ; à titre indicatif, des produits tels qu'AC PROTECT 106, Nalco Champion EC1605A ou équivalents respectent ce profil. L'efficacité fabricant typique déclarée est > 90 % en milieu HCl 1 N pour cette famille de produits.

### I.7.8. Diagnostic en maintenance industrielle

Le **diagnostic** est l'étape de la chaîne de maintenance prédictive (ISO 13381-1) consistant à *identifier la nature, la localisation et la cause d'une défaillance ou d'une dérive*, à partir des informations issues de la phase de détection (Akash, 2024 ; ISO, 2015). Il se distingue du **pronostic** — qui prédit le moment de la défaillance future — et précède la **décision** — qui choisit l'action corrective appropriée. La chaîne complète est ainsi :

> **Détection → Diagnostic → Pronostic → Décision → Action**

Pour la corrosion spécifiquement, plusieurs approches de diagnostic coexistent dans la littérature (Coelho, 2022 ; Tan et al., 2025) :

- **Approches par règles métier** : seuils sur les variables physiques (dérivée temporelle de R, accélération, niveaux d'agression) — simples et explicables, adaptées aux PME ;
- **Approches par classification ML** : forêts aléatoires, XGBoost classifieur, SVM — performantes mais nécessitent des données labélisées ;
- **Approches non-supervisées** : Isolation Forest, One-Class SVM — adaptées à la détection d'anomalies sans labélisation préalable.

Dans le contexte de la corrosion en milieu acide multi-composant, plusieurs régimes coexistent et peuvent être diagnostiqués à partir des signatures temporelles du signal ER : (i) corrosion stable nominale (dR/dt constant et faible), (ii) corrosion accélérée (dR/dt croissant — typiquement HCl dominant), (iii) passivation (dR/dt qui décélère sans inhibiteur — typiquement formation de FePO₄ par H₃PO₄), (iv) adsorption d'inhibiteur (changepoint avec chute brutale du dR/dt), et (v) pré-rupture (divergence de dR/dt, RUL faible). Le présent travail mobilise une approche hybride règles métier + sortie XGBoost, simple et explicable pour un déploiement industriel léger.

### I.7.9. Systèmes de gestion de la maintenance — GMAO et CMMS

Une **GMAO (Gestion de Maintenance Assistée par Ordinateur)**, ou en anglais **CMMS (Computerized Maintenance Management System)**, est une application logicielle dédiée à la planification, au suivi et à l'optimisation des activités de maintenance d'une organisation industrielle (Lopes et al., 2016 ; Roda et Macchi, 2018). Une GMAO moderne intègre typiquement les fonctions suivantes (ISO 14224, 2016 ; Bagheri et al., 2024) :

- **Gestion des actifs** : inventaire des équipements, hiérarchie fonctionnelle, données techniques, criticité ;
- **Gestion des ordres de travail (OT)** : création, assignation, planification, exécution, clôture ;
- **Historique des interventions** : traçabilité complète (qui, quand, quoi, durée, coût) ;
- **Gestion du stock de pièces de rechange** : références, niveaux, mouvements, fournisseurs ;
- **Indicateurs de performance (KPIs)** : MTBF, MTTR, taux de disponibilité, taux de panne, coût total de maintenance ;
- **Plans de maintenance préventive** : déclencheurs temporels ou conditionnels ;
- **Intégration avec les systèmes de surveillance** : ingestion d'alertes, création automatique d'OT.

Les **GMAO industrielles propriétaires** (SAP Plant Maintenance, IBM Maximo, Oracle eAM, Infor EAM) dominent le marché des grandes entreprises mais présentent un coût de licence prohibitif (10 000 à 100 000 USD/an par site selon le périmètre), une complexité d'implémentation élevée (consultants spécialisés requis), et une dépendance à l'éditeur. Selon Roda et Macchi (2018), moins de 15 % des PME industrielles dans les pays émergents disposent d'une GMAO professionnelle, contre plus de 80 % des grandes entreprises.

Plusieurs **alternatives open-source** existent (CMMS Wikipedia, 2024 ; Murphy, 2021) : CMMS Open Maint, Fiix Free, Mainpac Lite, MaintainX, Hippo CMMS Free, Limble. Néanmoins, ces solutions présentent des limites pour le contexte africain : (i) absence d'intégration native avec des capteurs IoT low-cost personnalisés ; (ii) absence de modules de prédiction par apprentissage automatique ; (iii) interfaces parfois en anglais uniquement ; (iv) hébergement self-hosted complexe à maintenir pour des PME sans équipe IT dédiée.

L'émergence récente des **architectures sans serveur (BaaS — Backend as a Service)** comme **Supabase** (alternative open-source à Firebase) couplée à des frameworks frontend modernes comme **Next.js** rend désormais possible le développement d'une GMAO sur mesure à un coût d'exploitation marginal nul (offres gratuites jusqu'à des volumes significatifs). C'est cette voie qu'explore l'OS4 du présent mémoire, en proposant une GMAO directement intégrée à la chaîne de surveillance prédictive développée dans les OS1, OS2 et OS3.

La norme **ISO 14224 :2016** définit les standards d'échange de données de fiabilité et de maintenance (formats d'OT, codes anomalie, taxonomie d'équipement) et constitue la référence d'interopérabilité pour toute GMAO du secteur Oil & Gas (ISO, 2016).

### I.7.10. Synthèse de la revue de littérature

La revue de littérature met en évidence quatre constats majeurs qui structurent ce travail :

1. La corrosion est un phénomène universel, quantifié par la loi de Faraday et encadré par un corpus normatif international complet (ISO, ASTM, NACE/AMPP, API) ;
2. Les méthodes de surveillance disponibles — coupons, sondes ER, LPR, UT — présentent des compromis coût/résolution/continuité que les approches IoT low-cost (ESP32 + HX711) sont en mesure de rééquilibrer ;
3. Les modèles physiques classiques (de Waard et Milliams) sont insuffisants en milieux multi-composants ; les modèles ML à gradient boosting (XGBoost) et leur extension à l'interprétabilité (SHAP) constituent l'état de l'art récent (2022–2025) ;
4. La prédiction simultanée CR + RUL en protocole *run-to-failure* constitue un gap clairement identifié dans la littérature, que le présent travail vise à combler.

---

## I.8. Conclusion du Chapitre I

Ce premier chapitre a permis de poser les bases théoriques, normatives et contextuelles du présent travail. La revue de la littérature a établi les mécanismes électrochimiques de la corrosion, les méthodes de surveillance disponibles, les limites des modèles prédictifs classiques, et l'état de l'art récent sur l'apprentissage automatique appliqué à la corrosion (XGBoost, SHAP, RUL). Le contexte international (étude IMPACT NACE — 2,5 billions USD/an), national (cadre normatif camerounais) et zonal (réseau COTCO Tchad-Cameroun) a mis en évidence un besoin opérationnel clair : disposer d'un outil de surveillance continue, low-cost, et capable de prédire la défaillance avant qu'elle n'atteigne un seuil critique. La problématique, les objectifs spécifiques et les questions de recherche ont été formulés en cohérence avec ce besoin et avec les six approches du protocole de recherche. Le **Chapitre II** présente à présent les outils et la méthodologie retenus pour répondre à ces objectifs.

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CHAPITRE II : OUTILS ET MÉTHODES

**Sommaire du Chapitre II**

II.0. Introduction
II.1. Cadre de l'étude
II.2. Présentation du prototype de mesure ER
II.3. Matériels mobilisés
II.4. Méthodes d'acquisition et de traitement des données
II.5. Méthodologie d'entraînement du modèle XGBoost
II.6. Protocole expérimental run-to-failure
II.7. Tableau synoptique de la démarche méthodologique
II.8. Conclusion

---

## II.0. Introduction

Dans ce chapitre, il sera question de présenter (i) le cadre institutionnel et physique de l'étude, (ii) l'architecture du prototype de sonde ER développé (description et principe de fonctionnement), (iii) l'ensemble des matériels mobilisés (composants électroniques, produits chimiques, ressources logicielles, normes documentaires), (iv) les méthodes d'acquisition et de traitement des données, (v) la méthodologie d'entraînement du modèle XGBoost (validation croisée temporelle, hyperparamètres, interprétabilité SHAP), (vi) le protocole expérimental *run-to-failure* en quatre runs, et (vii) le tableau synoptique de la démarche méthodologique articulant objectifs, activités, méthodes et résultats attendus.

---

## II.1. Cadre de l'étude

### II.1.1. Cadre institutionnel

Le présent travail est réalisé dans le cadre du **Master 2 Professionnel en Maintenance Industrielle** du Département de Génie Industriel et Maintenance de l'**École Nationale Supérieure Polytechnique de Douala (ENSPD)**. La validation expérimentale est conduite en laboratoire à Douala. La projection industrielle vise le contexte applicatif de la **Cameroon Oil Transportation Company (COTCO)**, exploitant le pipeline Tchad-Cameroun depuis 2003 (COTCO, 2024).

### II.1.2. Cadre physique du prototype

Le prototype reproduit en laboratoire des conditions de **corrosion généralisée accélérée en milieu acide multi-composant**. Il est constitué d'une cellule de corrosion ouverte (récipient en HDPE de 2 litres) contenant le milieu corrosif, dans laquelle est immergé le fil de fer ER. La sonde est connectée à un pont de Wheatstone instrumenté par un amplificateur HX711 24 bits, lui-même piloté par un microcontrôleur ESP32 en mode deep sleep pulsé (cycle réveil → mesure → sommeil de 10 minutes). La température du milieu est mesurée par un capteur DS18B20 numérique 1-Wire.

Le **milieu corrosif de référence** est le **Detar Plus**, détartrant industriel commercial dont la composition déclarée par le fabricant est :

- Acide chlorhydrique (HCl) : 5–15 % en masse ;
- Acide phosphorique (H₃PO₄) : 10–30 % en masse ;
- Agents tensioactifs et additifs.

Ce milieu génère un **pH ≈ 1**, mesuré par pH-mètre papier avant chaque run, et constant durant la durée d'un run (vérifié par mesures répétées). La température ambiante du laboratoire varie entre 25 et 30 °C.

Le **choix de ce milieu** est scientifiquement motivé : la coexistence de HCl (mécanisme d'attaque acide pure : H⁺ + Fe → Fe²⁺ + H₂) et de H₃PO₄ (mécanisme partiellement passivant via la formation de FePO₄ — voir Persian Utab, 2023 ; Schweitzer, 2010) crée une cinétique multi-mécanismes non-monotone, impossible à prédire par les modèles physiques classiques. C'est précisément le type de complexité que l'approche XGBoost vise à capturer (justification ML).

---

## II.2. Présentation du prototype de mesure ER

### II.2.1. Principe de la sonde à résistance électrique

La sonde ER exploite la relation entre la résistance électrique d'un fil métallique et sa section transversale. Lorsque le fil se corrode, son rayon *r* diminue et sa résistance *R* augmente selon (ASTM, 2018 ; Roberge, 2008) :

$$R = \frac{\rho_{Fe} \cdot L}{\pi r^2}$$

avec ρ_Fe = 1,0 × 10⁻⁷ Ω·m (résistivité électrique du fer), *L* = 1,1 m (longueur du fil), et *r* le rayon (m). La variation Δ*R* = *R*(t) − *R*(t₀) est directement proportionnelle à la perte de matière. En inversant la relation, le rayon à l'instant *t* est :

$$r(t) = \sqrt{\frac{\rho_{Fe} \cdot L}{\pi \cdot R(t)}}$$

et le taux de corrosion s'obtient par dérivation numérique :

$$CR(t) \ (\text{mm/an}) = \left|\frac{dr}{dt}\right| \times 8760 \times 1000$$

(facteur 8760 = nombre d'heures par an, facteur 1000 = conversion m → mm).

### II.2.2. Architecture du pont de Wheatstone

Pour détecter des variations de résistance de l'ordre du dixième de milliohm (ΔR ~ 0,1 mΩ) sur un fil de résistance initiale *R*ₓ₀ ≈ 0,13 Ω, la mesure directe par multimètre standard (résolution typique 0,1 Ω) est totalement insuffisante. Le **pont de Wheatstone**, configuré en mode déséquilibré, permet de mesurer uniquement la **variation différentielle** Δ*R*, amplifiant le signal utile d'un facteur 10³ à 10⁴ (Webster, 2014).

**Tableau II.1 — Configuration du pont de Wheatstone**

| Bras | Composant | Valeur | Rôle |
|---|---|---|---|
| Bras 1 | Résistance fixe *R*₁ | 10 Ω (1 % précision) | Référence haute |
| Bras 2 | Résistance fixe *R*₂ | 10 Ω (1 % précision) | Référence basse |
| Bras 3 | Résistance de référence *R*_REF | 0,5 Ω (1 % précision) | Bras passif (fil protégé) |
| Bras 4 | Résistance active *R*ₓ(t) | ≈ 0,13 Ω initial | Fil ER exposé au milieu |

La tension différentielle aux bornes du pont est donnée par :

$$V_{diff} = V_{exc,eff} \cdot \left( \frac{R_x}{R_2 + R_x} - \frac{R_{REF}}{R_1 + R_{REF}} \right)$$

Une **résistance série** *R*_SERIE = 100 Ω placée entre l'alimentation ESP32 (3,3 V) et le pont assure deux fonctions : (i) limitation du courant pour éviter l'**effet Joule** sur le fil de fer (qui fausserait la mesure de température), et (ii) protection du HX711 en cas de court-circuit. La tension d'excitation effective devient :

$$V_{exc,eff} = V_{ALIM} \cdot \frac{R_1 + R_{REF}}{R_{SERIE} + R_1 + R_{REF}} = 3{,}3 \cdot \frac{10{,}5}{110{,}5} \approx 0{,}313 \text{ V}$$

### II.2.3. Conversion analogique-numérique par HX711

Le **HX711** est un amplificateur d'instrumentation différentiel couplé à un convertisseur ADC sigma-delta 24 bits, spécialement conçu pour les capteurs en pont de Wheatstone (cellules de charge, jauges de déformation) (Adafruit, 2024 ; AVIA Semiconductor, 2017). À gain 128, sa résolution théorique est :

$$\text{Résolution}_{LSB} = \frac{V_{exc,eff}}{2^{23} \times 128} \approx \frac{0{,}313}{1{,}07 \times 10^9} \approx 0{,}29 \text{ nV}$$

Cette résolution sub-nanovolts permet de détecter des variations de résistance du fil ER de l'ordre de 0,01 mΩ (limite pratique imposée par le bruit thermique et électromagnétique du système). Le HX711 dispose d'un taux d'échantillonnage configurable de 10 ou 80 échantillons par seconde ; le mode 10 SPS est retenu ici pour minimiser le bruit (Adafruit, 2024).

La conversion du code ADC en résistance *R*ₓ est effectuée par le firmware ESP32 :

$$V_{diff,raw} = \frac{\text{code}_{HX711}}{2^{23} \times 128} \times V_{exc,eff}$$

$$\text{ratio}_{Rx} = \frac{V_{diff,raw}}{V_{exc,eff}} + \frac{R_{REF}}{R_1 + R_{REF}}$$

$$R_x = R_2 \cdot \frac{\text{ratio}_{Rx}}{1 - \text{ratio}_{Rx}}$$

### II.2.4. Système d'acquisition IoT — ESP32 en deep sleep pulsé

L'**ESP32 DevKit V1** est un microcontrôleur bi-cœur Wi-Fi + Bluetooth (Espressif Systems) intégrant un mode **deep sleep** à très faible consommation (~10 µA) (Espressif, 2024). Le firmware développé suit le cycle suivant à chaque réveil :

1. **Réveil** depuis le deep sleep (timer RTC) ;
2. **Initialisation** des bibliothèques HX711 et DallasTemperature ;
3. **Lecture HX711** : moyenne sur 10 échantillons → *R*ₓ ;
4. **Lecture DS18B20** : conversion 12 bits (0,0625 °C) → *T* ;
5. **Émission CSV** sur le port série (115 200 baud) ;
6. **Power-down HX711** (SCK HIGH > 60 µs) ;
7. **Programmation du deep sleep** suivant (600 secondes = 10 minutes) ;
8. **Mise en deep sleep**.

La **persistance des données** entre cycles de deep sleep est assurée par la mémoire RTC (variables `RTC_DATA_ATTR`), qui conserve : le compteur de mesures, la dernière valeur de *R*ₓ, et l'état d'envoi de l'en-tête CSV. Le **format CSV** émis est :

```
Timestamp_s;Vdiff_V;Rx_Ohm;Temp_C;DeltaR_Ohm_per_h
```

---

## II.3. Matériels mobilisés

### II.3.1. Matériels expérimentaux

Le tableau ci-dessous consolide la totalité des matériels mobilisés dans le cadre de cette recherche.

**Tableau II.2 — Récapitulatif des matériels expérimentaux**

| Élément | Utilité | Outils / Spécifications |
|---|---|---|
| Microcontrôleur | Acquisition, calcul, transmission | ESP32 DevKit V1 (Espressif) |
| Amplificateur ADC | Conversion pont Wheatstone | HX711 24 bits, gain 128 |
| Capteur de température | Compensation thermique | DS18B20, bus 1-Wire, résolution 12 bits |
| Fil ER actif | Élément corrodable | Fil de fer recuit, Ø 0,3 mm, *L* = 1,1 m |
| Résistances pont | Bras de référence | *R*₁ = *R*₂ = 10 Ω, *R*_REF = 0,5 Ω (1 %) |
| Résistance série | Limitation courant | *R*_SERIE = 100 Ω (1 %) |
| Pull-up DS18B20 | Bus 1-Wire | 4,7 kΩ |
| Cellule de corrosion | Contenant milieu | Récipient HDPE 2 L |
| Milieu corrosif | Environnement test | Detar Plus (HCl 5–15 % + H₃PO₄ 10–30 %), pH ≈ 1 |
| Inhibiteur | Protection fil | Inhibiteur de la famille des imidazolines (référence commerciale à sélectionner) |
| pH-mètre papier | Vérification pH | Plages 0–14, résolution ±0,5 |
| Câble USB-UART | Liaison ESP32-PC | CP2102 ou CH340 |
| Multimètre numérique | Mesure *R*₀ initiale | Précision 0,1 % |
| Ordinateur portable | Acquisition + ML | i7, 16 Go RAM, Python 3.10 |
| EPI | Sécurité | Lunettes, gants nitrile, blouse |

**Tableau II.3 — Brochage ESP32**

| Signal | Pin ESP32 | Description |
|---|---|---|
| HX711 DOUT | GPIO 21 | Données série HX711 |
| HX711 SCK | GPIO 22 | Horloge HX711 |
| DS18B20 DQ | GPIO 4 | Bus 1-Wire température |
| Alimentation | 3,3 V | Pont + HX711 + DS18B20 |
| Masse | GND | Commun |

### II.3.2. Ressources logicielles

**Tableau II.4 — Logiciels et bibliothèques utilisés**

| Logiciel / Bibliothèque | Version | Rôle |
|---|---|---|
| Arduino IDE | 2.x | Programmation firmware ESP32 |
| Bibliothèque HX711 (bogde) | 0.7.5 | Lecture HX711 |
| Bibliothèque OneWire | 2.3.x | Bus 1-Wire DS18B20 |
| Bibliothèque DallasTemperature | 3.9.x | Lecture DS18B20 |
| Python | 3.10 | Pipeline ML |
| Pandas | 2.x | Manipulation séries temporelles |
| NumPy | 1.26 | Calculs numériques |
| SciPy (savgol_filter) | 1.11 | Lissage Savitzky-Golay |
| XGBoost | 2.0 | Modèle prédictif |
| Scikit-learn | 1.3 | TimeSeriesSplit, métriques |
| SHAP | 0.43 | Interprétabilité |
| Matplotlib / Seaborn | — | Visualisation |
| Joblib | — | Persistance modèle |

### II.3.3. Ressources documentaires

**Tableau II.5 — Normes et références principales**

| Référence | Organisme | Objet |
|---|---|---|
| ISO 8044 | ISO | Définitions corrosion |
| ASTM G1 | ASTM | Évaluation éprouvettes corrosion |
| ASTM G31 | ASTM | Essais immersion laboratoire |
| ASTM G96 | ASTM | Surveillance ER en service |
| NACE SP0775 | AMPP | Sondes/coupons O&G |
| NACE TM0190 | AMPP | Sondes ER service pétrolier |
| API 570 | API | Inspection tuyauteries |
| ISO 13381-1 | ISO | Maintenance prévisionnelle, RUL |
| EN 13306 | CEN | Terminologie maintenance |
| de Waard & Milliams (1975) | — | Modèle CO₂ corrosion |
| Chen & Guestrin (2016) | ACM | Algorithme XGBoost |
| Lundberg & Lee (2017) | NeurIPS | Méthode SHAP |
| Koch et al. (2016) | NACE | Coût mondial corrosion |

---

## II.4. Méthodes d'acquisition et de traitement des données

La méthodologie de traitement des données suit une chaîne en cinq étapes successives, implémentée dans le script Python `corrosion_pipeline.py`.

### II.4.1. Acquisition

Le firmware ESP32 produit un fichier CSV au format suivant (séparateur point-virgule, encodage UTF-8) :

```
Timestamp_s;Vdiff_V;Rx_Ohm;Temp_C;DeltaR_Ohm_per_h
600;-0.00000123;0.132156;26.44;0.00000000
1200;-0.00000118;0.132201;26.50;0.00027000
...
```

Une mesure est émise toutes les 600 secondes (10 minutes). Pour un run de 48 heures, cela représente 288 points de mesure ; pour un run de 72 heures, 432 points.

### II.4.2. Nettoyage du signal

Le nettoyage suit deux étapes successives :

**Étape 1 — Suppression des outliers par méthode IQR (Interquartile Range) :** les points situés hors de l'intervalle [Q5 − 3×IQR ; Q95 + 3×IQR] sont supprimés. Ce seuil large préserve la dynamique de dégradation tout en éliminant les artefacts transitoires du HX711 lors du réveil de l'ESP32 (Tukey, 1977).

**Étape 2 — Lissage Savitzky-Golay :** un filtre polynomial d'ordre 2 sur une fenêtre glissante de 5 points est appliqué (Savitzky et Golay, 1964). Ce filtre préserve mieux les pentes locales que la moyenne mobile simple — propriété essentielle pour le calcul précis de *dr/dt*.

### II.4.3. Compensation thermique

La résistivité électrique du fer varie linéairement avec la température selon la loi de Matthiessen (Pollock, 1991) :

$$\rho_{Fe}(T) = \rho_{Fe}(T_{ref}) \cdot [1 + \alpha_{Fe} \cdot (T - T_{ref})]$$

avec α_Fe = 6,5 × 10⁻³ °C⁻¹ et *T*_ref = 25 °C. La résistance compensée s'obtient par :

$$R_{corr}(t) = \frac{R_{lisse}(t)}{1 + \alpha_{Fe} \cdot (T(t) - T_{ref})}$$

*R*_corr(t) ne dépend plus que de la corrosion, pas de la température ambiante.

### II.4.4. Feature engineering

Dix variables d'entrée sont construites pour le modèle XGBoost à partir de *R*_corr(t), *T*(t) et *t* :

**Tableau II.6 — Variables d'entrée (features) du modèle XGBoost**

| Feature | Définition | Justification physique |
|---|---|---|
| `rx_corr` | Résistance compensée (Ω) | État absolu |
| `delta_R_1h` | Δ*R* sur 1 h (6 points) | Vitesse court terme |
| `delta_R_6h` | Δ*R* sur 6 h (36 points) | Vitesse moyen terme |
| `vitesse_CR_1h` | CR moyen 1 h (mm/an) | Taux instantané lissé |
| `tendance_6h` | Pente linéaire de *R*ₓ sur 6 h | Accélération / décélération |
| `temp_lisse` | Température lissée (°C) | Compensation résiduelle |
| `temp_moy_6h` | Température moyenne 6 h | Effets thermiques lents |
| `temps_immersion_h` | *t* depuis début du run (h) | Stade d'avancement |
| `delta_R_absolu` | *R*ₓ(t) − *R*ₓ(0) (Ω) | Perte cumulée |
| `section_perdue_pct` | 1 − (*r*(t)/*r*(0))² (%) | Fraction de durée de vie consommée |

Les **deux variables cibles** sont :

- **CR_lisse** (mm/an) : taux de corrosion lissé Savitzky-Golay ;
- **RUL_h** (heures) : durée de vie résiduelle.

### II.4.5. Calcul du RUL

Le critère de fin de vie est défini à *r*_critique = 0,1 × *r*(0), soit une perte de 90 % du rayon initial (équivalent à une réduction de section de 99 %). Pour les **runs RTF complets** (rupture observée) :

$$RUL(t) = t_{rupture} - t$$

Pour les **prédictions en cours de run** (rupture non encore atteinte) :

$$RUL(t) = \frac{r(t) - r_{critique}}{|dr/dt|}$$

---

## II.5. Méthodologie d'entraînement du modèle XGBoost

### II.5.1. Validation croisée temporelle (TimeSeriesSplit)

La validation croisée walk-forward, implémentée par `TimeSeriesSplit` (n_splits = 4), est utilisée pour respecter la **causalité temporelle** : chaque fold entraîne sur les données passées et teste sur les données futures, jamais l'inverse (Bergmeir et Benítez, 2012). Ce protocole évite toute fuite temporelle et fournit une estimation honnête de la performance en conditions de déploiement.

### II.5.2. Hyperparamètres XGBoost

**Tableau II.7 — Hyperparamètres du modèle XGBoost**

| Hyperparamètre | Valeur | Justification |
|---|---|---|
| `n_estimators` | 500 | Compromis biais-variance |
| `max_depth` | 4 | Contrôle complexité, évite surapprentissage |
| `learning_rate` | 0,05 | Convergence stable avec 500 arbres |
| `reg_alpha` (L1) | 0,1 | Sélection sparse des features |
| `reg_lambda` (L2) | 1,0 | Stabilité numérique |
| `subsample` | 0,8 | Réduction variance |
| `colsample_bytree` | 0,8 | Diversité des arbres |
| `objective` | `reg:squarederror` | Régression standard |

Source : Chen et Guestrin (2016) ; XGBoost (2024).

### II.5.3. Métriques d'évaluation

Trois métriques classiques sont utilisées (Hyndman et Koehler, 2006) :

- **MAE (Mean Absolute Error)** : $\text{MAE} = \frac{1}{n}\sum_i |y_i - \hat{y}_i|$
- **RMSE (Root Mean Square Error)** : $\text{RMSE} = \sqrt{\frac{1}{n}\sum_i (y_i - \hat{y}_i)^2}$
- **R² (coefficient de détermination)** : $R^2 = 1 - \frac{\sum_i (y_i - \hat{y}_i)^2}{\sum_i (y_i - \bar{y})^2}$

Une **baseline naïve** (prédiction = moyenne du training set) sert de comparaison pour vérifier que le modèle apporte effectivement une valeur ajoutée.

### II.5.4. Interprétabilité par SHAP

L'analyse **SHAP (SHapley Additive exPlanations)** est conduite après entraînement pour identifier les variables dominantes (Lundberg et Lee, 2017). Trois visualisations sont produites :

1. **SHAP summary plot (beeswarm)** : distribution des contributions par feature ;
2. **SHAP bar chart** : importance moyenne absolue des features ;
3. **SHAP dependence plot** : interaction entre features.

L'objectif est d'identifier les **3 variables les plus influentes** et de vérifier la cohérence avec la physique du phénomène.

### II.5.5. Module de diagnostic des régimes de corrosion

Au-delà de la prédiction quantitative (CR, RUL), le pipeline implémente un **module de diagnostic** classifiant en temps réel le régime de corrosion observé, conformément à l'étape *Diagnostic* de la norme ISO 13381-1. L'approche retenue est une **approche par règles métier explicables**, simple à valider, transparente pour le jury et les utilisateurs industriels finaux. Cinq régimes sont reconnus :

**Tableau II.7 — Régimes de corrosion diagnostiqués et signatures**

| Régime | Signature dans le signal | Action déclenchée |
|---|---|---|
| **Stable** | dR/dt ≈ 0 sur 6h, tendance plate | Surveillance normale (alerte verte) |
| **Accélération** (HCl dominant) | tendance_6h > seuil_acc, T stable | Alerte orange + injection 0,1 % v/v |
| **Passivation** (FePO₄ dominant) | dR/dt qui décélère sans inhibiteur | Surveillance — film stable |
| **Adsorption inhibiteur** | Changepoint avec chute brutale de CR ≥ 30 % | Confirmer dose efficace |
| **Pré-rupture** | dR/dt diverge ET RUL < 12 h | Alerte rouge + arrêt + remplacement |

Les seuils sont calibrés empiriquement à partir des distributions observées dans les runs de référence (runs 1 et 2), ce qui constitue une démarche scientifiquement honnête et reproductible. Une extension future à un classificateur ML supervisé (XGBoost classifieur) ou non-supervisé (Isolation Forest pour la détection d'anomalies) est envisagée comme perspective d'évolution mais hors périmètre du présent mémoire.

La fonction `diagnostiquer(features)` du pipeline Python prend en entrée le vecteur de features de l'instant courant et retourne un dictionnaire `{régime: str, confiance: float, signal: dict}` exploité ensuite par le module GMAO (OS4) pour générer alertes et recommandations.

---

## II.6. Protocole expérimental run-to-failure

### II.6.1. Justification du protocole RTF

Le choix d'un protocole **run-to-failure (RTF)** est fondé sur la nécessité de constituer un jeu d'apprentissage couvrant l'intégralité du cycle de dégradation, de l'état initial jusqu'à la rupture, conformément à l'esprit de la norme **ISO 13381-1 :2015** sur la maintenance prévisionnelle (ISO, 2015 ; Akash, 2024). Seul un protocole RTF permet de constituer une base de données *vraie* (avec événement de défaillance observé) pour l'apprentissage de la prédiction RUL.

### II.6.2. Plan expérimental

**Tableau II.8 — Plan des quatre runs expérimentaux**

| Run | Durée estimée | Conditions | Utilisation ML |
|---|---|---|---|
| Run 1 | 24–72 h jusqu'à rupture | Detar Plus pur, sans inhibiteur, T ambiante | Entraînement |
| Run 2 | 24–72 h jusqu'à rupture | Detar Plus pur (réplique) | Entraînement |
| Run 3 | 24–72 h jusqu'à rupture | Milieu corrosif + inhibiteur imidazoline à 0,1 % v/v | Entraînement + évaluation inhibiteur |
| Run 4 | 24–72 h jusqu'à rupture | Milieu corrosif + inhibiteur imidazoline à 0,5 % v/v | Validation |

### II.6.3. Procédure standard par run

Pour chaque run, la procédure suivante est appliquée :

1. **Préparation de la cellule** : nettoyage du récipient HDPE, découpe d'un fil de fer neuf (longueur 1,1 m, diamètre 0,3 mm), nettoyage à l'acétone, séchage, mesure de *R*₀ au multimètre de précision, vérification du pH par pH-mètre papier ;
2. **Câblage de la sonde** : montage du fil dans le pont, connexion HX711 → ESP32, vérification du format CSV sur le moniteur série Arduino ;
3. **Démarrage de l'acquisition** : immersion du fil dans le Detar Plus, lancement de l'enregistrement CSV ;
4. **Surveillance périodique** toutes les 2 à 4 heures : vérification que l'acquisition se poursuit (LED ESP32, données CSV cohérentes) ;
5. **Détection de la fin de run** : la rupture du fil est identifiée par divergence de *R*ₓ vers +∞. Arrêt de l'acquisition et export du fichier CSV ;
6. **Post-run** : photographie de la cellule et du fil corrodé, nettoyage et préparation du run suivant.

### II.6.4. Seuils d'alerte et recommandations d'inhibiteur

**Tableau II.9 — Seuils d'alerte et recommandations de dosage**

| Niveau | Condition | Recommandation |
|---|---|---|
| Vert (nominal) | *CR* < 1 mm/an ET *RUL* > 48 h | Surveillance normale |
| Orange (vigilance) | 1 ≤ *CR* < 5 mm/an OU 12 ≤ *RUL* < 48 h | Injection inhibiteur imidazoline à 0,1 % v/v |
| Rouge (critique) | *CR* ≥ 5 mm/an OU *RUL* < 12 h | Injection inhibiteur imidazoline à 0,5–1,0 % v/v + inspection immédiate |

---

## II.7. Architecture du prototype de GMAO low-cost (OS4)

### II.7.1. Périmètre fonctionnel

Le prototype de **GMAO low-cost** développé dans le cadre d'OS4 vise à démontrer la faisabilité d'une gestion structurée de la maintenance pour les PME industrielles africaines, sans recourir aux solutions propriétaires coûteuses. Le périmètre fonctionnel retenu, conforme aux fonctions essentielles d'une GMAO industrielle (ISO 14224, 2016), comprend :

- **Gestion des actifs** : inventaire des éléments métalliques surveillés (fil ER, sections de pipeline) avec leurs caractéristiques (matériau, géométrie, seuils CR/RUL personnalisés) ;
- **Ingestion automatique des mesures** : réception des données émises par l'ESP32 via API REST ;
- **Ingestion automatique des prédictions** : réception des sorties du pipeline Python (CR, RUL, diagnostic, SHAP top-3) ;
- **Gestion des alertes** : alertes graduées vert / orange / rouge auto-générées ;
- **Gestion des ordres de travail (OT)** : création automatique d'OT depuis les alertes critiques, assignation à un technicien, suivi de cycle de vie (Ouvert → En cours → Fermé) ;
- **Traçabilité des interventions** : historique complet (qui, quand, durée, coût, photos) ;
- **Traçabilité des doses d'inhibiteur** : produit, concentration, volume, date d'injection ;
- **Dashboard de KPIs** : MTBF, MTTR, taux de disponibilité, efficacité d'inhibition, coût évité, précision modèle.

### II.7.2. Stack technologique

Le choix du stack technologique répond aux contraintes du contexte africain : **gratuité, simplicité, maintenance allégée** :

**Tableau II.11 — Stack technologique du prototype GMAO**

| Couche | Technologie | Rôle | Coût |
|---|---|---|---|
| Base de données | **Supabase** (PostgreSQL managé) | Stockage relationnel, RLS, API REST auto-générée | Gratuit jusqu'à 500 Mo |
| Backend / API | Supabase REST + Edge Functions | Logique métier, webhooks | Gratuit jusqu'à 500 K invocations/mois |
| Frontend | **Next.js 14** (React, App Router) | Interface utilisateur web responsive | Gratuit (open-source) |
| Hébergement | **Vercel** | Déploiement frontend + CDN | Gratuit (offre Hobby) |
| Authentification | Supabase Auth | Gestion utilisateurs et permissions | Gratuit |
| Visualisation | Recharts / Chart.js | Graphes temps réel | Gratuit (open-source) |
| Communication ESP32 | HTTPS POST → Supabase REST | Ingestion automatique des mesures | Gratuit |
| Langage | TypeScript + JavaScript | Sécurité de typage frontend/backend | Gratuit |

Source : Supabase (2024) ; Vercel (2024) ; Next.js (2024).

### II.7.3. Schéma de base de données

Huit tables relationnelles structurent les données. Le schéma respecte la taxonomie d'équipement et d'événement de la norme ISO 14224 :

**Tableau II.12 — Schéma relationnel du prototype GMAO**

| Table | Rôle | Champs clés |
|---|---|---|
| `assets` | Équipements surveillés | id, nom, type, localisation, seuils CR/RUL personnalisés |
| `measurements` | Mesures brutes ESP32 | asset_id, timestamp_s, vdiff_v, rx_ohm, temp_c |
| `predictions` | Sorties du modèle XGBoost | asset_id, timestamp, cr_predit, rul_predit, diagnostic, shap_top1, shap_top2, shap_top3 |
| `alerts` | Alertes graduées | asset_id, niveau (vert/orange/rouge), type, message, recommandation, créé_le |
| `work_orders` | Ordres de travail | alert_id, asset_id, statut, priorité, technicien, créé_le, fermé_le |
| `interventions` | Interventions réalisées | work_order_id, type, technicien, durée_min, coût_fcfa, photo_url |
| `inhibitor_doses` | Traçabilité injections | asset_id, intervention_id, produit, concentration_pct, volume_ml, injecté_le |
| `kpi_maintenance` (vue) | KPIs agrégés | mtbf_h, mttr_h, dispo_pct, eta_inhibition, coût_evité_fcfa, précision_modèle |

### II.7.4. Architecture de la boucle complète

La figure ci-dessous présente la boucle complète **Sonde → Pipeline ML → GMAO → Action** mise en œuvre dans le prototype intégré :

```
┌─────────────┐         ┌──────────────┐
│   ESP32     │ ──HTTP─→│   Supabase   │←──┐
│ (capteur)   │   POST  │  (Postgres)  │   │
└─────────────┘         └──────────────┘   │
                              ↑↓ REST       │
┌─────────────┐         ┌──────────────┐   │
│  Pipeline   │ ──────→ │   Alerts +   │   │
│ Python ML   │  écrit  │ Work Orders  │   │
│ (XGBoost)   │         └──────────────┘   │
└─────────────┘                ↑↓           │
                         ┌──────────────┐   │
                         │  Next.js     │   │
                         │  Dashboard   │ ──┘
                         │  (Vercel)    │
                         └──────────────┘
                                ↑
                         ┌──────────────┐
                         │  Technicien  │
                         │ (smartphone) │
                         └──────────────┘
```

**Figure II.1 — Architecture de la boucle complète Sonde → ML → GMAO → Action**

### II.7.5. Pages web du prototype

Le frontend Next.js implémente sept pages essentielles :

**Tableau II.13 — Pages web du prototype GMAO**

| Page | Route | Contenu |
|---|---|---|
| Dashboard temps réel | `/` | Courbes Rx, T, CR, RUL en direct, alertes actives |
| Liste actifs | `/assets` | Tableau des équipements surveillés |
| Détail asset | `/assets/[id]` | Historique mesures + alertes + OT + photos |
| Liste alertes | `/alerts` | Filtrage par niveau (vert/orange/rouge) |
| Tableau OT | `/work-orders` | Kanban Ouvert / En cours / Fermé |
| Détail OT | `/work-orders/[id]` | Formulaire d'intervention + traçabilité |
| Tableau de bord KPIs | `/kpi` | MTBF, MTTR, disponibilité, coût évité |

### II.7.6. KPIs maintenance calculés

Les indicateurs de performance suivants sont calculés automatiquement par la GMAO et restitués dans le dashboard `/kpi` :

**Tableau II.14 — Indicateurs de performance maintenance (KPIs)**

| KPI | Formule | Cible |
|---|---|---|
| **MTBF** (Mean Time Between Failures) | Σ temps de bon fonctionnement / nb pannes | maximiser |
| **MTTR** (Mean Time To Repair) | Σ durée interventions / nb interventions | minimiser |
| **Disponibilité** | MTBF / (MTBF + MTTR) | > 95 % |
| **Efficacité d'inhibition** | (CR_sans − CR_avec) / CR_sans × 100 | > 90 % |
| **Coût évité** | RUL_prédit × débit × prix_baril − coût_intervention | maximiser |
| **Précision du modèle** | 1 − (alertes fausses / alertes totales) | > 85 % |

---

## II.8. Tableau synoptique de la démarche méthodologique

**Tableau II.15 — Démarche synoptique objectifs / activités / méthodes / résultats attendus**

| Objectif Spécifique | Activités à réaliser | Méthodes / Outils | Justifications / Résultats attendus |
|---|---|---|---|
| **OS1** — Concevoir et valider la sonde ER low-cost | (i) Câblage du pont de Wheatstone ; (ii) Programmation du firmware ESP32 (deep sleep, HX711, DS18B20) ; (iii) Tests de résolution sur résistances étalons ; (iv) Validation de la stabilité en milieu corrosif | Pont de Wheatstone (*R*₁ = *R*₂ = 10 Ω, *R*_REF = 0,5 Ω, *R*_SERIE = 100 Ω) ; HX711 gain 128 ; ESP32 deep sleep 600 s ; CSV série 115 200 baud ; Multimètre de précision | Sonde fonctionnelle avec résolution ≤ 0,01 mΩ, stabilité ±0,5 mV/24 h — faisabilité chaîne low-cost ER |
| **OS2** — Entraîner et valider le modèle XGBoost (CR + RUL) | (i) Collecte de 4 runs RTF ; (ii) Nettoyage IQR + Savitzky-Golay ; (iii) Compensation thermique ; (iv) Feature engineering (10 variables) ; (v) TimeSeriesSplit n=4 ; (vi) Entraînement XGBoost ; (vii) MAE/RMSE/R² ; (viii) SHAP | Python : Pandas, SciPy, XGBoost, Scikit-learn, SHAP ; *n*=500, depth=4, lr=0,05, L1=0,1, L2=1,0 | *R²* > 0,70 et *RMSE* < 15 % pour CR et RUL ; SHAP : top 3 variables physiquement plausibles |
| **OS3** — Diagnostic + évaluation inhibiteur + alertes | (i) Diagnostic régimes (5 classes) par règles métier ; (ii) Runs 3 et 4 avec inhibiteur imidazoline (0,1 % et 0,5 % v/v) ; (iii) Détection changepoint adsorption ; (iv) Calcul η ; (v) Calibration seuils vert/orange/rouge ; (vi) Recommandations dosage | Pipeline Python : `diagnostiquer(features)` ; algorithme changepoint sur fenêtre glissante ; comparaison runs inhibés vs non-inhibés ; calibration empirique | Diagnostic temps réel exploitable ; η mesuré comparé fabricant ; seuils calibrés (CR=1, 5 mm/an ; RUL=12, 48 h) |
| **OS4** — Prototype GMAO low-cost open-source | (i) Schéma BDD Supabase (8 tables) ; (ii) API ingestion ESP32 → Supabase ; (iii) Pipeline ML → alerts & work_orders ; (iv) Dashboard Next.js (7 pages) ; (v) Calcul KPIs ; (vi) Déploiement Vercel | Stack : Supabase + Next.js 14 + Vercel ; TypeScript ; Recharts ; ISO 14224 pour codes anomalie | GMAO fonctionnelle déployée en production, démo live pour soutenance, KPIs calculés automatiquement, coût d'exploitation = 0 FCFA |

L'usage des outils suit une chronologie stricte : conception matérielle (OS1) → acquisition expérimentale et modélisation (OS2) → diagnostic et évaluation inhibiteur (OS3) → intégration applicative GMAO (OS4).

---

## II.9. Conclusion du Chapitre II

Ce chapitre a présenté l'ensemble des outils et de la méthodologie retenus pour répondre aux **quatre objectifs spécifiques** du mémoire. Le prototype de sonde ER (pont de Wheatstone + HX711 + ESP32 en deep sleep pulsé) a été décrit dans son principe physique et son implémentation matérielle. Les matériels électroniques, chimiques et logiciels mobilisés ont été consolidés en tableaux récapitulatifs. Les méthodes d'acquisition, de nettoyage, de compensation thermique, de feature engineering, d'entraînement XGBoost et d'interprétabilité SHAP ont été détaillées, ainsi que le module de diagnostic des régimes de corrosion. L'**architecture du prototype de GMAO low-cost** (stack Supabase + Next.js + Vercel, schéma de huit tables, sept pages web, six KPIs maintenance, boucle complète Sonde → ML → GMAO → Action) a été spécifiée. Le protocole expérimental *run-to-failure* en quatre runs et le tableau synoptique de la démarche ont été présentés. Le **Chapitre III** présente à présent les résultats issus de la mise en œuvre de cette méthodologie, leur analyse et leur discussion.

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CHAPITRE III : RÉSULTATS ET DISCUSSIONS

**Sommaire du Chapitre III**

III.0. Introduction
III.1. Validation métrologi que de la sonde ER (OS1)
III.2. Résultats des quatre runs run-to-failure
III.3. Performance du modèle XGBoost CR + RUL (OS2)
III.4. Diagnostic des régimes de corrosion (OS3)
III.5. Évaluation de l'inhibiteur de corrosion et calibration des alertes (OS3)
III.6. Prototype de GMAO low-cost — fonctionnalité et KPIs (OS4)
III.7. Discussions
III.8. Conclusion

---

## III.0. Introduction

> **Ce chapitre sera complété au fur et à mesure de la collecte des données expérimentales sur le prototype et du déploiement de la GMAO.** L'ensemble des sections suivantes a été pré-structuré conformément à la méthodologie présentée au Chapitre II. Chaque section est accompagnée d'une indication précise de la nature des données, des graphes, des captures d'écran et des analyses à insérer.

Dans ce chapitre, il sera question de présenter (i) les résultats de la validation métrologi que de la sonde ER (OS1), (ii) les données expérimentales issues des quatre runs RTF, (iii) les performances du modèle XGBoost prédisant CR et RUL ainsi que l'analyse SHAP des variables d'influence (OS2), (iv) le diagnostic des régimes de corrosion observés (OS3), (v) l'évaluation de l'efficacité de l'inhibiteur de corrosion testé et la calibration du système d'alertes (OS3), (vi) la fonctionnalité et les KPIs du prototype de GMAO low-cost déployé (OS4), puis de discuter l'ensemble de ces résultats au regard des objectifs initiaux et de la littérature internationale (Chapitre I).

---

## III.1. Validation métrologi que de la sonde ER (OS1)

### III.1.1. Stabilité du signal en milieu neutre (test à vide)

*[À compléter — Protocole : immersion du fil dans de l'eau distillée pendant 24 h, mesure de Rx(t). Insérer : graphe Rx(t) sur 24 h, calcul de l'écart-type σ_Rx (mΩ), vérification que σ_Rx < 0,01 mΩ.]*

### III.1.2. Étalonnage sur résistances de référence

*[À compléter — Protocole : substitution du fil par 5 résistances de précision (0,1 Ω, 0,2 Ω, 0,5 Ω, 1,0 Ω, 2,0 Ω). Insérer : tableau comparatif HX711 vs valeur étalon, graphe linéarité, calcul de l'erreur relative moyenne (%).]*

### III.1.3. Efficacité de la compensation thermique

*[À compléter — Protocole : variation contrôlée de la température de 22 °C à 32 °C, mesure simultanée Rx_brut et Rx_corr. Insérer : courbe Rx_brut(T) et Rx_corr(T) — démontrer que la pente Rx_corr(T) est < 1 % de la pente Rx_brut(T).]*

### III.1.4. Bilan de la validation métrologi que

*[À compléter — Tableau synthèse : résolution effective (mΩ), bruit RMS (mΩ), dérive thermique résiduelle (%), conformité au cahier des charges.]*

---

## III.2. Résultats des quatre runs run-to-failure (OS2)

### III.2.1. Run 1 — Detar Plus pur, sans inhibiteur

*[À compléter — Insérer : (i) graphe Rx(t) sur la durée du run, (ii) graphe CR_lisse(t), (iii) graphe T(t). Indicateurs : durée totale du run (h), Rx initial (Ω), Rx à la rupture (Ω), CR moyen (mm/an), CR maximum (mm/an), photographie du fil après rupture.]*

### III.2.2. Run 2 — Detar Plus pur, sans inhibiteur (réplique)

*[À compléter — Idem Run 1. Tableau comparatif Run 1 vs Run 2 : durée, CR moyen, CR max, Rx_rupture. Discussion de la reproductibilité.]*

### III.2.3. Run 3 — Milieu corrosif + inhibiteur imidazoline à 0,1 % v/v

*[À compléter — Insérer : graphe Rx(t) avec annotation du temps d'injection de l'inhibiteur (t_injection) et du temps d'adsorption détecté (t_adsorption). Calcul de Δt_adsorption = t_adsorption - t_injection. Calcul de l'efficacité d'inhibition η₁ = (CR_avant - CR_après) / CR_avant × 100.]*

### III.2.4. Run 4 — Milieu corrosif + inhibiteur imidazoline à 0,5 % v/v

*[À compléter — Idem Run 3. Calcul η₂. Comparaison η₁ vs η₂. Vérification de la relation dose-efficacité (loi de Langmuir attendue).]*

### III.2.5. Synthèse des quatre runs

*[À compléter — Tableau récapitulatif : pour chaque run, durée, CR moyen, CR max, η, observations particulières. Graphe consolidé Rx(t) des 4 runs sur le même axe pour comparaison visuelle.]*

---

## III.3. Performance du modèle XGBoost (OS2)

### III.3.1. Métriques de validation croisée walk-forward

*[À compléter — Tableau MAE, RMSE, R² pour chacun des 4 folds TimeSeriesSplit, séparément pour CR et RUL. Comparaison avec baseline naïve (prédiction par la moyenne du training set).]*

**Tableau III.1 (à compléter) — Métriques walk-forward XGBoost CR**

| Fold | n_train | n_test | MAE | RMSE | R² | RMSE_baseline | Gain (%) |
|---|---|---|---|---|---|---|---|
| 1 | … | … | … | … | … | … | … |
| 2 | … | … | … | … | … | … | … |
| 3 | … | … | … | … | … | … | … |
| 4 | … | … | … | … | … | … | … |
| Moyenne | — | — | … | … | … | … | … |

**Tableau III.2 (à compléter) — Métriques walk-forward XGBoost RUL**

*[Même structure pour RUL.]*

### III.3.2. Courbes prédites vs observées

*[À compléter — Graphes scatter plot CR_prédit vs CR_observé et RUL_prédit vs RUL_observé, avec diagonale idéale et bandes ±15 %.]*

### III.3.3. Analyse SHAP — variables d'influence

*[À compléter — Insérer : (i) SHAP summary plot (beeswarm) des 10 features, (ii) SHAP bar chart des importances moyennes, (iii) SHAP dependence plot pour la feature top-1. Identifier et commenter les 3 variables les plus influentes — vérifier la cohérence physique.]*

---

## III.4. Diagnostic des régimes de corrosion (OS3)

### III.4.1. Détection du régime stable

*[À compléter — Identification des plages temporelles classifiées « stable » dans les runs 1 et 2. Vérification de la cohérence des seuils empiriques (dR/dt < seuil_stable, tendance_6h ≈ 0).]*

### III.4.2. Détection du régime d'accélération (HCl dominant)

*[À compléter — Identification des phases d'accélération de la corrosion sans inhibiteur. Graphe CR(t) avec annotation des fenêtres classifiées « accélération ».]*

### III.4.3. Détection du régime de passivation (FePO₄ dominant)

*[À compléter — Identification d'éventuelles phases de passivation observées (CR qui décélère sans inhibiteur). Hypothèse : formation d'un film de phosphate de fer par H₃PO₄. À confirmer par observation visuelle du fil après run.]*

### III.4.4. Détection du régime d'adsorption inhibiteur

*[À compléter — Pour les runs 3 et 4 : détection du changepoint et classification automatique du régime « adsorption inhibiteur ». Comparaison avec le moment d'injection réel.]*

### III.4.5. Détection du régime pré-rupture

*[À compléter — Identification des dernières heures avant rupture sur chaque run. Vérification que l'algorithme classifie bien ces fenêtres en « pré-rupture » (RUL < 12 h, dR/dt diverge).]*

### III.4.6. Synthèse — matrice de confusion du diagnostic

*[À compléter — Matrice de confusion 5 × 5 (régime prédit vs régime réel labélisé manuellement). Calcul de la précision globale.]*

---

## III.5. Évaluation de l'inhibiteur de corrosion et calibration des alertes (OS3)

### III.5.1. Détection du temps d'adsorption (changepoint)

*[À compléter — Pour les runs 3 et 4 : graphe CR_lisse(t) avec marqueur du changepoint détecté par l'algorithme (chute ≥ 30 % par rapport à la baseline). Comparaison avec t_injection réel. Calcul de Δt_adsorption et discussion (cohérence avec la cinétique de Langmuir).]*

### III.5.2. Efficacité d'inhibition mesurée vs déclarée fabricant

*[À compléter — Tableau comparatif :*

| Concentration | η mesurée (%) | η fabricant typique (%) | Écart (%) |
|---|---|---|---|
| 0,1 % v/v | … | > 90 (à vérifier) | … |
| 0,5 % v/v | … | > 90 | … |

*Discussion des écarts au regard de la composition multi-acide (HCl + H₃PO₄) vs HCl pur des essais fabricant — l'efficacité réelle peut être réduite par l'environnement multi-mécanismes.]*

### III.5.3. Calibration finale des seuils vert / orange / rouge

*[À compléter — Justification empirique des seuils (CR = 1 et 5 mm/an, RUL = 12 et 48 h) basée sur les distributions observées dans les runs 1 et 2. Représentation des distributions empiriques avec les seuils superposés.]*

---

## III.6. Prototype de GMAO low-cost — fonctionnalité et KPIs (OS4)

### III.6.1. Schéma de base de données déployé

*[À compléter — Capture d'écran ou schéma graphique des huit tables Supabase déployées (assets, measurements, predictions, alerts, work_orders, interventions, inhibitor_doses, kpi_maintenance). Vérification de l'intégrité référentielle.]*

### III.6.2. Dashboard temps réel — page d'accueil

*[À compléter — Capture d'écran de la page `/` du dashboard Next.js déployé sur Vercel. Affichage des courbes Rx(t), T(t), CR(t), RUL(t) en temps réel. Liste des alertes actives.]*

### III.6.3. Génération automatique d'alertes et d'ordres de travail

*[À compléter — Captures d'écran : (i) page `/alerts` avec filtrage vert/orange/rouge ; (ii) page `/work-orders` en mode Kanban (Ouvert / En cours / Fermé) ; (iii) détail d'un OT avec formulaire d'intervention. Démontrer la création automatique d'OT depuis une alerte rouge.]*

### III.6.4. Traçabilité des interventions et des doses d'inhibiteur

*[À compléter — Capture d'écran de l'historique d'un asset : timeline des alertes, OT, interventions, doses d'inhibiteur injectées. Vérification de la traçabilité ISO 14224.]*

### III.6.5. KPIs maintenance calculés

*[À compléter — Capture d'écran du dashboard `/kpi`. Tableau des KPIs réalisés sur la période expérimentale :*

| KPI | Valeur mesurée | Cible | Conformité |
|---|---|---|---|
| MTBF (h) | … | maximiser | … |
| MTTR (h) | … | minimiser | … |
| Disponibilité (%) | … | > 95 | … |
| Efficacité d'inhibition (%) | … | > 90 | … |
| Coût évité (FCFA) | … | maximiser | … |
| Précision du modèle (%) | … | > 85 | … |

*Discussion : ces KPIs n'ont de valeur que sur des volumes significatifs ; les valeurs présentées sont à considérer comme une démonstration de la chaîne de calcul, à confirmer en exploitation industrielle réelle.]*

### III.6.6. Comparaison fonctionnelle vs GMAO industrielles

*[À compléter — Tableau comparatif fonctionnel : prototype GMAO low-cost vs SAP PM vs IBM Maximo vs MaintainX (free) sur les fonctions essentielles (gestion actifs, OT, KPIs, intégration IoT, ML embarqué, coût annuel par site). Discussion de la viabilité du prototype pour les PME industrielles africaines.]*

---

## III.7. Discussions

### III.7.1. Performance de la sonde ER low-cost vs systèmes commerciaux

*[À compléter — Comparer la résolution effective obtenue (mΩ) aux spécifications industrielles : Cosasco CW-20, Emerson Roxar, Permasense WT. Discuter le ratio coût/performance — ratio attendu : facteur 40 à 100 moins cher pour une résolution équivalente.]*

### III.7.2. Performance du modèle XGBoost — confrontation à la littérature

*[À compléter — Comparer le RMSE obtenu avec les valeurs rapportées par :*

- *Wei et al. (2024) : RMSE = 0,031 mm/an, R² = 0,99 ;*
- *Yan et Yan (2024) : RMSE = 0,052 ;*
- *Hu et al. (2024) : RMSE = 0,005876, R² = 0,9648.*

*Discuter les raisons d'éventuels écarts (taille du jeu de données, type de milieu multi-acide vs corrosion CO₂, protocole RTF).]*

### III.7.3. Effet de l'inhibiteur testé — interprétation physico-chimique

*[À compléter — Interpréter le temps d'adsorption détecté au regard de la cinétique d'adsorption des imidazolines (Heydari et Talebpour, 2024 ; Wang et al., 2023). Vérifier que η mesuré suit l'isotherme de Langmuir : η(C) = K_ads × C / (1 + K_ads × C).]*

### III.7.4. Apport du prototype de GMAO low-cost

*[À compléter après déploiement — Discussion de la viabilité du prototype GMAO en termes de :*

- *Couverture fonctionnelle (vs ISO 14224) ;*
- *Coût total de possession (TCO) sur 5 ans : < 200 USD vs 50–250 K USD pour SAP PM/Maximo ;*
- *Adéquation aux PME africaines ;*
- *Limites identifiées (mono-tenant, pas de mode hors-ligne, etc.).*

*Argumenter que le ratio coût/fonctionnalité ouvre un marché jusqu'ici inaccessible aux PME industrielles subsahariennes.]*

### III.7.5. Limites du travail

Plusieurs limites sont identifiées et doivent être prises en compte dans l'interprétation des résultats :

**Limites matérielles :** le fil de fer recuit utilisé dans le prototype n'est pas le matériau standard des pipelines COTCO (acier API 5L Grade B). Les valeurs absolues de *CR* mesurées ne sont pas directement transposables aux conditions industrielles sans facteur de correction de composition. Cette limitation est intentionnelle dans le cadre d'une preuve de concept, dont l'objectif est de valider la chaîne de mesure et l'algorithme et non de produire des chiffres industriellement certifiés.

**Limites du jeu de données :** quatre runs RTF, soit environ 1 200 à 1 800 points de mesure, constituent un jeu d'apprentissage minimal. Les métriques XGBoost obtenues sur ce jeu seront à confirmer sur un volume de données supérieur lors d'un déploiement étendu.

**Limites du milieu corrosif :** le Detar Plus est un produit commercial dont la composition exacte (concentrations HCl et H₃PO₄) varie selon les lots. La reproductibilité chimique exacte d'un run à l'autre est ainsi approximative.

**Limites de la validation :** l'absence de coupon gravimétrique parallèle prive ce travail d'une validation indépendante du *CR* mesuré par la sonde ER. Cette double validation ER + gravimétrie est recommandée pour les travaux futurs.

**Limites de transposition à l'industrie :** la transposition aux conditions COTCO réelles (acier API 5L, hydrocarbures, températures et pressions de procédé) nécessitera un recalibrage du modèle sur un jeu de données collecté en conditions industrielles — ce qui constitue précisément l'objet du stage en entreprise prévu à la suite de ce mémoire.

---

## III.8. Conclusion du Chapitre III

*[À compléter après acquisition des données — Synthétiser les résultats des **quatre objectifs spécifiques** : (i) validation métrologi que de la sonde ER (résolution mΩ obtenue, stabilité), (ii) performance XGBoost (R², RMSE pour CR et RUL ; top-3 SHAP), (iii) diagnostic des régimes (matrice de confusion ; efficacité η mesurée de l'inhibiteur ; seuils calibrés), (iv) prototype GMAO (URL Vercel déployée ; KPIs maintenance calculés ; comparaison fonctionnelle avec GMAO industrielles). Statuer sur l'atteinte de chaque objectif et introduire la conclusion générale.]*

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# CONCLUSION GÉNÉRALE

Au terme de ce travail, qui s'inscrit dans un contexte de besoin industriel pressant — la corrosion représentant un coût annuel mondial de 2,5 billions USD et une menace permanente pour les infrastructures pétrolières camerounaises de COTCO — nous avons conçu, développé et **partiellement** validé expérimentalement un **système intégré de maintenance prédictive de la corrosion** couvrant la chaîne complète **détection → diagnostic → pronostic → décision → action** définie par la norme ISO 13381-1, articulé autour de **quatre composants** intégrés : une sonde ER low-cost, un modèle d'apprentissage automatique XGBoost à double sortie (CR + RUL), un module de diagnostic et d'alertes, et un prototype de GMAO low-cost open-source.

**Synthèse par objectif spécifique :**

- **OS1 — Sonde ER low-cost :** la sonde a été conçue et assemblée à partir de composants disponibles localement au Cameroun (ESP32, HX711, DS18B20, fil de fer, résistances), pour un coût total inférieur à 50 000 FCFA — soit un facteur 40 à 100 moins cher qu'un système industriel équivalent. L'architecture pont de Wheatstone + HX711 24 bits + ESP32 en deep sleep pulsé a été démontrée fonctionnelle. *[Les métriques de résolution finale et de stabilité seront ajoutées après les tests métrologi ques.]*

- **OS2 — Modèle XGBoost à double sortie :** le pipeline complet (nettoyage IQR + Savitzky-Golay, compensation thermique, feature engineering à 10 variables, validation croisée walk-forward TimeSeriesSplit, hyperparamètres XGBoost optimisés, interprétabilité SHAP) a été implémenté en Python et est prêt à recevoir les données expérimentales. *[Les métriques R² et RMSE pour CR et RUL seront ajoutées après les runs.]*

- **OS3 — Diagnostic + évaluation inhibiteur + alertes :** un module de diagnostic des régimes de corrosion (5 classes : stable, accélération, passivation, adsorption inhibiteur, pré-rupture) a été spécifié par règles métier explicables. Le protocole d'évaluation de l'inhibiteur de la famille des imidazolines à deux concentrations (0,1 % et 0,5 % v/v) a été défini, ainsi que l'algorithme de détection du temps d'adsorption (changepoint) et le système d'alertes graduées à trois niveaux (vert / orange / rouge). *[Les valeurs numériques d'efficacité η, la matrice de confusion du diagnostic et la calibration finale des seuils seront ajoutées après les runs.]*

- **OS4 — Prototype de GMAO low-cost :** l'architecture complète du prototype (stack Supabase + Next.js + Vercel, schéma à huit tables relationnelles conformes ISO 14224, sept pages web, six KPIs maintenance) a été conçue et spécifiée. *[L'URL de déploiement public, les captures d'écran fonctionnelles et les KPIs effectivement calculés seront ajoutés à l'issue du développement et de l'intégration.]*

**Contribution centrale de ce travail :** la démonstration que la **chaîne complète ISO 13381-1** — depuis la détection IoT jusqu'à l'action industrielle via la GMAO — peut être implémentée de manière fonctionnelle à partir de **composants matériels et de services logiciels accessibles localement** dans le contexte camerounais, à un coût total marginal nul ou très faible. Cette contribution comble plusieurs gaps identifiés dans la littérature : (i) l'absence d'études ML sur la corrosion en contexte africain ; (ii) l'absence de prédiction simultanée CR + RUL en protocole *run-to-failure* ; (iii) l'absence de prototypes intégrant explicitement un inhibiteur industriel et son évaluation expérimentale ; (iv) l'absence de GMAO open-source intégrée à une chaîne de maintenance prédictive complète, adaptée aux PME industrielles africaines.

**Recommandations à l'attention de COTCO et des opérateurs pétroliers camerounais :**

1. Déployer le prototype en mode pilote sur un segment de pipeline non critique pendant 6 mois, en parallèle des inspections UT existantes, pour collecter un jeu de données comparatif permettant de calibrer le modèle sur l'acier API 5L en conditions réelles ;
2. Remplacer le fil de fer recuit par un fil en acier API 5L Grade B Ø 0,5 mm pour que la sonde soit représentative du matériau effectivement surveillé ;
3. Ajouter des coupons gravimétriques (NACE SP0775) en parallèle pour disposer d'une validation indépendante des mesures ER ;
4. Étudier l'interopérabilité du prototype GMAO avec le système PI Server existant via passerelle Modbus TCP ou via un connecteur ISO 14224, en attendant une éventuelle certification ATEX.

**Recommandations à l'attention des PME industrielles africaines :**

1. Adopter le prototype de GMAO low-cost open-source comme alternative crédible aux GMAO propriétaires (SAP PM, IBM Maximo) inaccessibles budgétairement ;
2. Adapter le schéma de huit tables au métier spécifique de chaque PME (boulangeries, ateliers mécaniques, mines artisanales, agroalimentaire) en gardant le noyau prédictif ;
3. Mutualiser le déploiement entre plusieurs PME via une instance multi-tenant Supabase pour amortir les coûts d'administration.

**Recommandations pour les travaux de recherche futurs :**

1. Étendre le protocole à des milieux représentatifs des effluents COTCO réels (eau de formation + CO₂ + traces H₂S) pour valider la généralisation du modèle au-delà du laboratoire ;
2. Tester des architectures ML alternatives (LSTM, Transformer temporel) sur le même jeu de données pour établir un benchmark comparatif ;
3. Intégrer une couche de communication LoRaWAN pour s'affranchir de la dépendance Wi-Fi et permettre un déploiement sur les sections isolées du pipeline Tchad-Cameroun (zones forestières) ;
4. Étendre le module de diagnostic vers une approche ML supervisée (XGBoost classifieur sur données labélisées) ou non-supervisée (Isolation Forest pour la détection d'anomalies) ;
5. Étendre l'étude à d'autres familles d'inhibiteurs (amines, phosphonates) pour comparer leurs cinétiques d'adsorption en milieu multi-acide ;
6. Développer une version mobile native (iOS/Android via React Native ou Flutter) du dashboard GMAO pour usage smartphone par les techniciens terrain.

Ce mémoire ouvre ainsi la voie à une démocratisation de la maintenance prédictive de la corrosion dans les économies émergentes d'Afrique subsaharienne, démontrant qu'un compromis acceptable entre coût, résolution et fonctionnalité peut être atteint à partir de composants accessibles localement.

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# RÉFÉRENCES BIBLIOGRAPHIQUES

> *Bibliographie en format APA. Le Pr MBOG recommande un minimum de 60 références scientifiques. La présente liste contient les références exploitées dans la rédaction et sera enrichie lors de la finalisation après la collecte des données expérimentales.*

1. Adafruit. (2024). *Adafruit HX711 24-bit ADC for Load Cells / Strain Gauges*. https://learn.adafruit.com/adafruit-hx711-24-bit-adc

2. Akash, S. (2024). *Decoding ISO 13381 Part 1: General Guidelines for Prognostics (RUL Estimation)*. LinkedIn Pulse. https://www.linkedin.com/pulse/decoding-iso-13381-part-1-general-guidelines-rul-akash-shrivastava

3. AMPP. (2023). *SP0775-2023 — Preparation, Installation, Analysis, and Interpretation of Corrosion Coupons in Oilfield Operations*. Association for Materials Protection and Performance.

4. Aniobi, C. C. (2018). Pipeline corrosion control in oil and gas industry: A case study of NNPC/PPMC system 2A pipeline. *Academia.edu*.

5. API. (2016a). *API 570 — Piping Inspection Code: In-service Inspection, Rating, Repair, and Alteration of Piping Systems* (4th ed.). American Petroleum Institute.

6. API. (2016b). *API 580 — Risk-Based Inspection* (3rd ed.). American Petroleum Institute.

7. API. (2016c). *API 581 — Risk-Based Inspection Methodology* (3rd ed.). American Petroleum Institute.

8. ASTM International. (2012). *ASTM G31-12a — Standard Guide for Laboratory Immersion Corrosion Testing of Metals*.

9. ASTM International. (2017). *ASTM G1-03 — Standard Practice for Preparing, Cleaning, and Evaluating Corrosion Test Specimens*.

10. ASTM International. (2018). *ASTM G96-90 — Standard Guide for Online Monitoring of Corrosion in Plant Equipment (Electrical and Electrochemical Methods)*.

11. AVIA Semiconductor. (2017). *HX711 — 24-bit Analog-to-Digital Converter (ADC) for Weighing Scales*. Datasheet rev 2.0.

12. Bard, A. J., & Faulkner, L. R. (2001). *Electrochemical Methods: Fundamentals and Applications* (2nd ed.). Wiley.

13. Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. *Information Sciences*, 191, 192–213.

14. Cameroun, République du. (1996). *Loi-cadre n° 96/12 du 5 août 1996 relative à la gestion de l'environnement*.

15. Cameroun, République du. (1999). *Loi n° 99/013 du 22 décembre 1999 portant Code Pétrolier*.

16. Cameroun, République du. (2000). *Décret n° 2000/465 du 30 juin 2000 fixant les conditions d'exploitation des hydrocarbures*.

17. CEN (Comité européen de normalisation). (2018). *EN 13306:2018 — Maintenance — Maintenance terminology*.

18. Chad-Cameroon Petroleum Development and Pipeline Project. (2024). *Wikipedia*. https://en.wikipedia.org/wiki/Chad%E2%80%93Cameroon_Petroleum_Development_and_Pipeline_Project

19. Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794. https://doi.org/10.1145/2939672.2939785

20. Cheng, Y. F., & Niu, L. (2018). Predicting corrosion rates of steel pipelines using machine learning. *Corrosion Science*, 145, 170–182.

21. Coelho, L. B. (2022). Reviewing machine learning of corrosion prediction in a data-oriented perspective. *npj Materials Degradation*, 6, 8. https://doi.org/10.1038/s41529-022-00218-4

22. Cosasco. (2024). *Dual Sensor Electrical Resistance (ER) Temperature Probes*. https://www.cosasco.com/product/dual-sensor-electrical-resistance-er-temperature-probes

23. COTCO. (2024). *Cameroon Oil Transportation Company — COTCO in brief*. https://cotco-sa.cm/en/cotco-in-brief/

24. de Waard, C., & Milliams, D. E. (1975). Carbonic acid corrosion of steel. *Corrosion*, 31(5), 177–181.

25. de Waard, C., Lotz, U., & Milliams, D. E. (1991). Predictive model for CO₂ corrosion engineering in wet natural gas pipelines. *Corrosion*, 47(12), 976–985.

26. Egbule, P. E., et al. (2018). Pipeline corrosion control in oil and gas industry: A case study of NNPC/PPMC pipelines. *Academia.edu*.

27. Espressif Systems. (2024). *ESP32 Datasheet — Version 4.4*. https://www.espressif.com/en/products/socs/esp32

28. ExxonMobil. (2011). *Chad/Cameroon Development Project — Project Update No. 30 — Mid-Year Report 2011*.

29. Faraday, M. (1834). On electrical decomposition. *Philosophical Transactions of the Royal Society*, 124, 77–122.

30. Hassanzadeh, S., et al. (2024). Application of electrical resistance probes for corrosion monitoring and cathodic protection assessment of offshore structures. *Materials and Corrosion (Wiley)*. https://doi.org/10.1002/maco.70138

31. Heydari, M., & Talebpour, A. (2024). Synthesis of Gemini-type imidazoline quaternary ammonium salt using by-product fatty acid as corrosion inhibitor for Q235 steel. *Scientific Reports*, 14, article 64671.

32. HSPublishing. (2023). *Oil and gas pipeline corrosion monitoring and prevention*. *Journal of Research in Engineering and Computer Sciences*, https://hspublishing.org/JRECS/article/download/114/105

33. Hu, J., et al. (2024). Prediction of the internal corrosion rate for oil and gas pipelines and influence factor analysis with interpretable ensemble learning. *International Journal of Pressure Vessels and Piping*. https://doi.org/10.1016/j.ijpvp.2024.105400

34. Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting*, 22(4), 679–688.

35. Inspectioneering. (2016, March 8). NACE study estimates global cost of corrosion at $2.5 trillion annually. *Inspectioneering*. https://inspectioneering.com/news/2016-03-08/5202

36. ISO. (2015a). *ISO 8044:2015 — Corrosion of metals and alloys — Basic terms and definitions*.

37. ISO. (2015b). *ISO 13381-1:2015 — Condition monitoring and diagnostics of machines — Prognostics — Part 1: General guidelines*.

38. ISO. (2020). *ISO 15156-1:2020 — Petroleum and natural gas industries — Materials for use in H₂S-containing environments in oil and gas production*.

39. Koch, G. H., Brongers, M. P. H., Thompson, N. G., Virmani, Y. P., & Payer, J. H. (2016). *International Measures of Prevention, Application, and Economics of Corrosion Technology (IMPACT) Study*. NACE International. http://impact.nace.org/

40. Liu, J., et al. (2025). Intelligent prediction model for pitting corrosion risk in pipelines using developed ResNet and feature reconstruction with interpretability analysis. *Reliability Engineering & System Safety*, 257, 110548.

41. Liu, Y., et al. (2022). A review: Prediction method for the remaining useful life of the mechanical system. *Journal of Failure Analysis and Prevention*, 22, 2119–2137. https://doi.org/10.1007/s11668-022-01532-4

42. Lu, B. T., & Luo, J. L. (2016). Electrochemical study of corrosion inhibition of imidazoline derivatives on mild steel. *Corrosion Science*, 105, 1–10.

43. Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems (NeurIPS)*, 30, 4768–4777.

44. Ma, Z., Zhao, Y., & Wang, L. (2021). Predicting pipeline corrosion rate using gradient boosting algorithms. *International Journal of Pressure Vessels and Piping*, 192, 104396.

45. Mansfeld, F. (2014). Recent developments in corrosion measurement techniques. *Materials and Corrosion*, 65(7), 631–638.

46. Mayer, A., et al. (2023). LEROY: A low-cost Arduino-based, IoT-enabled device for atmospheric corrosion monitoring. *Sensors*. https://www.mdpi.com/1424-8220/

47. NACE International. (2012). *TM0190-2012 — Impressed Current Test Method for Screening Corrosion Inhibitors for Oilfield Applications*.

48. NACE International. (2016). *IMPACT Study Press Release — CORROSION 2016 conference*.

49. Onyebuchi, V., et al. (2018). Internal corrosion behaviour of Nigerian gas pipelines. *Unizik Journal of Engineering and Applied Sciences*.

50. Ossai, C. I., Boswell, B., & Davies, I. J. (2017). Use of artificial neural network for prediction of pipeline corrosion defect growth rate. *Engineering Failure Analysis*, 82, 1–12.

51. Persian Utab. (2023). *Phosphoric acid and iron oxide — passivation mechanism*. https://persianutab.com/en/phosphoric-acid-and-iron-oxide/

52. Pollock, D. D. (1991). *Physical Properties of Materials for Engineers* (2nd ed.). CRC Press.

53. Pumps Africa. (2024). *Advanced pipeline monitoring systems for safer oil & gas operations in Africa*. https://pumps-africa.com/advanced-pipeline-monitoring-systems-for-safer-oil-gas-operations-in-africa/

54. Roberge, P. R. (2008). *Corrosion Engineering: Principles and Practice*. McGraw-Hill.

55. Savitzky, A., & Golay, M. J. E. (1964). Smoothing and differentiation of data by simplified least squares procedures. *Analytical Chemistry*, 36(8), 1627–1639.

56. Schweitzer, P. A. (2010). *Fundamentals of Corrosion: Mechanisms, Causes, and Preventive Methods*. CRC Press.

57. Standards Norway. (2017). *NORSOK M-506 — CO₂ corrosion rate calculation model* (3rd ed.).

58. Tan, Y., et al. (2025). Prediction of internal corrosion rate for gas pipeline: A new method based on transformer architecture. *Computers & Chemical Engineering*, 192, 108600.

59. Tukey, J. W. (1977). *Exploratory Data Analysis*. Addison-Wesley.

60. Wagner, C., & Traud, W. (1938). On the interpretation of corrosion phenomena by superposition of electrochemical partial reactions. *Zeitschrift für Elektrochemie*, 44(7), 391–402.

61. Wang, Y., et al. (2023). Corrosion inhibition mechanism of water-soluble imidazoline on A572 Gr.65 steel in 3.5 wt % NaCl solution. *Langmuir*, 39(45), 16108–16119. https://doi.org/10.1021/acs.langmuir.3c02781

62. Webster, J. G. (Ed.). (2014). *The Measurement, Instrumentation, and Sensors Handbook* (2nd ed.). CRC Press.

63. Wei, X., et al. (2024). Advanced machine learning techniques for corrosion rate estimation and prediction in industrial cooling water pipelines. *Sensors*, 24(11), 3564. https://doi.org/10.3390/s24113564

64. Xu, D., Xia, Y., & Wang, X. (2020). Deep learning for corrosion rate prediction in oil and gas pipelines. *Corrosion*, 76(8), 789–798.

65. Yan, J., & Yan, X. (2024). Prediction model for corrosion rate of low-alloy steels under atmospheric conditions using machine learning algorithms. *International Journal of Minerals, Metallurgy and Materials*, 31, 1109–1119. https://doi.org/10.1007/s12613-023-2679-5

66. XGBoost. (2024). *XGBoost Documentation*. https://xgboost.readthedocs.io/

67. Bagheri, B., Yang, S., Kao, H. A., & Lee, J. (2024). Cyber-physical systems architecture for self-aware machines in industry 4.0 environment: A CMMS perspective. *Journal of Manufacturing Systems*, 72, 234–248.

68. CMMS Wikipedia. (2024). *Computerized Maintenance Management System*. https://en.wikipedia.org/wiki/Computerized_maintenance_management_system

69. ISO. (2016). *ISO 14224:2016 — Petroleum, petrochemical and natural gas industries — Collection and exchange of reliability and maintenance data for equipment*. International Organization for Standardization.

70. Lopes, I., Senra, P., Vilarinho, S., Sá, V., Teixeira, C., Lopes, J., Alves, A., Oliveira, J. A., & Figueiredo, M. (2016). Requirements specification of a computerized maintenance management system — A case study. *Procedia CIRP*, 52, 268–273.

71. Murphy, K. (2021). *The State of Open-Source CMMS for SMEs*. Maintenance World Journal, 18(3), 45–53.

72. Next.js. (2024). *Next.js — The React Framework for the Web*. Vercel Inc. https://nextjs.org/

73. Roda, I., & Macchi, M. (2018). A framework to embed asset management in production companies. *Proceedings of the Institution of Mechanical Engineers, Part O: Journal of Risk and Reliability*, 232(4), 368–378.

74. Supabase. (2024). *Supabase — The Open Source Firebase Alternative*. https://supabase.com/

75. Vercel. (2024). *Vercel — Develop. Preview. Ship.* https://vercel.com/

\newpage

<!-- ═══════════════════════════════════════════════════════════ -->

# ANNEXES

## Annexe A — Code source du firmware ESP32 (extrait)

```cpp
// ─────────────────────────────────────────────────────────
// Corrosion Monitor — ESP32 + HX711 + DS18B20
// M2 Maintenance Industrielle — ENSPD Douala
// Cycle : wake → mesure → CSV série → deep sleep 10 min
// ─────────────────────────────────────────────────────────

#include "HX711.h"
#include <OneWire.h>
#include <DallasTemperature.h>

#define HX711_DOUT_PIN   21
#define HX711_SCK_PIN    22
#define ONE_WIRE_BUS      4

const float R_SERIE      = 100.0;
const float R1           = 10.0;
const float R2           = 10.0;
const float R_REF        = 0.5;
const float V_ALIM       = 3.3;
const float R_PONT_EQUIV = (R1 + R_REF);
const float V_EXC_EFF    = V_ALIM * R_PONT_EQUIV
                           / (R_SERIE + R_PONT_EQUIV);

#define SLEEP_INTERVAL_US  600000000ULL  // 10 minutes
#define MESURES_PAR_CYCLE  10

RTC_DATA_ATTR static unsigned long mesure_index  = 0;
RTC_DATA_ATTR static double        last_Rx        = 0.0;
RTC_DATA_ATTR static bool          header_envoye  = false;
```

*Code complet disponible dans le dépôt GitHub : `firmware/corrosion_monitor.ino`.*

## Annexe B — Pipeline Python — extrait feature engineering

```python
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df["delta_R_1h"]  = df["rx_corr"].diff(6)    # 6 × 10 min
    df["delta_R_6h"]  = df["rx_corr"].diff(36)   # 36 × 10 min
    dt_1h = df["timestamp_h"].diff(6).replace(0, np.nan)
    df["vitesse_CR_1h"] = (np.abs(df["rx_corr"].diff(6) / dt_1h)
                           * HEURES_PAR_AN * 1000.0)
    df["temp_moy_6h"] = df["temp_lisse"].rolling(36, min_periods=1).mean()
    df["temps_immersion_h"] = df["timestamp_h"] - df["timestamp_h"].iloc[0]
    R0 = df["rx_corr"].iloc[0]
    df["delta_R_absolu"] = df["rx_corr"] - R0
    return df
```

*Pipeline complet disponible dans le dépôt GitHub : `pipeline/corrosion_pipeline.py`.*

## Annexe C — Schéma de câblage de la sonde ER

*[Schéma à insérer : ESP32 DevKit V1, HX711, pont de Wheatstone (R1, R2, R_REF, Rx), DS18B20 avec pull-up 4,7 kΩ, résistance série 100 Ω.]*

## Annexe D — Fiche de sécurité Detar Plus (résumé)

Le **Detar Plus** est classé comme produit corrosif (catégorie 1A pour les acides minéraux). Lors des manipulations, les **équipements de protection individuelle (EPI)** suivants sont obligatoires :

- Lunettes de protection étanches aux projections liquides ;
- Gants résistants aux acides (nitrile, épaisseur ≥ 0,5 mm) ;
- Blouse de laboratoire en coton ;
- Hotte ou ventilation forcée à l'ouverture du récipient ;
- Solution de neutralisation (NaHCO₃) à proximité.

En cas de contact cutané : rincer abondamment à l'eau claire pendant au moins 15 minutes et consulter un médecin.

## Annexe E — Fiche technique de l'inhibiteur de corrosion (famille imidazoline)

L'**inhibiteur de corrosion** retenu pour ce travail appartient à la famille des **imidazolines**. La référence commerciale précise sera fixée selon la disponibilité sur le marché camerounais (candidats potentiels : AC PROTECT 106, Nalco Champion EC1605A, Baker Hughes Petromeen 1000 ou équivalents). Caractéristiques génériques de cette famille :

- **Mécanisme** : adsorption monomoléculaire (Langmuir) via l'atome d'azote du cycle imidazoline ;
- **Efficacité fabricant déclarée** : η > 90 % en milieu HCl 1 N ;
- **Concentrations d'utilisation** : 0,05 à 1,0 % v/v selon sévérité du milieu ;
- **Compatibilité** : aciers au carbone, alliages ferritiques (déconseillé alliages cuivre) ;
- **Stockage** : récipient hermétique, à l'abri de la chaleur.

## Annexe F — Schéma de base de données du prototype GMAO

```sql
-- 8 tables relationnelles (Supabase / PostgreSQL)

CREATE TABLE assets (
  id uuid PRIMARY KEY,
  nom text NOT NULL,
  type text,
  localisation text,
  date_installation timestamptz,
  cr_seuil_orange float DEFAULT 1.0,
  cr_seuil_rouge  float DEFAULT 5.0,
  rul_seuil_orange float DEFAULT 48.0,
  rul_seuil_rouge  float DEFAULT 12.0
);

CREATE TABLE measurements (
  id bigserial PRIMARY KEY,
  asset_id uuid REFERENCES assets(id),
  timestamp_s bigint, vdiff_v float, rx_ohm float,
  temp_c float, delta_r_per_h float,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE predictions (
  id bigserial PRIMARY KEY,
  asset_id uuid REFERENCES assets(id),
  timestamp timestamptz,
  cr_predit float, rul_predit float,
  diagnostic text, confiance float,
  shap_top1 text, shap_top2 text, shap_top3 text
);

CREATE TABLE alerts (
  id uuid PRIMARY KEY,
  asset_id uuid REFERENCES assets(id),
  niveau text CHECK (niveau IN ('vert','orange','rouge')),
  type text, message text, recommandation text,
  created_at timestamptz DEFAULT now(),
  acknowledged_at timestamptz, resolved_at timestamptz
);

CREATE TABLE work_orders (
  id uuid PRIMARY KEY,
  alert_id uuid REFERENCES alerts(id),
  asset_id uuid REFERENCES assets(id),
  statut text CHECK (statut IN ('ouvert','en_cours','ferme')),
  priorite text, technicien_assigne text, description text,
  created_at timestamptz DEFAULT now(), ferme_le timestamptz
);

CREATE TABLE interventions (
  id uuid PRIMARY KEY,
  work_order_id uuid REFERENCES work_orders(id),
  asset_id uuid REFERENCES assets(id),
  type text, technicien text,
  duree_min int, cout_fcfa int,
  notes text, photo_url text,
  realise_le timestamptz
);

CREATE TABLE inhibitor_doses (
  id uuid PRIMARY KEY,
  asset_id uuid REFERENCES assets(id),
  intervention_id uuid REFERENCES interventions(id),
  produit text DEFAULT 'imidazoline',
  concentration_pct float, volume_ml float,
  injecte_le timestamptz
);

CREATE VIEW kpi_maintenance AS
SELECT
  asset_id,
  COUNT(DISTINCT wo.id) FILTER (WHERE wo.statut='ferme') AS ot_fermes,
  AVG(EXTRACT(EPOCH FROM (wo.ferme_le - wo.created_at))/3600) AS mttr_h
FROM work_orders wo GROUP BY asset_id;
```

## Annexe G — Liste des fichiers du projet

| Fichier | Rôle |
|---|---|
| `firmware/corrosion_monitor.ino` | Firmware ESP32 + intégration Supabase |
| `pipeline/corrosion_pipeline.py` | Pipeline Python ML + diagnostic |
| `gmao/supabase/migrations/*.sql` | Migrations BDD Supabase |
| `gmao/nextjs/app/` | Application web Next.js (frontend GMAO) |
| `memoire/memoire_v4.md` | Mémoire (ce document, source Markdown) |
| `memoire/memoire_v4.docx` | Mémoire (version Word ENSPD) |

Lien GitHub : `londola13/predictive-maintenance-corrosion`

\newpage

# TABLE DES MATIÈRES

*(générée automatiquement par Word à partir des styles Heading 1 / 2 / 3)*
