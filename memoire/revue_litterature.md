# REVUE DE LITTÉRATURE

*Système de maintenance prédictive de la corrosion par apprentissage automatique :
conception d'une sonde ER low-cost, acquisition IoT
et prédiction du taux de corrosion par XGBoost*

**Mémoire de Master 2 — ENSPD Douala**
Maintenance Industrielle — Corrosion/Érosion Oil & Gas

---

# PARTIE 1 — LA CORROSION : PHÉNOMÈNE, ENJEUX ET RÉPONSES INDUSTRIELLES

## 1.1  Mécanismes électrochimiques fondamentaux

La corrosion des métaux est un phénomène naturel et irréversible par lequel un matériau métallique tend à retourner à son état thermodynamiquement stable, c'est-à-dire à l'état oxydé sous lequel il se trouve naturellement dans la croûte terrestre. Le fer, par exemple, existe à l'état naturel sous forme d'hématite (Fe₂O₃) ou de magnétite (Fe₃O₄). La transformation de ce minerai en acier par métallurgie constitue un apport d'énergie que la corrosion vient progressivement dissiper.

La définition normative de référence est celle de la norme ISO 8044 : « la corrosion est une interaction physico-chimique entre un métal et son environnement qui entraîne des modifications des propriétés du métal et qui peut conduire à une dégradation significative de la fonction du métal, de l'environnement ou du système technique dont ils font partie. »

### 1.1.1  Nature électrochimique de la corrosion

Dans un milieu électrolytique (solution aqueuse, sol humide, condensat), la corrosion procède par un mécanisme de pile galvanique dans lequel deux réactions électrochimiques couplées se produisent simultanément à la surface du métal.

Réaction anodique — oxydation (dissolution du métal) :

> `Fe  →  Fe²⁺  +  2e⁻`

Le métal cède des électrons et des ions métalliques passent en solution. C'est la zone anodique qui se corrode.

Réaction cathodique — réduction (consommation des électrons) :

En milieu acide (pH < 4), réduction des protons :

> `2H⁺  +  2e⁻  →  H₂ ↑`

En milieu neutre ou légèrement acide, réduction de l'oxygène dissous :

> `O₂  +  2H₂O  +  4e⁻  →  4OH⁻`

Ces deux réactions ne peuvent pas exister l'une sans l'autre : les électrons produits à l'anode doivent obligatoirement être consommés à la cathode. C'est ce couplage qui définit la densité de courant de corrosion (i_corr), paramètre central de toute quantification.

> 📌 *Dans le prototype de laboratoire, l'environnement acide (Detar Plus — détartrant professionnel à base d'acide phosphorique et d'acide chlorhydrique, pH ≈ 0,5–1,5) active simultanément ces deux réactions sur le fil de fer de la sonde ER, avec une cinétique fortement accélérée par rapport aux milieux industriels.*

### 1.1.2  Loi de Faraday — lien entre courant et perte de matière

La loi de Faraday (1834) établit la relation quantitative entre le courant électrique échangé et la masse de métal dissous. Elle constitue le fondement théorique de toutes les méthodes de mesure électrochimiques présentées au Chapitre 2 :

$$m = \frac{M \cdot I \cdot t}{n \cdot F}$$

*Avec :*
- **m** = masse de métal dissous (g)
- **M** = masse molaire du métal — fer : 55,85 g/mol
- **I** = courant de corrosion (A)
- **t** = durée d'exposition (s)
- **n** = nombre d'électrons échangés — 2 pour Fe → Fe²⁺
- **F** = constante de Faraday = 96 485 C/mol

Le taux de corrosion (CR — Corrosion Rate), exprimé en mm/an conformément à la norme ASTM G1, est calculé à partir de la perte de masse par unité de surface et de temps :

$$CR \ (mm/an) = \frac{87{,}6 \cdot \Delta m}{\rho \cdot A \cdot t}$$

*Avec :*
- **Δm** = perte de masse (mg)
- **ρ** = densité du métal (g/cm³) — acier : 7,87 g/cm³
- **A** = aire exposée (cm²)
- **t** = durée d'exposition (heures)
- **87,6** = facteur de conversion dimensionnelle (ASTM G1)

> 📌 *Cette formule est la référence industrielle universelle. Elle sera utilisée dans ce travail pour convertir les variations de résistance électrique mesurées par la sonde ER en taux de corrosion exprimés en mm/an — variable cible du modèle XGBoost.*

### 1.1.3  Potentiel de corrosion et diagrammes de Pourbaix

Tout métal immergé dans un électrolyte adopte spontanément un potentiel mixte (E_corr), dit potentiel de corrosion, résultant de l'équilibre cinétique entre la dissolution anodique et la réduction cathodique. Les diagrammes de Pourbaix (potentiel E en fonction du pH) délimitent les domaines de stabilité thermodynamique d'un métal dans un environnement aqueux en trois zones :

- **Zone de corrosion** : les ions métalliques (Fe²⁺, Fe³⁺) sont stables en solution — le métal se dissout
- **Zone de passivité** : un film d'oxyde protecteur (Fe₂O₃) se forme et ralentit la corrosion
- **Zone d'immunité** : le métal est thermodynamiquement stable — aucune corrosion

> 📌 *Dans le prototype, l'environnement fortement acide du Detar Plus (pH ≈ 0,5–1,5) place le fil de fer dans la zone de corrosion active du diagramme de Pourbaix — ce qui garantit une dissolution rapide et mesurable sur la durée de chaque run expérimental (24–72 heures selon les conditions).*

### 1.1.4  Cinétique de corrosion — équation de Butler-Volmer

La vitesse réelle de corrosion ne dépend pas seulement de la thermodynamique (diagramme de Pourbaix) mais aussi de la cinétique électrochimique, décrite par l'équation de Butler-Volmer :

$$i = i_{corr} \cdot \left[ e^{\frac{\alpha_a \cdot F \cdot \eta}{R \cdot T}} - e^{\frac{-\alpha_c \cdot F \cdot \eta}{R \cdot T}} \right]$$

*Avec :*
- **i** = densité de courant (A/m²)
- **i_corr** = densité de courant de corrosion (A/m²)
- **αa, αc** = coefficients de transfert anodique et cathodique
- **F** = constante de Faraday = 96 485 C/mol
- **η** = surtension = E − E_corr (V)
- **R** = constante des gaz = 8,314 J/mol·K
- **T** = température absolue (K)

En pratique industrielle, cette équation est exploitée par la méthode de polarisation linéaire (LPR) qui permet de mesurer i_corr en temps réel — méthode décrite au Chapitre 2. Elle justifie également l'influence de la température comme facteur aggravant, paramètre directement intégré dans le modèle XGBoost au Chapitre 4.

## 1.2  Classification des formes de corrosion

La corrosion ne se manifeste pas de manière uniforme. Elle prend des formes variées selon la nature du métal, la composition de l'environnement et les conditions mécaniques. La classification internationale de référence est établie par l'AMPP (ex-NACE International) et reprise dans la norme NACE SP0775. Cette classification est essentielle pour tout ingénieur en maintenance : chaque forme de corrosion impose une stratégie de surveillance et une méthode de mesure spécifiques.

| Forme | Mécanisme | Localisation typique | Norme / Référence |
|---|---|---|---|
| Généralisée (uniforme) | Dissolution uniforme sur toute la surface exposée | Pipelines acier au carbone, réservoirs | ASTM G1, NACE SP0775 |
| Par piqûres | Attaque localisée créant des cavités profondes ; film passif percé localement par les ions Cl⁻ | Acier inoxydable en milieu chloruré | ASTM G46, ISO 11463 |
| Galvanique | Couplage électrochimique entre deux métaux de potentiels différents dans un électrolyte | Raccords bimétalliques, structures offshore | ASTM G82, NACE TM0107 |
| Sous contrainte (SCC) | Combinaison d'une contrainte mécanique de traction et d'un environnement corrosif | Tubes sous pression, soudures | NACE TM0177, ISO 7539 |
| Érosion-corrosion | Attaque accélérée par l'écoulement du fluide qui détruit le film protecteur | Coudes, vannes, pompes | ASTM G76, NACE 35100 |
| CO₂ (sweet corrosion) | CO₂ dissous forme H₂CO₃ (acide carbonique) → attaque acide du fer | Pipelines Oil & Gas, têtes de puits | de Waard et Milliams (1975) |
| H₂S (sour corrosion) | H₂S provoque la fragilisation par hydrogène (SSC) et la fissuration (HIC) | Puits à gaz acide, raffineries | NACE MR0175 / ISO 15156 |
| MIC (corrosion microbienne) | Activité de bactéries (SRB, IRB) modifiant les conditions électrochimiques locales | Fonds de réservoirs, conduites enterrées | NACE TM0212 |

Dans le secteur Oil & Gas, les deux formes les plus prévalentes sont la corrosion CO₂ (sweet corrosion) et la corrosion H₂S (sour corrosion). La corrosion CO₂ est régie par le modèle semi-empirique de Waard et Milliams (1975, révisé 1991), qui reste la référence industrielle pour l'estimation du taux de corrosion en fonction de la pression partielle de CO₂ et de la température. Ce modèle sera discuté en détail à la section 1.3.

La corrosion H₂S, régie par la norme NACE MR0175 / ISO 15156, introduit un mécanisme supplémentaire de fragilisation par hydrogène : les atomes H issus de la réaction cathodique pénètrent dans le réseau cristallin de l'acier et provoquent des fissures internes (HIC — Hydrogen Induced Cracking) ou de surface (SSC — Sulfide Stress Cracking). Ces phénomènes ne sont pas mesurables par la sonde ER et nécessitent des contrôles non-destructifs spécifiques (UT, TOFD).

Concernant la MIC (Microbiologically Influenced Corrosion), bien que significative dans les pipelines industriels — notamment dans les fonds de réservoirs où les bactéries sulfato-réductrices (SRB) prospèrent en conditions anaérobies — elle ne sera pas reproduite dans ce prototype. L'environnement de laboratoire (vinaigre + NaCl) ne présente pas les conditions microbiologiques requises. Cette forme de corrosion est mentionnée pour exhaustivité du panorama mais reste hors du périmètre du système de mesure développé.

> 📌 *Le prototype reproduit une corrosion généralisée en milieu acide fort (Detar Plus : H₃PO₄ + HCl, pH ≈ 0,5–1,5). Ce milieu multi-acide crée une cinétique de corrosion complexe et non-monotone — l'HCl attaque agressivement tandis que l'H₃PO₄ tend à former un film de phosphate de fer (FePO₄) partiellement protecteur — ce qui constitue précisément le type de comportement non-linéaire que l'approche par apprentissage automatique (XGBoost) vise à capturer, là où les modèles physiques classiques ne peuvent pas prédire l'interaction entre ces deux mécanismes antagonistes. Cette justification sera développée à la section 3.3.*

## 1.3  Facteurs influents sur le taux de corrosion

Le taux de corrosion n'est pas une constante intrinsèque du matériau : il résulte de l'interaction dynamique entre le métal et son environnement. La maîtrise de ces facteurs est fondamentale à deux titres : d'une part, elle guide la conception de l'environnement corrosif contrôlé du prototype ; d'autre part, ces mêmes facteurs constituent les variables d'entrée (features) du modèle XGBoost développé au Chapitre 4.

### 1.3.1  Température

La température est le facteur cinétique dominant. Son influence sur la vitesse de corrosion suit une loi d'Arrhenius, qui traduit l'accélération des réactions chimiques avec la chaleur :

$$CR \propto e^{\frac{-E_a}{R \cdot T}}$$

*Avec :*
- **Ea** = énergie d'activation (J/mol)
- **R** = constante des gaz = 8,314 J/mol·K
- **T** = température absolue (K)

En pratique industrielle, une règle empirique largement utilisée stipule qu'une augmentation de 10°C double approximativement la vitesse de corrosion. Cette règle est formalisée dans le modèle de Waard et Milliams (1975, révisé 1991) pour la corrosion CO₂ :

