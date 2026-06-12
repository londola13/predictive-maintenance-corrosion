# III.X — Évaluation du modèle prédictif et conditions de son passage à l'échelle

## III.X.1 — Objectif et démarche d'évaluation

L'objectif de cette section est d'évaluer rigoureusement la capacité du modèle d'apprentissage automatique (XGBoost) à remplir les deux fonctions visées : l'estimation du taux de corrosion (CR) et la prédiction de la durée de vie résiduelle (RUL).

Conformément aux bonnes pratiques de l'apprentissage automatique, cette évaluation ne se limite pas à mesurer une performance absolue : elle compare systématiquement le modèle à des **méthodes de référence** (baselines) simples. Cette comparaison est essentielle : un modèle n'a de valeur que s'il surpasse ce qu'une heuristique élémentaire produirait. Trois protocoles complémentaires ont été mis en œuvre :

1. **Validation par essai exclu (*leave-one-run-out*)** : le modèle est entraîné sur tous les essais sauf un, puis évalué sur l'essai écarté. Ce protocole mesure la capacité de **généralisation à une condition expérimentale nouvelle**.
2. **Prévision intra-essai (*forecasting*)** : à partir de l'historique récent d'un essai, le modèle prédit l'état futur (résistance à un horizon d'une heure). Ce protocole reproduit le **cas d'usage industriel réel** : suivre un équipement donné et anticiper sa dégradation.
3. **Comparaison aux baselines** : persistance (l'état futur égale l'état présent) et extrapolation linéaire de la tendance récente.

L'indicateur principal retenu est le coefficient de détermination R², complété par l'erreur absolue moyenne (MAE).

## III.X.2 — Résultats : généralisation entre conditions

Le tableau suivant présente les résultats de la validation par essai exclu pour la prédiction du taux de corrosion.

| Essai de test | R² (XGBoost) |
|---|---|
| Essai 1 (HCl brut) | −1,45 |
| Essai 2 (HCl 1:1) | −9,09 |
| Essai 3 (HCl 2:1) | +0,05 |
| **Moyenne** | **−3,50** |

Les coefficients R² négatifs indiquent que, dans ce protocole, le modèle ne généralise pas à une condition non vue lors de l'entraînement. L'analyse en identifie la cause principale : les trois essais présentent des **vitesses de corrosion très différentes** (l'essai en milieu brut corrode environ neuf fois plus vite que l'essai le plus dilué). Le modèle, entraîné sur des dynamiques lentes, ne peut prédire une dynamique rapide qu'il n'a jamais observée — et réciproquement. À cela s'ajoute le fait que chaque concentration n'est représentée que par **un seul essai**, ce qui empêche le modèle d'apprendre la variabilité propre à chaque condition.

## III.X.3 — Résultats : prévision de la dégradation

Le tableau suivant compare le modèle aux baselines pour la prévision de la résistance à un horizon d'une heure (évaluation sur le dernier tiers de chaque essai, incluant la phase d'emballement).

| Essai | R² XGBoost | R² Persistance | R² Extrapolation linéaire |
|---|---|---|---|
| Essai 1 (brut) | −0,96 | 0,62 | **0,87** |
| Essai 2 (1:1) | −0,98 | 0,75 | **0,77** |
| Essai 3 (2:1) | −0,89 | **0,56** | 0,23 |

Le résultat est sans ambiguïté : les méthodes de référence **égalent ou surpassent** le modèle d'apprentissage automatique. L'extrapolation linéaire, en particulier, atteint un R² de 0,87 là où XGBoost obtient un score négatif.

Cette contre-performance s'explique par une propriété fondamentale des modèles à base d'arbres de décision : ils sont **incapables d'extrapoler au-delà de la plage de valeurs observée à l'entraînement**. Or la résistance du fil croît de façon monotone : la phase finale de chaque essai atteint des valeurs supérieures à toute la phase d'entraînement. Le modèle, plafonnant à la dernière valeur connue, sous-estime systématiquement la dégradation, tandis qu'une simple extrapolation de tendance prolonge naturellement la courbe.

Le recentrage de la cible sur une grandeur bornée (la variation de résistance plutôt que sa valeur absolue) corrige cette anomalie d'extrapolation, mais ne confère toujours pas au modèle d'avantage décisif sur les baselines.

## III.X.4 — Interprétation : les conditions de pertinence de l'apprentissage automatique

Ces résultats, loin d'invalider l'approche, en précisent les **conditions de pertinence**. L'apprentissage automatique n'apporte de valeur que lorsque deux conditions sont réunies :

- **Un volume de données suffisant** pour qu'un modèle statistique surpasse une heuristique simple ;
- **Une complexité multivariée** : des interactions non triviales entre de nombreuses variables, que les méthodes simples ne peuvent capturer.

Le prototype développé dans ce travail ne réunit, par construction, aucune de ces deux conditions : il repose sur un **unique signal** (la résistance électrique) et sur un **nombre restreint d'essais**. Dans ce contexte, la dynamique de dégradation se résume à une tendance régulière, qu'une extrapolation linéaire décrit efficacement. Il est par conséquent attendu — et scientifiquement cohérent — qu'un modèle complexe n'y apporte pas d'avantage.

Ce constat délimite avec précision le périmètre de validité du prototype : **il établit la faisabilité de la chaîne complète d'acquisition et de traitement** — du capteur instrumenté jusqu'à la décision de maintenance — sans prétendre, à cette échelle, démontrer la supériorité du modèle prédictif.

## III.X.5 — Perspective : la montée en valeur à l'échelle industrielle

La portée de ce travail réside dans sa **transposabilité**. Les limites observées ne sont pas intrinsèques à la méthode : elles sont les conséquences directes du contexte expérimental réduit. Elles définissent, en creux, les conditions de la pleine valeur du modèle prédictif à l'échelle industrielle.

Sur une installation réelle — telle qu'une turbine, un compresseur ou une ligne de pipeline instrumentée —, les deux conditions de pertinence sont précisément réunies :

- **Une instrumentation multivariée** : vibration, température, pression, intensité, débit… dont les **interactions non linéaires** portent la signature des modes de défaillance. C'est exactement le type de complexité que l'extrapolation linéaire ne peut traiter et que l'apprentissage automatique est conçu pour exploiter.
- **Un historique massif** : les systèmes de supervision industriels accumulent, sur des années, des volumes de données considérables, offrant au modèle la profondeur statistique qui fait défaut au prototype.

Dans ce cadre, la prédiction de la durée de vie résiduelle devient un problème authentiquement multivarié, où le modèle déploie son avantage : distinguer des signatures de panne, pondérer des variables couplées, anticiper des ruptures par reconnaissance de motifs complexes.

Ainsi, la contribution de ce travail est double et cohérente :

1. **Un prototype fonctionnel** qui valide, de bout en bout, l'architecture d'une chaîne de maintenance prédictive — du capteur instrumenté à la décision, en passant par le cloud et le modèle.
2. **Une évaluation critique et rigoureuse** qui établit les conditions sous lesquelles l'apprentissage automatique apporte une valeur réelle — et qui trace, par là même, la trajectoire de son industrialisation.

Cette démarche — concevoir, mesurer honnêtement, et délimiter le domaine de validité — constitue le cœur de la méthode d'ingénierie appliquée à l'innovation industrielle 4.0.