$$\log(CR) = 5{,}8 - \frac{1710}{T} + 0{,}67 \cdot \log(pCO_2)$$

*Avec :*
- **CR** = taux de corrosion (mm/an)
- **T** = température absolue (K)
- **pCO₂** = pression partielle de CO₂ (bar)

Ce modèle, bien que semi-empirique et limité aux conditions de pipeline Oil & Gas, reste la référence industrielle pour une première estimation rapide du taux de corrosion. Dans le prototype, la température est maintenue entre 30°C et 55°C à l'aide d'une résistance chauffante d'aquarium, et mesurée en continu par le capteur DS18B20.

### 1.3.2  pH et acidité

Le pH est le paramètre qui quantifie la concentration en ions H⁺ dans la solution. En milieu acide (pH < 7), la réaction cathodique de réduction des protons est favorisée, accélérant la dissolution anodique du métal. En dessous de pH 4, la corrosion du fer devient très agressive car le film d'oxyde protecteur (Fe₂O₃) se dissout. Au-dessus de pH 10, une couche passive stable se forme, inhibant naturellement la corrosion.

Dans le contexte Oil & Gas, le pH est directement lié à la teneur en CO₂ et H₂S dissous. Le CO₂ forme de l'acide carbonique (H₂CO₃, pKa₁ = 6,35) et l'H₂S forme de l'acide sulfhydrique (H₂S, pKa₁ = 7,02), tous deux abaissant le pH de l'eau de formation. Dans notre prototype, le Detar Plus concentré (mélange d'acide phosphorique H₃PO₄ et d'acide chlorhydrique HCl) crée un environnement fortement acide mesuré à **pH ≈ 1** par papier pH au début de chaque run. Ce pH est utilisé comme **constante de référence** du run et non comme variable mesurée en continu : l'ajout d'une sonde pH introduirait des courants parasites dans le liquide conducteur (boucle de masse avec le pont de Wheatstone) et complexifierait le montage sans apport significatif, le pH variant peu pendant la durée d'un run (quelques heures à quelques dizaines d'heures).

### 1.3.3  Pression partielle de CO₂ (pCO₂)

Le CO₂ dissous dans l'eau de formation constitue l'agent corrosif principal des pipelines de production pétrolière. Il réagit avec l'eau selon :

> `CO₂  +  H₂O  →  H₂CO₃  →  H⁺  +  HCO₃⁻`

La pression partielle de CO₂ (pCO₂) est définie par la loi de Dalton des pressions partielles : pCO₂ = y_CO₂ × P_totale, où y_CO₂ est la fraction molaire de CO₂ dans la phase gazeuse. La loi de Henry intervient ensuite pour relier cette pression partielle à la concentration de CO₂ dissous dans la phase aqueuse : C_CO₂ = K_H × pCO₂, où K_H est la constante de Henry (mol/L·bar). Selon le modèle de Waard et Milliams, le taux de corrosion est proportionnel à pCO₂^0,67. En pratique industrielle, une pCO₂ supérieure à 0,2 bar est considérée comme corrosive ; au-delà de 0,5 bar, la corrosion est sévère (seuils communément admis dans l'industrie Oil & Gas, repris dans NACE SP0106).

Dans le prototype de laboratoire, la pCO₂ n'est pas un paramètre pertinent : le milieu corrosif (Detar Plus) est un mélange d'acides minéraux (H₃PO₄ + HCl) et non une solution saturée en CO₂. La corrosion dans le prototype est donc pilotée par la concentration en ions H⁺ (pH) et en ions Cl⁻ (agressivité des chlorures), et non par la pCO₂. Ce paramètre est mentionné ici pour exhaustivité du cadre théorique applicable aux pipelines Oil & Gas.

### 1.3.4  Teneur en eau (BSW)

Le BSW (Basic Sediment and Water) désigne la fraction volumique d'eau dans le fluide transporté. L'eau est l'électrolyte indispensable à la corrosion : sans eau libre au contact du métal, les réactions électrochimiques ne peuvent pas se produire. Un BSW élevé augmente la conductivité ionique de la phase aqueuse et accélère les échanges de charges à l'interface métal/électrolyte.

En dessous de 30% BSW, la phase continue est généralement huileuse et le métal est naturellement protégé. Au-delà de 60–70% BSW, la phase aqueuse devient continue et la corrosion s'accélère significativement. Ce paramètre est mesuré en continu dans les installations industrielles par des analyseurs BSW dédiés (capteur capacitif ou micro-ondes).

### 1.3.5  Vitesse d'écoulement et érosion-corrosion

La vitesse du fluide influence la corrosion selon deux mécanismes antagonistes. D'un côté, un débit élevé favorise l'apport d'oxygène et renouvelle l'électrolyte au contact du métal, accélérant la corrosion. De l'autre, en dessous d'une vitesse minimale, les dépôts (boues, cire, sédiments) s'accumulent et créent des piles de concentration locales encore plus agressives.

Au-delà d'une vitesse critique (typiquement 3–5 m/s pour l'acier au carbone), le film protecteur d'oxyde est mécaniquement arraché par le fluide — c'est l'érosion-corrosion. Ce phénomène est particulièrement sévère aux coudes, réductions de section et vannes partiellement ouvertes.

### 1.3.6  Inhibiteurs de corrosion

Les inhibiteurs de corrosion sont des substances chimiques qui, ajoutées en faible concentration dans l'environnement corrosif, réduisent significativement le taux de corrosion. Leur efficacité est quantifiée par le taux d'inhibition η :

$$\eta \ (\%) = \frac{CR_{sans} - CR_{avec}}{CR_{sans}} \times 100$$

*Avec :*
- **CR_sans** = taux de corrosion sans inhibiteur (mm/an)
- **CR_avec** = taux de corrosion avec inhibiteur (mm/an)
- **η** = taux d'inhibition (%) — objectif industriel : η > 90%

Les inhibiteurs se classifient selon leur mécanisme d'action en trois catégories (ASTM G170, NACE TM0374) :

- **Anodiques** : Forment un film passif sur la zone anodique (chromates, nitrites). Très efficaces mais toxiques — usage restreint.
- **Cathodiques** : Précipitent sur les zones cathodiques et limitent la réduction de l'O₂ (sels de zinc, polyphosphates).
- **Mixtes (films adsorbés)** : S'adsorbent sur toute la surface métallique et bloquent simultanément les zones anodiques et cathodiques. Classe dominante en industrie pétrolière (amines, imidazolines, inhibiteurs organiques naturels).

Les inhibiteurs organiques naturels constituent un axe de recherche actif, particulièrement pertinent dans le contexte africain où des ressources végétales locales (extraits d'Azadirachta indica, d'Hibiscus sabdariffa, huiles végétales) ont démontré des propriétés inhibitrices significatives (η > 80%) dans plusieurs études publiées (Okafor et al., 2010 ; Umoren et al., 2013).

Dans ce travail, l'inhibiteur retenu est l'**AC PROTECT 106**, un inhibiteur de corrosion industriel à base d'**imidazoline** et de ses dérivés. Les imidazolines constituent la famille d'inhibiteurs organiques la plus utilisée en industrie pétrolière pour la protection de l'acier en milieu acide chlorhydrique (HCl) : leur mécanisme d'action repose sur l'adsorption d'un film moléculaire dense sur la surface métallique via les doublets d'électrons libres de l'azote de l'hétérocycle, bloquant simultanément les sites anodiques et cathodiques (inhibiteur mixte). Ce mécanisme est identique en milieu Detar Plus dont la composante HCl est le principal agent corrosif. L'efficacité des imidazolines en milieu HCl est largement documentée dans la littérature : η > 90% pour des concentrations de 0,1 à 1% v/v (Bentiss et al., 2000 ; Popova et al., 2003 ; Quraishi et Sharma, 2003). Une propriété clé pour ce travail est le **temps d'adsorption** de l'inhibiteur — le délai entre l'injection et l'établissement du film protecteur (typiquement quelques minutes à quelques dizaines de minutes selon la concentration et la température) — qui sera mesuré directement sur la courbe dR/dt comme indicateur de l'efficacité cinétique de la protection.

> 📌 *La dose d'inhibiteur recommandée constitue l'une des SORTIES du système prédictif. Le modèle XGBoost prédit le taux de corrosion futur et la durée de vie résiduelle (RUL), puis un moteur de règles recommande automatiquement la dose d'AC PROTECT 106 (imidazoline) optimale (0, 1, 2 ou 5 g/L) pour maintenir η > 90% — boucle fermée mesure → prédiction → action de protection.*

### 1.3.7  Synthèse — Facteurs et features XGBoost

Le tableau suivant synthétise les facteurs influents, leur effet sur le taux de corrosion et leur statut dans le modèle de prédiction :

| Facteur | Effet sur CR | Mesuré dans prototype | Feature XGBoost |
|---|---|---|---|
| Température (T) | CR × 2 par +10°C | DS18B20 (continu) | Oui — temp |
| pH / acidité | CR ↑ quand pH ↓ | Papier pH (mesure initiale) — pH ≈ 1, utilisé comme constante | Constante = 1 |
| pCO₂ | CR ∝ pCO₂^0,67 | Non applicable (milieu HCl/H₃PO₄) | Non |
| BSW (teneur en eau) | CR ↑ quand BSW ↑ | Solution 100% aqueuse | Fixe = 100% |
| Vitesse écoulement | CR ↑ (érosion-corrosion) | Non — bac statique | Non |
| Inhibiteur (AC PROTECT 106 (imidazoline)) | CR ↓ si η > 90% | Dose ajoutée manuellement (g/L) | Oui — dose_inhibiteur |
| Résistance sonde ER | R ↑ quand CR ↑ (fil s'amince) | HX711 + pont Wheatstone | Oui — resistance, delta_R |
| Temps depuis immersion | Indicateur d'épuisement de l'acide | Horodatage ESP32 | Oui — temps_immersion |

## 1.4  Coûts et enjeux mondiaux de la corrosion

La corrosion représente l'un des défis économiques les plus coûteux de l'industrie mondiale. L'étude de référence NACE IMPACT (International Measures of Prevention, Application, and Economics of Corrosion Technologies), publiée en 2016, évalue le coût annuel mondial de la corrosion à 2 500 milliards de dollars USD, soit environ 3,4% du PIB mondial. Ce chiffre dépasse le coût combiné des catastrophes naturelles annuelles et illustre l'ampleur du problème.

Dans le secteur Oil & Gas spécifiquement, la corrosion représente entre 25% et 35% de l'ensemble des défaillances de pipelines. Aux États-Unis, la base de données PHMSA (Pipeline and Hazardous Materials Safety Administration) recense annuellement entre 600 et 800 incidents significatifs toutes causes confondues sur les réseaux de pipelines (gaz, liquides dangereux). La corrosion est responsable de 15 à 25% de ces incidents, soit environ 100 à 150 incidents significatifs par an directement attribués à la corrosion interne ou externe. Le coût d'un incident majeur dépasse fréquemment 10 millions USD, incluant les travaux de réparation, la dépollution environnementale et les pertes de production.

L'étude NACE IMPACT souligne également que 25 à 30% de ces coûts seraient évitables par l'application systématique des meilleures pratiques de gestion de la corrosion, parmi lesquelles la surveillance en temps réel et la maintenance prédictive occupent une place centrale. C'est précisément dans cette perspective que s'inscrit le présent travail : démontrer qu'une approche low-cost basée sur l'IoT et le machine learning peut contribuer significativement à la réduction de ces coûts, y compris dans des contextes à ressources limitées tels que l'Afrique subsaharienne.

Dans le contexte camerounais et africain, l'enjeu est particulièrement critique. Les infrastructures pétrolières (COTCO, Perenco, Total Energies Cameroun) opèrent dans des environnements tropicaux humides qui accélèrent la corrosion, avec des températures ambiantes élevées (28–35°C) et une saison des pluies intense favorisant la corrosion atmosphérique et galvanique. L'accès aux systèmes de surveillance industriels certifiés étant coûteux, le développement de solutions locales adaptées constitue un enjeu stratégique de souveraineté technique.

## 1.5  Stratégies de protection contre la corrosion

Face aux mécanismes de corrosion décrits précédemment, l'industrie a développé un ensemble de stratégies de protection complémentaires. La norme NACE SP0169 et les recommandations AMPP classifient ces stratégies en cinq grandes catégories, présentées ici dans une logique allant du plus passif au plus actif.

### 1.5.1  Vue d'ensemble des approches

| Stratégie | Principe | Limitation principale |
|---|---|---|
| Sélection des matériaux | Utiliser des alliages résistants (inox, Inconel, duplex) | Coût très élevé |
| Revêtements et peintures | Barrière physique entre métal et environnement | Passif, vieillissement, discontinuités |
| Protection cathodique (CP) | Forcer le métal en zone d'immunité électrochimique | Infrastructure électrique requise |
| Inhibiteurs de corrosion | Film chimique adsorbé bloquant les réactions | Dosage continu, coût chimiques |
| Contrôle de l'environnement | Dégazage O₂, déshumidification, pH control | Applicable uniquement en circuit fermé |

### 1.5.2  Revêtements et peintures anti-corrosion

Les revêtements constituent la première ligne de défense dans la majorité des infrastructures industrielles. Ils agissent comme une barrière physique empêchant le contact direct entre le métal et l'environnement corrosif. Les principaux types utilisés dans l'industrie pétrolière sont les revêtements époxy (application liquide, norme ISO 12944), le FBE (Fusion Bonded Epoxy, norme CSA Z245.20 / NACE SP0394) pour les pipelines enterrés, et la métallisation par projection thermique de zinc ou d'aluminium (norme ISO 2063) pour les structures offshore.

La limite fondamentale des revêtements est leur caractère passif et non adaptatif : une fois posé, le revêtement ne s'ajuste pas aux variations des conditions opératoires. Toute discontinuité (holiday, défaut d'application, vieillissement) crée un point d'attaque corrosive concentrée, souvent plus sévère que sans revêtement (effet d'anode de petite surface). C'est pourquoi les revêtements sont systématiquement combinés avec la protection cathodique sur les pipelines enterrés.

Cette stratégie étant purement passive et ne générant aucune donnée mesurable par notre système, elle ne sera pas développée davantage dans ce mémoire. Elle constitue néanmoins un prérequis de la conception des pipelines que tout ingénieur en corrosion doit maîtriser.

### 1.5.3  Protection cathodique (CP)

La protection cathodique est l'une des méthodes les plus efficaces et les plus répandues pour protéger les structures métalliques enterrées ou immergées. Son principe repose sur la thermodynamique électrochimique : en abaissant le potentiel du métal à protéger jusqu'à la zone d'immunité du diagramme de Pourbaix, toute dissolution anodique devient thermodynamiquement impossible.

Deux technologies coexistent en industrie (NACE SP0169) :

- **Anode sacrificielle** : Un métal moins noble (zinc, magnésium, aluminium) est connecté électriquement à la structure à protéger. Ce métal, plus anodique, se corrode préférentiellement en protégeant la structure. Avantages : aucune alimentation électrique requise, installation simple. Limitation : durée de vie limitée de l'anode, efficacité décroissante. Normes EN 12473 (principes généraux de la CP), EN 12954 (structures enterrées), NACE SP0387.
- **Courant imposé (ICCP)** : Un courant électrique continu est imposé de l'extérieur via un redresseur et des anodes inertes (platine, MMO). Le potentiel de protection visé est −850 mV/CSE (Electrode au Sulfate de Cuivre) pour l'acier au carbone selon NACE SP0169. Avantages : puissance ajustable, très longue durée de vie. Limitation : infrastructure électrique requise, risque de surprotection (fragilisation par hydrogène).

> 📌 *Dans le prototype, certains runs du protocole expérimental peuvent intégrer une anode sacrificielle en zinc connectée au fil de fer, créant un couple galvanique où le zinc se corrode préférentiellement. Le modèle XGBoost enregistre cette variable protection_cathodique (booléen) et quantifie la réduction de CR associée. L'utilisation de la protection cathodique reste optionnelle dans le protocole, la priorité étant donnée à l'inhibition chimique (AC PROTECT 106 (imidazoline)) comme stratégie de protection évaluée.*

### 1.5.4  Inhibiteurs de corrosion — Application industrielle

La section 1.3.6 a présenté les mécanismes d'action et la classification des inhibiteurs. Cette section se concentre sur leur application industrielle et les enjeux de dosage, directement reliés à la sortie du modèle XGBoost.

En industrie pétrolière, les inhibiteurs sont injectés en continu dans le fluide transporté via des pompes doseuses calibrées. La concentration typique est de l'ordre de 10 à 100 ppm (mg/L). Un sous-dosage entraîne une protection insuffisante (η < 70%), tandis qu'un surdosage est économiquement pénalisant et peut interférer avec les traitements en aval (désémulsification, traitement des eaux). La norme NACE TM0374 définit les protocoles d'évaluation de l'efficacité des inhibiteurs en laboratoire par tests rotatifs (wheel test).

Le défi industriel n'est donc pas seulement de choisir le bon inhibiteur, mais d'ajuster sa dose en temps réel en fonction des conditions opératoires variables (température, débit, BSW). C'est précisément ce problème d'optimisation dynamique que le modèle XGBoost de ce travail vise à résoudre : prédire le taux de corrosion futur et la durée de vie résiduelle (RUL) de l'élément métallique pour recommander la dose d'inhibiteur (AC PROTECT 106 (imidazoline)) minimale garantissant η > 90%.

## 1.6  Cadre normatif applicable

La mesure, la surveillance et la gestion de la corrosion sont encadrées par un ensemble de normes internationales édictées par l'ASTM International, l'AMPP (ex-NACE), l'ISO, l'API et l'ASME. Le tableau suivant présente les normes directement applicables à ce travail :

| Norme | Organisme | Objet |
|---|---|---|
| ASTM G1 | ASTM | Nettoyage et préparation des éprouvettes de corrosion |
| ASTM G31 | ASTM | Essais d'immersion en laboratoire |
| ASTM G46 | ASTM | Inspection et caractérisation de la corrosion par piqûres |
| ASTM G96-90 | ASTM | Surveillance en ligne par méthodes électriques et électrochimiques (ER, LPR) |
| ASTM G170 | ASTM | Évaluation et qualification des inhibiteurs de corrosion |
| NACE SP0775 | AMPP | Préparation et utilisation des coupons de corrosion en industrie |
| NACE TM0169 | AMPP | Évaluation de la corrosion par tests en laboratoire (coupons) |
| NACE TM0374 | AMPP | Évaluation des inhibiteurs par test rotatif (wheel test) |
| NACE MR0175/ISO 15156 | AMPP/ISO | Matériaux pour environnements H₂S (sour service) |
| NACE SP0169 | AMPP | Protection cathodique des pipelines enterrés |
| ISO 8044 | ISO | Vocabulaire de la corrosion |
| ISO 8407 | ISO | Procédures de nettoyage des éprouvettes corrodées |
| API 570 | API | Inspection des systèmes de tuyauterie en service |
| API 580/581 | API | Inspection basée sur le risque (RBI) — méthodologie |
| ASME B31.3 | ASME | Tuyauterie de process — calcul durée de vie résiduelle |

## Conclusion de la Partie 1

Cette première partie a établi les fondements scientifiques et industriels indispensables à la compréhension du système développé dans ce travail. La corrosion est un phénomène électrochimique quantifiable (loi de Faraday, taux de corrosion en mm/an), multiforme (8 types identifiés par la NACE), influencé par des paramètres mesurables (T, pH, pCO₂, dose inhibiteur) et encadré par un corpus normatif international rigoureux.

Les stratégies de protection disponibles — revêtements, protection cathodique, inhibiteurs — sont efficaces mais réactives : elles ne s'adaptent pas dynamiquement aux variations des conditions opératoires. Le défi central que ce travail adresse est précisément ce passage du réactif au prédictif : anticiper l'évolution du taux de corrosion pour recommander automatiquement la dose d'inhibiteur optimale au bon moment. La partie suivante présente les méthodes de mesure qui rendent cette prédiction possible.

---

# PARTIE 2 — MESURE ET SURVEILLANCE DE LA CORROSION EN INDUSTRIE

## 2.1  Classification des méthodes de mesure (ASTM G96)

La norme ASTM G96-90 (Standard Guide for Online Monitoring of Corrosion in Plant Equipment) constitue le référentiel international de classification des méthodes de surveillance de la corrosion. Elle distingue deux axes orthogonaux : le mode d'acquisition (hors-ligne vs en ligne) et le caractère de la mesure (direct vs indirect, destructif vs non-destructif).

| Méthode | Mode | Type | Grandeur mesurée |
|---|---|---|---|
| Gravimétrie (coupons) | Hors-ligne | Destructif / Direct | Perte de masse (mg) |
| LPR | En ligne | Non-destructif / Indirect | Résistance de polarisation Rp (Ω) |
| EIS | En ligne | Non-destructif / Indirect | Impédance complexe Z(ω) |
| Sonde ER | En ligne | Destructif / Direct | Résistance électrique R (Ω) |
| UT épaisseur | Hors-ligne | Non-destructif / Direct | Épaisseur de paroi (mm) |
| PAUT (Phased Array) | Hors-ligne | Non-destructif / Direct | Image 2D/3D de l'épaisseur |
| Guided Wave (GWT) | Hors-ligne* | Non-destructif / Direct | Épaisseur moyenne sur longue portée |

\* Le GWT est principalement utilisé en inspection périodique (hors-ligne). Des installations permanentes de monitoring continu existent (Guided Ultrasonics Ltd) mais restent minoritaires.

## 2.2  Méthodes hors-ligne — Gravimétrie et coupons

La méthode gravimétrique, décrite par les normes ASTM G1 et NACE SP0775, est la technique de référence historique pour la mesure du taux de corrosion. Elle consiste à exposer des éprouvettes métalliques (coupons) de masse et de surface connues dans le fluide corrosif pendant une durée déterminée, puis à mesurer la perte de masse après nettoyage selon le protocole ISO 8407.

Le taux de corrosion est calculé directement par la formule ASTM G1 présentée à la section 1.1.2. Cette méthode présente l'avantage d'une grande simplicité de mise en œuvre et d'un coût minimal. Elle est cependant fondamentalement discontinue : les coupons doivent être retirés pour être pesés, ce qui ne permet pas un suivi en temps réel de l'évolution de la corrosion. Les intervalles de changement de coupons sont typiquement de 30 à 90 jours en industrie, ce qui masque les variations rapides liées aux changements de conditions opératoires.

## 2.3  Méthodes électrochimiques en ligne

### 2.3.1  Polarisation linéaire (LPR)

La polarisation linéaire (LPR — Linear Polarization Resistance) est une méthode électrochimique permettant de mesurer le taux de corrosion instantané en temps réel, sans consommation significative du métal (mesure non-destructive). Elle repose sur la relation de Stern-Geary (1957) :

$$i_{corr} = \frac{B}{R_p}$$

*Avec :*
- **i_corr** = densité de courant de corrosion (A/m²)
- **B** = constante de Stern-Geary (V) — typiquement 0,026 V pour acier en milieu acide
- **Rp** = résistance de polarisation (Ω·m²) — mesurée expérimentalement

En pratique, Rp est mesurée en appliquant une petite perturbation de potentiel (±10–20 mV par rapport à E_corr) et en mesurant le courant résultant. La méthode LPR est très rapide (une mesure en 1–2 minutes) et adaptée à la surveillance continue. Sa principale limitation est qu'elle ne fonctionne qu'en milieu électrolytique conducteur (eau saline, condensat) et donne des résultats peu fiables en présence d'inhibiteurs adsorbés (modification de B).

### 2.3.2  Spectroscopie d'impédance électrochimique (EIS)

La spectroscopie d'impédance électrochimique (EIS — Electrochemical Impedance Spectroscopy) est la méthode électrochimique la plus riche en information. Elle consiste à appliquer une perturbation sinusoïdale de faible amplitude (5–10 mV) sur une large gamme de fréquences (10⁻² à 10⁵ Hz) et à mesurer la réponse en courant. Le rapport tension/courant à chaque fréquence définit l'impédance complexe Z(ω), représentée dans le diagramme de Nyquist ou de Bode.

L'ajustement d'un circuit électrique équivalent (circuit de Randles) aux données expérimentales permet d'extraire la résistance de transfert de charge Rct (liée à i_corr via Stern-Geary), la résistance de la solution Rs, et la capacité de double couche Cdl (indicateur de l'état de surface). L'EIS est la méthode de référence pour l'évaluation des inhibiteurs en laboratoire (ASTM G170) car elle caractérise complètement l'interface métal/électrolyte. Sa complexité et son coût d'équipement la réservent cependant à la recherche et aux laboratoires spécialisés.

## 2.4  Sondes à résistance électrique (ER) — Méthode centrale

### 2.4.1  Principe physique

La méthode de surveillance par résistance électrique (ER — Electrical Resistance) est définie par la norme ASTM G96-90 comme une technique de surveillance en ligne basée sur la mesure de la résistance électrique d'un élément sensible métallique exposé au milieu corrosif. Son principe repose sur la loi de Pouillet :

$$R = \frac{\rho \cdot L}{A}$$

*Avec :*
- **R** = résistance électrique de l'élément sensible (Ω)
- **ρ** = résistivité électrique du métal (Ω·m) — fer : 1,0 × 10⁻⁷ Ω·m
- **L** = longueur de l'élément sensible (m)
- **A** = section transversale de l'élément (m²)

Lorsque l'élément sensible corrode, sa section A diminue (perte de matière) tandis que sa longueur L et sa résistivité ρ restent constantes. Il en résulte une augmentation de la résistance R directement proportionnelle à la perte de matière. Pour un élément filaire de rayon r(t) décroissant avec le temps :

$$r(t) = \sqrt{\frac{\rho \cdot L}{\pi \cdot R(t)}}$$

Le taux de corrosion est alors calculé comme la vitesse de diminution du rayon de l'élément sensible, convertie en mm/an par la relation :

$$CR \ (mm/an) = \frac{r_0 - r(t)}{t} \times 8760$$

*Avec :*
- **r₀** = rayon initial de l'élément sensible (mm)
- **r(t)** = rayon à l'instant t (mm), calculé depuis R(t)
- **t** = durée écoulée (heures)
- **8760** = facteur de conversion heures → années

### 2.4.2  Sondes ER commerciales et chaîne de mesure industrielle

Les principaux fabricants de sondes ER pour l'industrie pétrolière sont Emerson (gamme Roxar), Cormon Ltd, et Metal Samples / Cosasco. (Note : Permasense, parfois confondu avec les sondes ER, fabrique en réalité des capteurs UT permanents à ondes guidées — technologie distincte décrite à la section 2.5.) Ces équipements se déclinent en plusieurs géométries d'éléments sensibles, choisies selon la sensibilité requise et la durée de vie souhaitée :

| Type | Caractéristiques | Application |
|---|---|---|
| Élément fil (wire) | Fil circulaire exposé — haute sensibilité, courte durée de vie | Mesures courte durée, laboratoire |
| Élément tube (tube) | Tube cylindrique — bonne sensibilité, durée de vie moyenne | Production standard |
| Élément flush | Plaquette affleurante — faible sensibilité, très longue durée | Surveillance long terme |
| Élément ruban (strip) | Ruban plat — sensibilité intermédiaire | Applications offshore |

La chaîne de mesure industrielle complète comprend : la sonde ER (élément sensible) → le transmetteur (convertisseur R → signal 4-20 mA ou numérique) → le réseau de terrain (HART, Modbus, WirelessHART) → le système d'historisation (PI Server OSIsoft/AVEVA) → le SCADA ou DCS. Le prix d'une sonde ER industrielle complète varie entre 2 000 et 15 000 USD selon le type et la connectivité.

## 2.5  Méthodes non-destructives (CND)

Les méthodes de contrôle non-destructif (CND) mesurent l'épaisseur résiduelle de paroi sans consommer l'élément sensible. Elles sont complémentaires des sondes ER car elles donnent une mesure absolue de l'état de la structure, là où la sonde ER donne une vitesse de corrosion instantanée.

La mesure d'épaisseur par ultrasons (UT classique, norme ASTM E797) utilise la propagation d'une onde ultrasonore dans le métal et la mesure du temps de retour de l'écho de fond. La précision typique est de ±0,1 mm, suffisante pour détecter des pertes d'épaisseur significatives. La technique PAUT (Phased Array UT) permet une imagerie 2D ou 3D de la corrosion en déplaçant électroniquement le faisceau ultrasonore, offrant une cartographie complète de l'état de la paroi. Le Guided Wave Testing (GWT) propage des ondes guidées sur de longues distances (jusqu'à 100 m) depuis un seul point d'accès, permettant l'inspection de tronçons entiers de pipeline sans excavation.

## 2.6  Synthèse comparative et justification du choix ER

| Méthode | Continu | Low-cost | Précision | Adapté labo DIY |
|---|---|---|---|---|
| Gravimétrie | Non | Oui | Bonne | Oui (référence) |
| LPR | Oui | Non | Bonne | Difficile (potentiostat) |
| EIS | Non | Non | Très bonne | Non (équipement spécialisé) |
| Sonde ER | Oui | Oui* | Moyenne | Oui (fil + Wheatstone) |
| UT classique | Non | Oui | Bonne | Difficile (pulser HV + ADC rapide + couplant) |
| PAUT | Non | Non | Très bonne | Non |
| GWT | Non | Non | Moyenne | Non |

\* Low-cost uniquement pour la version DIY développée dans ce travail. Les sondes ER commerciales coûtent 2 000–15 000 USD.

La sonde ER est la seule méthode combinant surveillance continue, mesure directe du taux de corrosion et transposabilité en laboratoire à faible coût. La gravimétrie sera utilisée en parallèle comme méthode de référence pour valider les mesures de la sonde DIY : les coupons exposés dans le même bac permettront de vérifier la cohérence entre la perte de masse mesurée et le CR calculé depuis la résistance électrique.

---

# PARTIE 3 — DE LA SONDE ER INDUSTRIELLE AU PROTOTYPE DE LABORATOIRE

## 3.1  Analogie composant par composant

L'objectif de cette partie est de démontrer que le prototype développé dans ce travail n'est pas un système ad hoc sans référence industrielle, mais une transposition rigoureuse et délibérée d'une chaîne de mesure ER industrielle normalisée (ASTM G96) vers un équivalent de laboratoire low-cost. Chaque composant industriel a son équivalent fonctionnel dans le prototype :

| Fonction | Composant industriel | Équivalent prototype | Principe identique ? |
|---|---|---|---|
| Élément sensible corrodable | Fil/tube acier certifié (Cormon, Emerson) | Fil de fer 1,0 mm | Oui — même loi R=ρL/A |
| Mesure différentielle | Pont de Wheatstone intégré dans transmetteur | Pont de Wheatstone discret (résistances de précision) | Oui — même circuit |
| Amplification signal | Amplificateur de précision (INA128, AD8221) | **HX711** (ADC 24 bits dédié ponts de Wheatstone, gain 128, CMRR élevé) | Supérieur — conçu nativement pour cette application |
| Limitation courant / anti-Joule | Alimentation continue régulée | Résistance série 100 Ω sur E+ — limite le courant à ~31 mA et supprime l'échauffement par effet Joule sur le fil | Amélioration — biais thermique éliminé passivement |
| Traitement numérique | Microprocesseur embarqué dans transmetteur | ESP32 (dual-core, WiFi + Bluetooth) | Oui — même fonction |
| Communication | HART 4-20 mA, WirelessHART, Modbus | HTTP/REST via WiFi 802.11 | Équivalent — protocoles différents |
| Historisation | PI Server OSIsoft (historien industriel) | Supabase (PostgreSQL cloud) | Équivalent — stockage temporel |
| Visualisation | SCADA/DCS (Wonderware, Honeywell) | Dashboard Streamlit | Équivalent — affichage temps réel |
| Prédiction / Décision | Absent dans systèmes classiques | XGBoost (contribution originale) | Nouveau — apport de ce travail |

## 3.2  Conception du pont de Wheatstone

Le pont de Wheatstone est un circuit électrique permettant de mesurer avec précision de très faibles variations de résistance en mode différentiel, annulant ainsi le bruit commun (variations de température, bruit d'alimentation). Il est constitué de quatre résistances disposées en carré, avec une source de tension Vs et une mesure de tension différentielle Vout entre les deux branches.

Dans la configuration utilisée, R1 = R2 = R3 = R₀ (résistances fixes de précision, tolérance 1%) et R4 = R_fil (sonde ER, résistance variable). La configuration retenue utilise R1 = R2 = 10 Ω et R_REF = 0,5 Ω (résistances de précision 1%). Le fil de fer de 1,1 m présente une résistance initiale mesurée Rx₀ ≈ 0,13 Ω (déterminée expérimentalement). Le pont n'est donc pas à l'équilibre initial (R_REF ≠ Rx₀) — cela se traduit par un Vdiff non nul à t=0. Ce déséquilibre initial est enregistré comme valeur de référence et les variations relatives ΔR = Rx(t) − Rx₀ constituent la grandeur de surveillance.

L'amplificateur ADC retenu est le **HX711** (24 bits, gain 128), conçu spécifiquement pour les ponts de Wheatstone dans les applications de pesée industrielle. Par rapport à l'ADS1115 (16 bits) initialement envisagé, il apporte une résolution théorique 2⁸ = 256× supérieure et un meilleur CMRR, mieux adapté à la mesure de tensions différentielles de quelques dizaines de microvolt.

Une résistance de **82 Ω** est placée en série entre l'alimentation 3,3 V et la broche E+ du pont. Elle remplit deux fonctions : (1) limiter le courant de circulation dans le fil à ~36 mA, réduisant la puissance dissipée dans le fil (P = I²R_fil ≈ 0,17 mW) à un niveau n'induisant pas d'échauffement mesurable ; (2) protéger le HX711 contre les surtensions. Cette résistance série réduit la tension effective aux bornes du pont à V_eff ≈ 3,3 × 10,5 / 92,5 ≈ 0,37 V — valeur à utiliser dans la formule de calcul de Rx pour obtenir une résistance absolue correcte.

**Note sur l'alimentation du pont** : L'ESP32 entre en deep sleep (consommation < 10 µA) entre deux mesures. À chaque réveil, le HX711 est réinitialisé et effectue 10 lectures moyennées (~2 s), puis l'ESP32 met le HX711 en power-down (SCK HIGH > 60 µs) avant de retourner en deep sleep. Ce cycle assure l'absence totale d'échauffement entre les mesures.

$$V_{out} = V_s \times \left( \frac{R_{fil}}{R_0 + R_{fil}} - \frac{R_0}{2 \cdot R_0} \right)$$

L'HX711 mesure Vout en mode différentiel (AIN0 - AIN1) avec un gain PGA de ×16, ce qui donne une résolution de 0,0078 mV par bit sur une plage de ±256 mV. Pour un fil de 1,0 mm (R₀ ≈ 0,13 Ω) alimenté sous Vs = 3,3 V, une corrosion de 1% de la section produit un déséquilibre Vout ≈ 0,08 mV, soit ~10 LSB — largement détectable. La mesure séquentielle (pont d'abord, puis pH) évite les courants parasites circulant via le liquide conducteur entre les deux circuits de mesure (boucle de masse).

## 3.3  Environnement corrosif : Detar Plus et justification du choix

### 3.3.1  Nature et composition du milieu corrosif

L'environnement corrosif du prototype est le **Detar Plus**, un détartrant acide professionnel à usage industriel et domestique. Sa Fiche de Données de Sécurité (FDS, document réglementaire obligatoire selon le Règlement CLP/CE n°1272/2008) indique la composition suivante :

- **Acide phosphorique (H₃PO₄)** : 10–30% en masse
- **Acide chlorhydrique (HCl)** : 5–15% en masse
- **Tensioactifs** : < 5% (agents mouillants, non corrosifs en eux-mêmes)
- **Additifs divers** : colorants, parfums (concentrations négligeables)

Le pH de la solution non diluée est compris entre **0,5 et 1,5** selon les lots, mesuré expérimentalement à la sonde pH avant chaque run. La densité est d'environ 1,10–1,15 g/cm³, mesurée par pesée de 100 mL sur balance de précision. Ces deux paramètres (pH initial, densité) constituent la **carte d'identité** de la solution de travail pour chaque run, garantissant la reproductibilité des résultats.

### 3.3.2  Mécanismes de corrosion dans le Detar Plus

Le Detar Plus crée un environnement corrosif **multi-mécanisme**, fondamentalement différent des milieux mono-acide classiques de la littérature. Trois processus électrochimiques coexistent et interagissent :

**Mécanisme 1 — Attaque par l'acide chlorhydrique (HCl)** : L'HCl est un acide fort qui se dissocie totalement en solution (HCl → H⁺ + Cl⁻). La corrosion procède par réduction des protons à la cathode (2H⁺ + 2e⁻ → H₂↑) et dissolution du fer à l'anode (Fe → Fe²⁺ + 2e⁻). Les ions chlorures Cl⁻ jouent un rôle supplémentaire d'agressivité : ils détruisent les films passifs (ASTM G46) et favorisent la corrosion par piqûres. Ce mécanisme est le moteur principal de la perte de matière.

**Mécanisme 2 — Passivation partielle par l'acide phosphorique (H₃PO₄)** : L'acide phosphorique, bien que corrosif en lui-même, forme un film de phosphate de fer (FePO₄ / Fe₃(PO₄)₂) à la surface du métal. Ce film agit comme un **convertisseur de rouille** — principe exploité industriellement dans les traitements de surface phosphatants (norme ISO 9717). Ce film ralentit la corrosion en constituant une barrière partielle entre le métal et l'électrolyte.

**Mécanisme 3 — Compétition dynamique HCl/H₃PO₄** : Les mécanismes 1 et 2 sont **antagonistes** : l'HCl attaque, l'H₃PO₄ protège partiellement. L'équilibre entre ces deux processus évolue dans le temps car l'HCl, acide fort à faible point d'ébullition, s'épuise plus vite que l'H₃PO₄ (par consommation chimique et par dégazage). La cinétique résultante est donc **non-monotone** : forte au début (HCl dominant), ralentissant progressivement (H₃PO₄ dominant après épuisement de l'HCl). Le suivi du pH en continu capture cette transition.

### 3.3.3  Justification du choix pour le machine learning

Le choix d'un milieu corrosif multi-acide n'est pas un compromis — c'est un **avantage méthodologique** pour la démonstration de l'approche par apprentissage automatique :

- **Un milieu mono-acide simple** (vinaigre, HCl pur, NaCl) produit une cinétique de corrosion **monotone et prédictible** par les modèles physiques classiques (loi d'Arrhenius, modèle de de Waard et Milliams). Un tel milieu démontre bien le fonctionnement du capteur, mais l'intérêt du ML y est limité : un modèle physique suffit.

- **Le Detar Plus** produit une cinétique **non-linéaire et non-monotone** résultant de l'interaction entre l'attaque acide (HCl), la passivation partielle (H₃PO₄), et l'épuisement différentiel des acides. Aucun modèle physique analytique ne peut prédire cette évolution sans calibration spécifique au produit. C'est précisément ce type de complexité — données mesurables mais mécanismes intriqués — que XGBoost est conçu pour capturer.

- **Pertinence industrielle** : Les détartrants acides sont largement utilisés en maintenance industrielle (nettoyage de circuits de refroidissement, décapage de soudures, détartrage de tuyauteries). La corrosion accidentelle ou résiduelle post-nettoyage par ces produits est un problème réel en industrie, documenté dans la littérature (Finšgar et Jackson, 2014). Le prototype adresse donc un cas d'usage concret et non un milieu artificiel purement académique.

### 3.3.4  Caractérisation expérimentale de la solution de travail

Avant chaque run expérimental, la solution est caractérisée par les mesures suivantes :

| Paramètre | Méthode de mesure | Valeur attendue |
|---|---|---|
| pH initial | Sonde pH calibrée (tampons pH 4,01 et pH 1,68) | 0,5–1,5 |
| Densité | Pesée de 100 mL sur balance (±0,01 g) | 1,10–1,15 g/cm³ |
| Température initiale | DS18B20 | Ambiante (25–30°C) |
| Volume | Éprouvette graduée | 500 mL (identique tous les runs) |
| Référence produit | Numéro de lot Detar Plus (FDS) | Noté sur le carnet d'expérience |

## 3.4  Protocole expérimental — 4 runs-to-failure

### 3.4.1  Philosophie du protocole : run-to-failure instrumenté

Le protocole adopte une approche de type **run-to-failure** (RTF) : chaque run consiste à immerger un fil de fer neuf dans le Detar Plus et à mesurer en continu sa dégradation jusqu'à la rupture physique (R → ∞, circuit ouvert détecté par l'HX711). Ce paradigme, issu de la maintenance prédictive industrielle (norme ISO 13381-1), produit des courbes de dégradation complètes qui constituent le jeu de données idéal pour l'entraînement de modèles de pronostic : chaque run fournit un historique complet de l'état de santé du composant depuis l'état neuf jusqu'à la défaillance.

Quatre runs sont réalisés dans des conditions différentes, permettant au modèle XGBoost d'apprendre la relation entre les variables environnementales (température, pH, présence d'inhibiteur) et la cinétique de dégradation. Un **fil neuf** est utilisé pour chaque run.

### 3.4.2  Phase de calibration préalable (J0 — Jour 0)

Avant les runs instrumentés, un test rapide de calibration est réalisé avec un court échantillon de fil (10 cm, immergé manuellement) pour estimer la vitesse de corrosion brute dans le Detar Plus concentré et valider le dimensionnement (diamètre de fil, fréquence de mesure). Ce test dure quelques heures et permet d'ajuster, si nécessaire, la fréquence d'échantillonnage.

### 3.4.3  Les 4 runs expérimentaux

| Run | Conditions | Variables modifiées | Durée estimée | Objectif |
|---|---|---|---|---|
| **Run 1** — Baseline | Detar Plus concentré, T ambiante (~28°C), sans inhibiteur | Référence | 24–48 h | Cinétique de corrosion de référence, non protégée |
| **Run 2** — Effet thermique | Detar Plus concentré, T = 45°C (résistance chauffante d'aquarium), sans inhibiteur | Température | 12–24 h | Quantifier l'accélération par effet Arrhenius |
| **Run 3** — Effet inhibiteur | Detar Plus concentré, T ambiante, **AC PROTECT 106 (imidazoline) 2 g/L** | Inhibiteur | 48–72 h | Quantifier η de l'AC PROTECT 106 (imidazoline) en milieu Detar Plus |
| **Run 4** — Combiné (test aveugle) | Detar Plus concentré, T = 45°C, **AC PROTECT 106 (imidazoline) 2 g/L** | T + inhibiteur | 24–48 h | Validation du modèle — XGBoost prédit le RUL et CR à partir des runs 1-3 |

**Durée totale estimée** : 7 à 10 jours, selon la cinétique réelle observée.

**Justification du nombre de runs** : Quatre runs constituent le minimum pour un plan factoriel 2² complet (2 facteurs × 2 niveaux : température basse/haute × inhibiteur absent/présent). Ce plan permet d'estimer l'effet principal de chaque facteur et leur interaction, tout en conservant un run (Run 4) comme jeu de test indépendant pour la validation du modèle.

### 3.4.4  Mesures et fréquence d'acquisition

Les mesures sont effectuées toutes les **10 minutes** (6 mesures/heure, ~144 mesures/jour). Pour un run de 48h, cela produit ~288 points de mesure. Sur l'ensemble des 4 runs, le volume total attendu est de **600 à 1 500 points** selon les durées réelles.

La séquence de mesure à chaque cycle de 10 minutes est la suivante :

1. **Réveil** de l'ESP32 (sortie du mode deep sleep)
2. **Activation MOSFET** : alimentation du pont de Wheatstone pendant ~50 ms
3. **Lecture pont** : HX711 acquiert Vout en mode différentiel (moyenne de 10 échantillons)
4. **Désactivation MOSFET** : pont hors tension (élimination effet Joule)
5. **Pause** 100 ms (dissipation résiduelle, découplage des mesures)
6. **Lecture pH** : HX711 acquiert la tension de la sonde pH
7. **Lecture température** : DS18B20 via bus OneWire
8. **Envoi** des données vers Supabase via WiFi (HTTP POST)
9. **Retour en deep sleep** jusqu'au prochain cycle

Cette séquence de mesure séquentielle (pont puis pH, jamais simultanément) évite les **boucles de masse** : si les deux circuits étaient alimentés en même temps, des courants parasites circuleraient via le liquide conducteur (le Detar Plus étant un excellent électrolyte), faussant les deux mesures.

### 3.4.5  Gravimétrie de validation

À chaque fin de run, le fil est retiré, rincé à l'eau distillée, séché à l'étuve (105°C, 1h, conformément à la norme ISO 8407), et pesé sur une balance de précision (±0,01 g). La perte de masse mesurée est comparée à la perte de masse calculée depuis les variations de résistance : cette **double mesure** (ER + gravimétrie) constitue la validation croisée interne du système de mesure et permet de quantifier l'erreur instrumentale de la sonde DIY.

## 3.5  Limites du prototype par rapport au système industriel

- **Certification** : Le prototype n'est pas certifié ATEX ni IECEx — inutilisable en zone explosive réelle.
- **Pression** : Mesure à pression atmosphérique uniquement. Les pipelines opèrent à 50–200 bar.
- **Environnement** : Detar Plus (HCl + H₃PO₄) ≠ CO₂/H₂S dissous sous pression — le milieu reproduit une corrosion acide accélérée, non les conditions spécifiques d'un pipeline de production. Cette différence est assumée et justifiée à la section 3.3.3 : l'objectif est de démontrer la capacité du ML à capturer une cinétique complexe, pas de reproduire un environnement industriel spécifique.
- **Composition du milieu** : Le Detar Plus est un produit commercial dont la composition exacte (concentrations molaires) n'est pas publiée. La reproductibilité est assurée par la caractérisation expérimentale de chaque lot (pH, densité, référence FDS) et non par la formulation chimique précise — approche pragmatique justifiée par l'usage de méthodes data-driven qui n'exigent pas un modèle physique du milieu.
- **Durée de vie** : Fil de fer 1,0 mm : durée de vie estimée 24–72 heures dans le Detar Plus concentré. Sonde ER industrielle : 1–5 ans. Cette durée courte est volontaire (protocole run-to-failure) et permet d'obtenir des courbes de dégradation complètes.
- **Volume de données** : ~600–1 500 points sur 4 runs, contre des millions de points sur des années en industrie. Le volume est suffisant pour XGBoost sur données tabulaires à faible dimensionnalité (8 features), mais interdit les architectures deep learning (LSTM, Transformer) qui nécessitent > 10 000 points.
- **Résolution ADC** : Le HX711 est un convertisseur **24 bits** dédié aux ponts de Wheatstone — sa résolution est comparable aux convertisseurs industriels de même type, avec un ENOB effectif d'environ 18–20 bits dans les conditions d'utilisation réelles.
- **Redondance** : Pas de capteur de secours ni de watchdog industriel. Une déconnexion WiFi pendant un run crée des lacunes (NaN) gérées nativement par XGBoost.

> 📌 *Ces limites sont assumées et documentées. L'objectif du prototype n'est pas de remplacer un système industriel certifié, mais de démontrer la faisabilité de l'approche ML+IoT pour la maintenance prédictive de la corrosion, avec des moyens accessibles dans un contexte académique. La rigueur méthodologique repose sur la reproductibilité des conditions (caractérisation de chaque lot), la validation croisée ER/gravimétrie, et la transparence des limites.*

---

# PARTIE 4 — MAINTENANCE PRÉDICTIVE ET APPRENTISSAGE AUTOMATIQUE

## 4.1  Évolution des stratégies de maintenance industrielle

La maintenance industrielle a connu une évolution continue depuis les débuts de l'industrialisation, passant d'une approche purement réactive à une approche de plus en plus anticipative. Quatre générations de stratégies se sont successivement développées :

- **Maintenance corrective (1ère génération)** : Intervention après défaillance. Aucun investissement préventif, mais coûts de défaillance élevés et imprévisibles. Toujours pertinente pour les équipements non critiques (norme EN 13306).
- **Maintenance préventive systématique (2ème génération)** : Remplacement des composants à intervalles fixes, indépendamment de leur état réel. Sûre mais économiquement inefficace : on remplace des pièces encore en bon état.
- **Maintenance conditionnelle (3ème génération)** : Intervention déclenchée par le dépassement d'un seuil mesuré (vibration, température, épaisseur). Représente le standard industriel actuel pour les équipements critiques.
- **Maintenance prédictive (4ème génération)** : Prédiction de la défaillance future par modèles mathématiques ou ML, permettant d'intervenir au moment optimal (ni trop tôt, ni trop tard). Objet de ce travail.

## 4.2  Fondements de la maintenance prédictive

### 4.2.1  Pronostic et gestion de la santé des équipements (PHM)

Le Pronostic et Gestion de la Santé (PHM — Prognostics and Health Management) est un cadre méthodologique qui intègre la surveillance en temps réel, le diagnostic de l'état courant et le pronostic de l'état futur d'un équipement pour optimiser les décisions de maintenance (Lee et al., 2014 ; Jardine et al., 2006). Le PHM dépasse la maintenance conditionnelle (3ème génération) en ajoutant une composante prédictive : il ne se contente pas de signaler un seuil dépassé mais estime le temps restant avant la défaillance — la durée de vie résiduelle (RUL — Remaining Useful Life).

Dans le contexte de la corrosion, le PHM se traduit par une chaîne fonctionnelle en trois étapes : (1) l'acquisition de données en continu par des capteurs (sondes ER, température, pH), (2) le traitement et le diagnostic (calcul du taux de corrosion courant, détection d'anomalies), et (3) le pronostic (prédiction de l'évolution du taux de corrosion et estimation du RUL). Ce travail implémente ces trois étapes dans un système intégré.

### 4.2.2  Taxonomie des modèles de pronostic

Les modèles de pronostic se classifient en trois catégories selon la nature de la connaissance mobilisée (Zio, 2012) :

- **Modèles physiques (white-box)** : Basés sur les lois fondamentales de la physique et de la chimie. Pour la corrosion : modèle de Waard et Milliams (CO₂), équation de Butler-Volmer (cinétique), loi d'Arrhenius (température). Avantage : interprétabilité totale, extrapolation possible. Limitation : hypothèses simplificatrices qui dégradent la précision dans les conditions réelles multi-factorielles.
- **Modèles data-driven (black-box)** : Basés uniquement sur l'apprentissage à partir des données mesurées, sans hypothèse physique a priori. Pour la corrosion : réseaux de neurones (ANN), machines à vecteurs de support (SVM), gradient boosting (XGBoost). Avantage : capture des non-linéarités complexes. Limitation : nécessité de données suffisantes, risque de sur-apprentissage, extrapolation incertaine.
- **Modèles hybrides (grey-box)** : Combinent un modèle physique de base avec un correcteur data-driven qui capture les écarts entre le modèle physique et la réalité. Exemple : de Waard et Milliams corrigé par un réseau de neurones. Avantage : meilleure extrapolation que le data-driven pur, meilleure précision que le physique pur. Limitation : complexité de mise en œuvre, nécessite une correspondance explicite avec le modèle physique.

Ce travail adopte une approche data-driven, justifiée par trois arguments. Premièrement, les données sont produites dans un milieu multi-acide commercial (Detar Plus : HCl + H₃PO₄) dont la cinétique non-monotone (attaque HCl vs passivation H₃PO₄) ne peut être prédite par aucun modèle physique analytique existant — un modèle hybride nécessiterait un modèle physique de référence calibré pour ce produit spécifique, qui n'existe pas. Deuxièmement, le volume de données attendu (~600–1 500 points, 8 features) est suffisant pour un modèle de gradient boosting, qui converge empiriquement dès 500 à 1 000 observations sur données tabulaires à faible dimensionnalité (Hastie et al., 2009 ; observation confirmée dans les benchmarks Kaggle). Troisièmement, le protocole de run-to-failure produit des courbes de dégradation complètes avec l'event de défaillance observé, ce qui permet l'entraînement direct d'un modèle de prédiction du RUL — avantage impossible à obtenir avec un milieu à corrosion lente (28 jours) et un seul échantillon.

### 4.2.3  Durée de vie résiduelle (RUL) et inspection basée sur le risque (RBI)

La durée de vie résiduelle (RUL) est le paramètre de sortie fondamental de tout système PHM. Pour un équipement soumis à la corrosion, le RUL est calculé selon la norme ASME B31.3 à partir de l'épaisseur résiduelle et du taux de corrosion. L'inspection basée sur le risque (RBI — API 580/581) utilise le RUL comme entrée pour prioriser les inspections des équipements sous pression dans l'industrie pétrolière. Le risque y est défini comme :

$$Risque = PoF \times CoF$$

La durée de vie résiduelle est calculée par :

$$RUL \ (ans) = \frac{e_{mesuré} - e_{min}}{CR}$$

*Avec :*
- **e_mesuré** = épaisseur de paroi mesurée (mm)
- **e_min** = épaisseur minimale admissible selon ASME B31.3 (mm)
- **CR** = taux de corrosion (mm/an)

Traditionnellement, le CR utilisé dans le calcul du RUL est une valeur historique (moyenne des mesures passées). La contribution de ce travail à la méthodologie RBI est de remplacer ce CR historique par un CR prédit par XGBoost (valeur prospective), permettant un RUL anticipatif qui intègre l'évolution probable des conditions opératoires — un RUL prospectif plutôt que rétrospectif.

## 4.3  Fondements de l'apprentissage automatique supervisé

### 4.3.1  Régression supervisée et fonction de perte

L'apprentissage automatique supervisé consiste à apprendre, à partir d'un jeu de données étiquetées (paires entrée-sortie connues), une fonction f qui, étant donné un vecteur d'entrée x (les features), prédit une sortie ŷ aussi proche que possible de la valeur réelle y. Lorsque la sortie est une variable continue — comme le taux de corrosion en mm/an — on parle de régression. Lorsqu'elle est catégorielle (par exemple : corrosion faible/moyenne/sévère), on parle de classification. Ce travail relève de la régression.

La qualité de la prédiction est mesurée par une fonction de perte L(y, ŷ). Les deux fonctions les plus courantes en régression sont l'erreur quadratique moyenne MSE = (1/n) Σ(yᵢ − ŷᵢ)², qui pénalise fortement les grandes erreurs (effet du carré), et l'erreur absolue moyenne MAE = (1/n) Σ|yᵢ − ŷᵢ|, plus robuste aux valeurs aberrantes et directement interprétable dans les unités de la variable cible (mm/an). Le coefficient de détermination R² = 1 − Σ(yᵢ − ŷᵢ)² / Σ(yᵢ − ȳ)² complète ces métriques en quantifiant la part de variance expliquée par le modèle. Un R² de 0,92 signifie que 92% de la variabilité du taux de corrosion est capturée. Dans ce travail, le triplet (MAE, RMSE, R²) sera systématiquement rapporté.

### 4.3.2  Compromis biais-variance et sur-apprentissage

Le défi fondamental de l'apprentissage supervisé est le compromis biais-variance (Hastie et al., 2009). L'erreur totale de prédiction se décompose en trois termes : le biais (écart systématique dû à un modèle trop simple), la variance (sensibilité aux fluctuations de l'échantillon d'entraînement, due à un modèle trop complexe) et le bruit irréductible (variabilité intrinsèque des mesures).

Le sur-apprentissage (overfitting) survient lorsqu'un modèle mémorise le bruit des données d'entraînement plutôt que la relation sous-jacente. Il se manifeste par une performance excellente sur les données d'entraînement mais médiocre sur les données nouvelles. Dans le contexte de ce prototype, le bruit de mesure provient des fluctuations électroniques de l'HX711, des micro-variations de température ambiante et de l'évaporation partielle de la solution. La régularisation — pénalisation de la complexité du modèle — est le mécanisme principal pour contrôler le sur-apprentissage, point développé en détail dans la section consacrée à XGBoost (4.5.4).

### 4.3.3  Méthodes d'ensemble : du bagging au boosting

Les méthodes d'ensemble améliorent les performances en combinant les prédictions de plusieurs modèles de base, typiquement des arbres de décision. Deux paradigmes fondamentaux structurent ce domaine.

Le bagging (Bootstrap Aggregating, Breiman, 1996) entraîne plusieurs arbres en parallèle sur des sous-échantillons aléatoires des données, puis moyenne leurs prédictions. La forêt aléatoire (Random Forest, Breiman, 2001) étend le bagging en ajoutant une sélection aléatoire des features à chaque nœud, ce qui décorrèle les arbres et réduit la variance globale. Le bagging réduit principalement la variance sans affecter significativement le biais.

Le boosting (Freund et Schapire, 1997 ; Friedman, 2001) entraîne les arbres en séquence : chaque nouvel arbre se concentre spécifiquement sur les erreurs commises par les précédents. Cette construction séquentielle réduit simultanément le biais et la variance, ce qui explique la supériorité systématique du boosting sur le bagging pour les données tabulaires structurées — fait établi par de nombreux benchmarks (Grinsztajn et al., 2022). Le gradient boosting (Friedman, 2001) formalise cette construction itérative comme une descente de gradient dans l'espace fonctionnel, cadre théorique développé en détail à la section 4.5.3.

> 📌 *Le choix entre Random Forest et XGBoost pour ce travail n'est pas arbitraire : la Random Forest est robuste mais ne minimise pas activement le biais résiduel. XGBoost, par sa construction séquentielle corrigeant les erreurs, est mieux adapté à la prédiction précise d'une variable continue (CR en mm/an) à partir de features fortement auto-corrélées temporellement.*

## 4.4  État de l'art — ML appliqué à la corrosion (2015–2024)

L'application du machine learning à la prédiction de la corrosion est un domaine de recherche en croissance rapide. Une revue de la littérature des dix dernières années permet d'identifier les approches dominantes et leurs performances comparatives.

Les premières applications ML à la corrosion ont utilisé les réseaux de neurones artificiels (ANN) pour modéliser la relation non-linéaire entre les paramètres physico-chimiques et le taux de corrosion (Caleyo et al., 2009 ; Ossai et al., 2015). Ces modèles ont démontré une supériorité par rapport aux modèles physiques purs (de Waard et Milliams) en présence de données hétérogènes, mais souffrent d'un manque d'interprétabilité — problème critique pour les ingénieurs de corrosion qui doivent justifier leurs décisions d'inspection.

Les forêts aléatoires (Random Forest) et les machines à vecteurs de support (SVM) ont ensuite été appliquées avec succès à la classification du risque de corrosion et à la prédiction des défaillances de pipelines (Xie et Tian, 2018 ; Almutairi et al., 2020). Ces méthodes offrent une meilleure robustesse face au bruit de mesure, mais leurs performances sur données tabulaires sont généralement inférieures au gradient boosting.

Les modèles LSTM (Long Short-Term Memory) ont été proposés pour exploiter la structure temporelle des séries de mesures de corrosion (Pidaparti et al., 2021). Bien que théoriquement adaptés aux données séquentielles, ils nécessitent un volume de données important (>10 000 points) et présentent une sensibilité élevée aux hyperparamètres, ce qui limite leur applicabilité dans des contextes à données restreintes comme ce prototype.

Le gradient boosting, et particulièrement XGBoost (Chen et Guestrin, 2016), s'est imposé comme la méthode de référence pour la prédiction sur données tabulaires industrielles dans de nombreux benchmarks (Kaggle, études comparatives). Son application à la prédiction de corrosion a été validée par plusieurs études récentes (Li et al., 2022 ; Soomro et al., 2023) qui rapportent des performances supérieures aux ANN et RF sur des jeux de données de taille limitée (<5 000 points).

| Auteurs (année) | Méthode | Données | Cible | Performance |
|---|---|---|---|---|
| Ossai et al., 2015 | ANN (MLP) | Pipeline inspection (ILI) | Profondeur piqûres | R² = 0,84 |
| Xie et Tian, 2018 | RF + SVM | PHMSA pipeline incidents | Classification risque | Accuracy 89% |
| Almutairi et al., 2020 | RF, SVM, ANN | Données terrain Aramco | CR (mm/an) | R² = 0,88 (RF) |
| Pidaparti et al., 2021 | LSTM | Séries temporelles (labo) | CR (mm/an) | MAE = 0,08 mm/an |
| Li et al., 2022 | XGBoost | Pipeline Gas (2 800 pts) | CR (mm/an) | R² = 0,93 |
| Soomro et al., 2023 | XGBoost + SHAP | Offshore (1 500 pts) | CR (mm/an) | R² = 0,92, MAE = 0,04 |
| Ce travail (2026) | XGBoost | Labo DIY (4 000 pts) | CR à 48h (mm/an) | À mesurer |

Ce tableau met en évidence trois tendances : (1) la progression des performances avec l'évolution des méthodes (ANN → RF → XGBoost), (2) la supériorité systématique du gradient boosting sur les données tabulaires de taille limitée, et (3) l'absence quasi-totale de travaux combinant acquisition IoT low-cost et prédiction ML dans une boucle fermée intégrée — gap que ce travail vise à combler.

## 4.5  XGBoost — Fondements et mécanisme de décision

### 4.5.1  L'arbre de décision : brique élémentaire

Tout algorithme de gradient boosting repose sur un modèle de base : l'arbre de décision. Un arbre de décision est une structure hiérarchique de règles binaires appliquées successivement aux variables d'entrée (features) pour aboutir à une prédiction. Chaque nœud interne teste une condition sur une feature (par exemple : delta_R_1h > 0,004 ?) et oriente l'observation vers la branche gauche (condition vraie) ou droite (condition fausse). Les feuilles terminales contiennent la valeur prédite, calculée comme la moyenne des observations d'entraînement qui ont atteint cette feuille.

L'algorithme d'apprentissage d'un arbre cherche, à chaque nœud, le seuil de séparation qui minimise la variance des résidus dans chaque sous-groupe résultant (critère de réduction de variance pour la régression). Ce processus est répété récursivement jusqu'à atteindre une profondeur maximale (max_depth) ou un nombre minimal d'observations par feuille (min_child_weight).

La limitation fondamentale d'un arbre unique réside dans son compromis biais-variance : un arbre peu profond présente un biais élevé (sous-apprentissage — il ne capture pas les nuances des données) ; un arbre très profond présente une variance élevée (sur-apprentissage — il mémorise le bruit de mesure). Le boosting résout ce dilemme en combinant un grand nombre d'arbres peu profonds.

### 4.5.2  Le boosting : correction itérative des erreurs

Le boosting est une méthode d'apprentissage ensembliste qui construit séquentiellement une série d'apprenants faibles (arbres peu profonds), chaque apprenant ciblant spécifiquement les erreurs commises par l'ensemble des apprenants précédents. Formellement, la prédiction finale est une somme pondérée de K arbres :

$$\hat{y} = \sum_{k=1}^{K} \eta \cdot f_k(x)$$

*Avec :*
- **ŷ** = prédiction finale (taux de corrosion en mm/an)
- **fk(x)** = prédiction du k-ième arbre pour l'observation x
- **η** = learning rate — contrôle la contribution de chaque arbre (typiquement 0,05–0,3)
- **K** = nombre total d'arbres (n_estimators, typiquement 100–500)

Le processus d'entraînement procède comme suit. À l'initialisation, la prédiction courante ŷ⁽⁰⁾ est fixée à la moyenne de la variable cible sur l'ensemble d'entraînement. À chaque itération k, le résidu rᵢ = yᵢ − ŷᵢ⁽ᵏ⁻¹⁾ est calculé pour chaque observation. Un nouvel arbre fk est entraîné à prédire ces résidus. La prédiction est ensuite mise à jour : ŷᵢ⁽ᵏ⁾ = ŷᵢ⁽ᵏ⁻¹⁾ + η · fk(xᵢ). L'arbre k ne prédit donc pas le taux de corrosion directement — il prédit l'écart entre la réalité et ce que les arbres précédents ont déjà estimé.

À titre d'illustration sur les données de corrosion : supposons que la prédiction initiale soit ŷ⁽⁰⁾ = 0,16 mm/an (moyenne de la phase de référence). Pour une observation réelle CR = 0,31 mm/an (phase corrosion intense), le résidu est r = +0,15. L'Arbre 1 apprend que lorsque delta_R_1h est élevé et la température dépasse 48°C, le résidu est fortement positif. Il contribue +0,12. L'Arbre 2 capture le résidu résiduel +0,03, et ainsi de suite jusqu'à convergence.

### 4.5.3  Du boosting au gradient boosting

Friedman (2001) a généralisé le boosting en formulant chaque itération comme une étape de descente de gradient dans l'espace fonctionnel. L'idée centrale est que le résidu rᵢ = yᵢ − ŷᵢ est mathématiquement équivalent au gradient négatif de la fonction de perte MSE par rapport à la prédiction courante :

$$r_i = -\frac{\partial L(y_i, \hat{y}_i)}{\partial \hat{y}_i} = y_i - \hat{y}_i \quad \text{(pour L = MSE)}$$

Cette reformulation est décisive car elle permet de substituer la MSE par toute fonction de perte différentiable (MAE, Huber, quantile), chaque choix modifiant la sensibilité du modèle aux valeurs extrêmes. En pratique pour la prédiction du taux de corrosion, la MSE est préférée car elle pénalise davantage les grandes erreurs — une sous-estimation sévère du taux de corrosion étant plus dangereuse qu'une légère surestimation.

### 4.5.4  Apports spécifiques de XGBoost

XGBoost (Chen et Guestrin, 2016) améliore le gradient boosting classique sur trois points fondamentaux qui le rendent particulièrement robuste dans les contextes industriels à données limitées et bruitées.

Premièrement, la fonction objectif intègre un terme de régularisation explicite qui pénalise la complexité de chaque arbre :

$$Obj = \sum_{i}^{n} L(y_i, \hat{y}_i) + \sum_{k}^{K} \Omega(f_k)$$

*Avec :*
- **L(yi, ŷi)** = fonction de perte — MSE : (yi − ŷi)²
- **Ω(fk)** = régularisation : γT + ½λ||w||² (T = nb feuilles, w = poids feuilles)
- **γ** = pénalise le nombre de feuilles — contrôle la complexité structurelle
- **λ** = régularisation L2 sur les poids — réduit la sensibilité au bruit

Le paramètre γ pénalise le nombre de feuilles de chaque arbre : un arbre avec beaucoup de feuilles n'est retenu que si le gain en précision justifie sa complexité. Le paramètre λ applique une régularisation L2 sur les poids des feuilles, évitant que le modèle s'ajuste aux fluctuations parasites du signal de résistance (bruit électronique de l'HX711, variations de connectivité).

Deuxièmement, XGBoost implémente un élagage post-construction (pruning) basé sur un gain seuil. Contrairement au gradient boosting classique qui arrête la croissance de l'arbre dès qu'une division est jugée mauvaise, XGBoost construit l'arbre jusqu'à la profondeur maximale puis élague les branches dont le gain net est inférieur à γ. Cette stratégie globale évite de rejeter des divisions localement mauvaises mais globalement bénéfiques.

Troisièmement, XGBoost gère nativement les valeurs manquantes en apprenant automatiquement, à chaque nœud, dans quelle branche orienter les observations présentant une valeur NaN. Dans le contexte de ce prototype, des interruptions de connectivité WiFi de l'ESP8266 peuvent créer des lacunes dans les séries temporelles. XGBoost apprend que ces lacunes correspondent généralement à un contexte particulier (perte de signal en phase de forte corrosion, par exemple) et traite les NaN de manière cohérente plutôt que de rejeter ces observations.

Ces trois mécanismes combinés confèrent à XGBoost une robustesse particulière dans les contextes à données limitées (<5 000 points) et bruitées, caractéristiques typiques des expérimentations en laboratoire. Chen et Guestrin (2016) ont validé ces propriétés sur 29 benchmarks de compétitions de machine learning, établissant XGBoost comme la méthode de référence pour les données tabulaires industrielles. Cette supériorité a été confirmée dans le domaine de la corrosion par Li et al. (2022) et Soomro et al. (2023), qui rapportent des R² supérieurs à 0,92 sur des jeux de données de moins de 3 000 points, nettement supérieurs aux ANN (R² ~ 0,85) et aux forêts aléatoires (R² ~ 0,88) dans les mêmes conditions.

> 📌 *Dans ce travail, XGBoost est utilisé pour trois tâches complémentaires : (1) prédire le taux de corrosion instantané CR (mm/an) — régression continue, (2) estimer la durée de vie résiduelle RUL (heures) — régression sur données de run-to-failure, et (3) recommander la dose d'AC PROTECT 106 (imidazoline) via un moteur de règles post-modèle (CR < 1 mm/an → aucune action ; 1–5 → 1 g/L ; 5–15 → 2 g/L ; > 15 → 5 g/L + alerte). Les seuils de CR sont adaptés au milieu Detar Plus (corrosion rapide) et non aux seuils pipeline classiques.*

## 4.6  Feature engineering pour séries temporelles de corrosion

La mesure brute de résistance toutes les 10 minutes présente une autocorrélation temporelle : deux mesures consécutives sont proches car la corrosion, même rapide dans le Detar Plus, est un processus continu. Le feature engineering transforme ces données brutes en features porteuses d'information sur la **dynamique** et la **tendance** du phénomène, à plusieurs échelles temporelles :

| Feature | Calcul | Information portée |
|---|---|---|
| R_brute | Résistance mesurée (Ω) | État instantané de dégradation du fil |
| delta_R_1h | R(t) − R(t−6) | Vitesse de corrosion sur la dernière heure |
| delta_R_6h | R(t) − R(t−36) | Tendance à moyen terme (6 heures) |
| vitesse_CR | delta_R_1h convertie en mm/an via R=ρL/A | Taux de corrosion instantané |
| tendance_6h | Pente de régression linéaire sur 36 mesures | Accélération ou décélération de la corrosion |
| temp_liquide | Température DS18B20 (°C) | Facteur cinétique Arrhenius |
| ph_run | pH initial mesuré au papier pH (constante par run) | Condition chimique de référence |
| dose_inhibiteur | Dose AC PROTECT 106 injectée (% v/v) | Variable de contrôle — présence/absence protection |
| inhibiteur_actif | Booléen 0/1 (après détection du temps d'adsorption) | Indique si le film inhibiteur est établi |
| temps_immersion | Heures depuis le début du run | Indicateur de vieillissement / épuisement du milieu |

**Adaptation au protocole multi-run** : Les features delta_R_6h et tendance_6h ne sont pas calculables pour les premières heures de chaque run (pas assez d'historique). Ces valeurs manquantes sont laissées comme NaN et traitées nativement par XGBoost, qui apprend automatiquement dans quelle branche orienter les observations incomplètes (cf. section 4.5.4).

**Justification des échelles temporelles** : L'échelle de 1h capture les événements rapides (dégazage HCl, variation de température), l'échelle de 6h capture les tendances de fond (épuisement progressif de l'acide, croissance du film de phosphate). L'échelle de 24h, utilisée dans le protocole initial à 28 jours, n'est plus pertinente pour des runs de 24-72h et a été supprimée.

## 4.7  Validation temporelle — Walk-forward Cross-Validation

La validation croisée standard (k-fold aléatoire) est inadaptée aux séries temporelles car elle introduit une fuite temporelle (data leakage) : des données futures peuvent se retrouver dans l'ensemble d'entraînement, ce qui biaise artificiellement les métriques à la hausse. Pour les données de corrosion, la méthode appropriée est la walk-forward cross-validation (ou TimeSeriesSplit) :

Dans cette approche, les données sont divisées en N folds chronologiques. À chaque itération k, le modèle est entraîné sur les folds 1 à k et évalué sur le fold k+1 (données strictement futures). La performance finale est la moyenne des métriques sur tous les folds de validation. Cette méthode garantit que le modèle n'a jamais accès à des données futures lors de l'entraînement, ce qui reflète fidèlement les conditions d'utilisation réelle.

## 4.8  Boucle fermée : mesure → prédiction → recommandation

Le système développé dans ce travail implémente une boucle de contrôle prédictive fermée, reliant directement la mesure en temps réel à la recommandation d'action :

1. **Acquisition** : ESP32 + HX711 (résistance, 24-bit) + DS18B20 (température) + sonde pH (séquentiel), mesure toutes les 10 minutes en deep sleep → CSV série → Supabase
2. **Feature engineering** : Pipeline Python calcule les features dérivées (delta_R_1h, delta_R_6h, vitesse_CR, tendance_6h, temps_immersion)
3. **Prédiction double** :
   - **Modèle CR** : XGBoost prédit le taux de corrosion instantané (mm/an)
   - **Modèle RUL** : XGBoost prédit la durée de vie résiduelle (heures avant rupture), entraîné sur les courbes de run-to-failure des runs précédents
4. **Décision** : Moteur de règles basé sur CR et RUL :
   - CR < 1 mm/an ET RUL > 24h → OK, aucune action
   - CR 1–5 mm/an OU RUL 12–24h → AC PROTECT 106 (imidazoline) 1 g/L
   - CR 5–15 mm/an OU RUL 4–12h → AC PROTECT 106 (imidazoline) 2 g/L
   - CR > 15 mm/an OU RUL < 4h → AC PROTECT 106 (imidazoline) 5 g/L + **alerte critique**
5. **Action** : Recommandation affichée sur dashboard Streamlit + alerte optionnelle (notification)
6. **Feedback** : La dose injectée et le temps écoulé deviennent des features pour les prédictions suivantes

> 📌 *Cette boucle fermée constitue l'apport original de ce travail par rapport aux systèmes ER classiques : ceux-ci mesurent et enregistrent, mais ne prédisent pas et ne recommandent pas. L'intégration du ML ferme la boucle entre la surveillance et l'action de maintenance. La double sortie (CR + RUL) donne à l'opérateur à la fois la vitesse de dégradation et le temps restant — les deux informations nécessaires à une décision de maintenance informée.*

## Conclusion de la Partie 4

Cette partie a posé les fondements méthodologiques complets du système prédictif développé dans ce travail. Le cadre PHM (Pronostic et Gestion de la Santé) a structuré la démarche : acquisition → diagnostic → pronostic. La taxonomie des modèles a justifié le choix d'une approche data-driven — choix renforcé par la nature multi-acide du milieu corrosif (Detar Plus), dont la cinétique non-monotone échappe aux modèles physiques classiques.

L'état de l'art a montré une progression claire des performances — des réseaux de neurones (R² ~ 0,84) aux forêts aléatoires (R² ~ 0,88) jusqu'au gradient boosting (R² > 0,92) — tout en révélant l'absence de système intégré combinant mesure IoT low-cost et prédiction ML en boucle fermée. Le mécanisme détaillé de XGBoost (arbre de décision → boosting → gradient → régularisation) a été présenté, suivi du feature engineering temporel adapté au protocole multi-run et de la validation par walk-forward cross-validation, deux étapes indispensables pour éviter le sur-apprentissage. La double sortie du système (CR instantané + RUL) et la recommandation automatique de dose d'inhibiteur (AC PROTECT 106 (imidazoline)) ferment la boucle entre la surveillance passive et la décision de maintenance active.

---

# PARTIE 5 — POSITIONNEMENT ET CONTRIBUTION ORIGINALE

## 5.1  Gaps identifiés dans la littérature

L'analyse de la littérature présentée dans les parties précédentes permet d'identifier trois gaps principaux que ce travail vise à adresser :

- **Gap 1 — Accessibilité des systèmes de surveillance** : Les systèmes de surveillance ER industriels (Cormon, Emerson, Permasense) coûtent entre 2 000 et 15 000 USD par point de mesure, rendant leur déploiement inaccessible aux PME industrielles et aux économies émergentes. Aucune solution low-cost (<100 USD) combinant mesure ER continue et transmission IoT n'a été documentée dans la littérature académique.
- **Gap 2 — Prédiction vs. Surveillance** : La majorité des systèmes ER industriels sont des outils de surveillance : ils mesurent et enregistrent le taux de corrosion passé mais ne prédisent pas son évolution future ni la durée de vie résiduelle. Les travaux ML sur la corrosion utilisent presque exclusivement des données publiques (PHMSA, SPE papers) générées dans des contextes industriels sans accès direct au système de mesure. La boucle mesure → prédiction (CR + RUL) → recommandation d'inhibiteur en temps réel n'est pas documentée à l'échelle d'un prototype fonctionnel complet.
- **Gap 3 — Contexte africain** : La littérature sur la maintenance prédictive de la corrosion dans le contexte des industries extractives africaines (Oil & Gas, mines) est quasi inexistante. Les solutions développées pour les environnements nord-américains ou européens ne prennent pas en compte les contraintes locales : connectivité intermittente, budget limité, disponibilité des pièces, expertise technique restreinte.

## 5.2  Contribution originale de ce travail

Face aux gaps identifiés, ce travail apporte les contributions suivantes :

- **Contribution 1 — Prototype IoT low-cost** : Conception et implémentation d'une chaîne de mesure ER complète (sonde DIY fil de fer + pont de Wheatstone + HX711 + ESP32 + Supabase) pour un coût total de hardware inférieur à 30 000 FCFA (~50 USD), soit un facteur 40 à 300 moins cher qu'un système industriel certifié, tout en conservant le même principe de mesure normalisé (ASTM G96). L'innovation de la mesure pulsée (MOSFET) élimine le biais d'échauffement par effet Joule, amélioration rarement documentée dans les prototypes académiques.
- **Contribution 2 — Intégration ML prédictif avec double sortie** : Premier prototype documenté intégrant une chaîne complète mesure ER → feature engineering temporel → XGBoost → prédiction simultanée du taux de corrosion (CR) et de la durée de vie résiduelle (RUL) → recommandation automatique de dose d'inhibiteur (AC PROTECT 106 (imidazoline)), fermant la boucle entre la surveillance et la décision de maintenance.
- **Contribution 3 — Validation expérimentale par run-to-failure** : Production de données de corrosion réelles en laboratoire (4 runs-to-failure dans un milieu multi-acide commercial) servant à entraîner et valider le modèle XGBoost sur des courbes de dégradation complètes incluant l'event de défaillance. La double validation ER + gravimétrie quantifie l'erreur instrumentale de la sonde DIY.
- **Contribution 4 — Milieu multi-acide comme argument ML** : Démonstration que l'approche data-driven apporte une valeur ajoutée spécifique en milieu à cinétique non-monotone (Detar Plus : HCl attaque / H₃PO₄ passivé) où les modèles physiques classiques ne peuvent pas prédire le comportement sans calibration spécifique.
- **Contribution 5 — Contexte africain** : Démonstration de la faisabilité d'un système de maintenance prédictive de la corrosion avec des composants disponibles sur le marché local camerounais (Jumia, marchés électroniques de Douala) et un produit chimique courant (détartrant domestique), ouvrant la voie à une démocratisation de la surveillance industrielle en Afrique.

## 5.3  Extrapolation industrielle du prototype

Le tableau d'analogie présenté à la section 3.1 permet de tracer directement le chemin de l'industrialisation du prototype. Chaque composant DIY peut être remplacé par son équivalent industriel certifié sans modifier l'architecture logicielle ni les algorithmes ML :

| Composant prototype | Équivalent industriel | Apport de l'industrialisation |
|---|---|---|
| Fil de fer 1,0 mm | Sonde ER Cormon CW-20 (wire element) | Certification ATEX, durée de vie 5 ans |
| HX711 24-bit + Wheatstone + 100Ω série (deep sleep entre mesures) | Transmetteur Emerson Roxar 2600 | Précision ±0,1 μm, sortie HART 4-20 mA |
| ESP32 | Passerelle WirelessHART ou Modbus TCP | Protocoles industriels certifiés |
| Supabase | PI Server OSIsoft/AVEVA | Historien temps réel, conformité ISA-95 |
| Streamlit | SCADA Honeywell Experion ou Aspentech | Interface certifiée SIL2 |
| XGBoost Python | Module ML intégré dans SCADA ou MES | Déploiement en production |

Cette correspondance directe constitue l'argument central de la valeur académique de ce travail : le prototype n'est pas une démonstration isolée, mais un proof-of-concept industriellement transposable, dont chaque composant a été délibérément choisi en référence à son équivalent normalisé.

---

# CONCLUSION DE LA REVUE DE LITTÉRATURE

Cette revue de littérature a établi le cadre théorique, normatif et technique du présent travail en suivant une progression rigoureuse du général au particulier. La corrosion, phénomène électrochimique universel quantifié par la loi de Faraday et encadré par un corpus normatif international (ASTM, NACE, API, ISO), représente un coût annuel de 2 500 milliards USD et demeure le principal mode de défaillance des infrastructures pétrolières.

Parmi les méthodes de surveillance disponibles, la sonde ER (ASTM G96) a été identifiée comme la seule technique combinant mesure continue, mesure directe du taux de corrosion et transposabilité en laboratoire à faible coût. Le prototype développé dans ce travail reproduit fidèlement le principe de la sonde ER industrielle avec des composants low-cost (fil de fer 1,0 mm, pont de Wheatstone à mesure pulsée, HX711, ESP32), dont la correspondance composant par composant avec les systèmes commerciaux a été établie.

Le choix du Detar Plus (mélange HCl + H₃PO₄) comme milieu corrosif, loin d'être un compromis, constitue un argument méthodologique : sa cinétique non-monotone (attaque acide vs passivation phosphatante) crée précisément le type de complexité que les modèles physiques classiques ne peuvent pas capturer et que l'approche data-driven par XGBoost est conçue pour résoudre.

L'apport original de ce travail réside dans l'intégration d'un modèle XGBoost à double sortie (taux de corrosion + durée de vie résiduelle) à cette chaîne de mesure, transformant un outil de surveillance passif en un système de maintenance prédictive actif, capable de recommander automatiquement la dose d'inhibiteur (AC PROTECT 106 (imidazoline)) optimale à partir des mesures en temps réel. Cette boucle fermée mesure → prédiction → recommandation, validée par un protocole de run-to-failure et une double vérification ER/gravimétrie, constitue la contribution centrale de ce mémoire.
