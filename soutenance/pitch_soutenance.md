# Pitch de soutenance, 15 minutes
Maintenance prédictive de la corrosion · BATOUMBI IKOND Ricky Parfait · ESTL La Salle

> Débit cible ≈ 135 mots/min. Regarder le jury, pas les slides. Marquer une pause après chaque chiffre clé.

| # | Slide | Durée | Cumul |
|---|---|---|---|
| 1 | Titre | 0:30 | 0:30 |
| 2 | Plan | 0:30 | 1:00 |
| 3 | Contexte | 1:00 | 2:00 |
| 4 | Problématique | 1:00 | 3:00 |
| 5 | Objectifs | 1:15 | 4:15 |
| 6 | Méthodologie | 1:00 | 5:15 |
| 7 | OS1 — Sonde | 1:00 | 6:15 |
| 8 | OS2 — Modèle | 1:00 | 7:15 |
| 9 | Résultats OS2 | 1:30 | 8:45 |
| 10 | OS3 — Température | 1:00 | 9:45 |
| 11 | Physique | 1:00 | 10:45 |
| 12 | OS4 — GMAO | 1:00 | 11:45 |
| 13 | Jumeau | 1:15 | 13:00 |
| 14 | Limites | 1:00 | 14:00 |
| 15 | Apports | 0:45 | 14:45 |
| 16 + 17 | Conclusion + Merci | 1:15 | 16:00* |

\* Prévoir une marge : viser 14 min de parole pour rester sous 15.

---

## 1 · TITRE *(0:30)*
Monsieur le Président, Messieurs les membres du jury, bonjour. Je vous remercie de votre présence. Je suis Ricky Parfait BATOUMBI IKOND, et je vais vous présenter mon travail de Master 2 : « Maintenance prédictive de la corrosion, une transition Industrie 3.0 vers 4.0 par sonde connectée et apprentissage automatique », réalisé sous l'encadrement de Monsieur FEZEU et la supervision du Docteur TCHAWE.

## 2 · PLAN *(0:30)*
Mon exposé suivra six temps : le contexte et la problématique ; mes objectifs et ma démarche ; la méthodologie ; les résultats ; une discussion de leurs apports et de leurs limites ; et enfin la conclusion et les perspectives.

## 3 · CONTEXTE *(1:00)*
La corrosion représente environ 2 500 milliards de dollars par an à l'échelle mondiale, près de 3,4 % du PIB. Dans le secteur pétrolier, elle est la première cause de dégradation des pipelines. Mon cas d'étude est le pipeline Tchad-Cameroun, exploité par la COTCO : plus de mille kilomètres d'acier en milieu agressif.

Mais voici le point central : le verrou n'est plus l'instrumentation. Les opérateurs comme COTCO disposent déjà de sondes à résistance électrique, et tracent leurs interventions. Ce qui manque, c'est l'intelligence applicative : corréler résistance, température et temps, prédire le taux de corrosion et la durée de vie, et relier ces prédictions à l'action. C'est exactement la transition Industrie 3.0 vers 4.0 que je propose d'opérer, à coût maîtrisé.

## 4 · PROBLÉMATIQUE *(1:00)*
Ce paradoxe, des données riches mais sous-exploitées, se décline en trois manques : pas de corrélation algorithmique entre les courbes et les variables de procédé ; pas d'estimation de la durée de vie résiduelle ; et une boucle non prédictive, les historiques existent, mais la prédiction n'y est pas reliée pour déclencher l'action.

D'où ma question centrale : *dans quelle mesure un système intégré, sonde ER instrumentée, modèle XGBoost prédisant le taux de corrosion et la durée de vie en protocole run-to-failure, et boucle décision → action, permet-il d'opérer cette transition, de façon transposable aussi bien à COTCO qu'aux PME industrielles africaines ?*

## 5 · OBJECTIFS *(1:15)*
Pour y répondre, j'ai structuré le travail en quatre objectifs, calqués sur la chaîne de la norme ISO 13381-1 : détection, pronostic, diagnostic, décision, action.

- OS1, concevoir et valider la sonde ER : montage 2 fils, amplificateur HX711 24 bits, microcontrôleur ESP32, en acquisition continue toutes les 30 secondes.
- OS2, entraîner un modèle XGBoost prédisant le taux de corrosion, validé par une procédure exigeante dite *leave-one-run-out*, et interprété par analyse SHAP.
- OS3, diagnostiquer les régimes de corrosion et identifier les facteurs qui conditionnent la fiabilité de la prédiction.
- OS4, structurer la boucle décision → action par un module de gestion de maintenance maison, transposable à un logiciel open-source.

## 6 · MÉTHODOLOGIE *(1:00)*
La méthodologie forme une chaîne complète, du capteur à l'ordre de travail. Le capteur, sonde en fil de fer, HX711, sonde de température DS18B20, est piloté par l'ESP32, qui envoie les mesures toutes les 30 secondes vers une base de données Supabase. Un pipeline Python les nettoie, applique une compensation thermique, puis entraîne le modèle XGBoost et conduit l'analyse SHAP. Le diagnostic des régimes alimente un système d'alertes graduées, vert, orange, rouge, et chaque alerte génère automatiquement un ordre de travail.

## 7 · OS1, SONDE *(1:00)*
Premier objectif : la sonde. Le principe est simple, la résistance d'un fil croît quand la corrosion réduit sa section, selon R = ρL / πr².

J'ai retenu un montage 2 fils à injection de courant, avec lecture différentielle par le HX711. J'avais d'abord essayé un pont de Wheatstone, mais le mode commun de l'amplificateur noyait le signal utile dans le bruit, je l'ai donc abandonné, et c'est un résultat en soi. Les valeurs sont justifiées : 970 ohms pour un courant faible qui évite l'échauffement, tout en gardant une tension lisible. La chaîne est étalonnée par substitution sur résistances étalons, et la température est mesurée par un DS18B20 protégé.

## 8 · OS2, MODÈLE *(1:00)*
Deuxième objectif : le modèle. Pourquoi XGBoost, et pas un réseau de neurones ? Parce que chaque essai me donne un à deux milliers de points, mais que j'ai peu d'essais : beaucoup de points, peu de runs. Dans cette configuration, les réseaux de neurones sur-apprennent. XGBoost, des arbres de décision boostés, est optimal sur données tabulaires à faible volume, et surtout interprétable par SHAP.

Point crucial : la validation. J'utilise le *leave-one-run-out* : je retire un essai entier de l'entraînement, et je le prédis avec les autres. Je mesure ainsi la vraie généralisation à un essai jamais vu, bien plus exigeant qu'une validation classique.

## 9 · RÉSULTATS OS2 *(1:30)*, temps fort
Et voici le résultat le plus important de ce travail. Le R² moyen en *leave-one-run-out* atteint +0,29, et bat les méthodes de référence. Mais ce chiffre n'a pas été obtenu d'emblée : c'est une trajectoire.

Au départ, entraîné sur la seule série à 30 degrés, sans couvrir les conditions, le modèle échouait lourdement, R² de moins 1,77. En ajoutant des essais qui couvrent et répètent les conditions, je suis remonté à +0,29.

L'apport méthodologique n'est donc pas la *valeur* du R², mais sa structure : il est positif là où les conditions de l'essai testé sont couvertes et répétées, et négatif sinon. Ce n'est pas le volume brut de données qui compte, mais la répétabilité des conditions.

Et j'assume une nuance : ajouter un essai d'une *morphologie différente* ramène le score vers +0,20, la métrique reste bruitée, car j'ai encore peu d'essais. Cette lecture, rarement explicitée dans la littérature, est selon moi la contribution centrale du travail.

## 10 · OS3, TEMPÉRATURE *(1:00)*
Troisième objectif : comprendre ce qui gouverne cette fiabilité. La température est la variable dominante, conformément à la loi d'Arrhenius, la vitesse de corrosion croît exponentiellement avec elle.

Deux essais se sont révélés imprédictibles, et chacun a isolé un facteur. Le Run 15 : une régulation thermique qui dérivait de 31 à 28 degrés. Le Run 17 : un acide dont la concentration avait baissé, le HCl s'étant évaporé avant immersion. La leçon est claire : la fiabilité exige le contrôle simultané de tous les facteurs, pas seulement la température.

## 11 · PHYSIQUE *(1:00)*
Au-delà des chiffres, j'ai tenu à comprendre la physique de la rupture. L'emballement final n'est pas une accélération chimique, mais une divergence géométrique : la section varie en r², donc la résistance s'emballe en 1 sur r³. C'est pourquoi la rupture mécanique coïncide exactement avec le début de l'emballement, « section qui tend vers zéro » signifie à la fois explosion de la résistance et perte de tenue. Après la rupture, une conduction résiduelle par l'électrolyte maintient un signal : cette portion est électrolytique, non métallique, et je l'exclus donc de l'apprentissage.

## 12 · OS4, GMAO *(1:00)*
Quatrième objectif : fermer la boucle, de la prédiction à l'action. Constat pratique : aucun logiciel de GMAO open-source n'offre d'API exploitable en version gratuite. J'ai donc développé un module GMAO maison : à chaque alerte, un ordre de travail enrichi, taux de corrosion, durée de vie, régime, section perdue, est généré et tracé automatiquement, sans aucun appel externe. Les indicateurs MTBF, MTTR, disponibilité sont calculés sur l'historique. Le tout à coût de licence nul, donc accessible aux PME africaines, et le même mécanisme est transposable à un logiciel open-source.

## 13 · JUMEAU *(1:15)*, temps fort (honnêteté)
En perspective, j'ai exploré un jumeau numérique : calibré sur les essais réels, il génère une bande prédictive de durée de vie, l'un des trois estimateurs que je confronte en temps réel.

J'ai mené deux tests « prédire puis confirmer », à l'issue volontairement contrastée. Le Run 21 : annoncé dans la bande *avant* l'essai, il a rompu à 13,1 heures, dans la bande. Le Run 22, en revanche, a rompu à 11,95 heures, *en deçà* de la bande : c'est l'essai le plus rapide de toute la campagne.

Ce « manqué » n'infirme pas la démarche, il en délimite le domaine. Le jumeau interpole entre les morphologies déjà observées, mais il n'extrapole pas au-delà. La leçon : la prédictibilité tient à la répétition au sein d'une même morphologie, pas au simple nombre d'essais.

## 14 · LIMITES *(1:00)*
J'assume pleinement les limites de cette preuve de concept. Le matériau, le fil de fer, n'est pas l'acier API 5L des pipelines : les valeurs absolues de taux de corrosion ne sont pas directement transposables. En milieu HCl concentré, l'électrolyte court-circuite partiellement la mesure, ce qui impose un fil fin. Le jeu de données reste réduit, donc les métriques sont bruitées et en cours de consolidation. Et une seule plage de température est aujourd'hui bien couverte. Mais ces limites ne sont pas intrinsèques à la méthode : elles définissent les conditions du passage à l'échelle.

## 15 · APPORTS *(0:45)*
Quatre apports à retenir. Un apport méthodologique : la fiabilité d'un modèle se lit dans la *structure* de son R². Une chaîne complète et low-cost, de la mesure à l'ordre de travail, en composants accessibles localement. Une double transposabilité : un saut surtout logiciel chez COTCO, un déploiement autonome pour les PME. Et une exigence de rigueur : chaque donnée, chaque seuil, chaque décision est adossé à une source.

## 16 · CONCLUSION *(1:00)*
En conclusion. OS1 : la chaîne d'acquisition est fonctionnelle et a suivi des essais complets jusqu'à la rupture. OS2 : XGBoost prédit le taux de corrosion et bat les références, sous condition de couverture. OS3 : la température domine, et la répétabilité des conditions fait la fiabilité. OS4 : la boucle décision → action est démontrée par un module GMAO maison, à coût nul.

Les objectifs sont partiellement atteints et en voie de consolidation. Mais l'essentiel est là : un prototype doublement transposable, de la mesure à la décision, et une lecture méthodologique des conditions sous lesquelles la maintenance prédictive de la corrosion devient fiable.

## 17 · MERCI *(0:15)*
Je vous remercie de votre attention, et je suis à votre disposition pour vos questions.

---

## Questions probables du jury, réponses prêtes

« Pourquoi du fil de fer et pas de l'acier de pipeline ? »
> C'est une preuve de concept qui valide la *chaîne et la méthode*, pas les valeurs absolues. Le fil de fer en HCl donne une corrosion accélérée (essais de 10-20 h au lieu de mois), idéale pour générer des courbes run-to-failure complètes. La transposition à l'acier API 5L est l'objet du stage à venir.

« Votre R² de 0,29 est faible. »
> En valeur absolue oui, et je l'assume. Mais ma validation est *inter-essais* (leave-one-run-out), bien plus exigeante que les R² > 0,96 de la littérature, obtenus en validation intra-jeu. Surtout, mon résultat n'est pas la valeur mais sa structure : positif quand les conditions sont couvertes et répétées. C'est ça l'apport.

« L'objectif RMSE < 15 % est-il atteint ? »
> Pas encore de façon stabilisée, c'était un objectif de conception fixé a priori, pas une exigence normative. Le faible nombre d'essais rend les métriques bruitées ; leur consolidation est en cours.

« Le Run 22 manqué, n'est-ce pas un échec du jumeau ? »
> Non, c'est un résultat honnête et instructif. Le jumeau interpole entre les morphologies observées, il n'extrapole pas. Le Run 22, le plus rapide de la campagne, tombe sous l'enveloppe des donneurs. Cela délimite précisément le domaine de validité et confirme le besoin de répéter chaque morphologie.

« Pourquoi pas GLPI directement ? »
> Aucun CMMS open-source n'expose d'API en version gratuite déployable dans ce cadre. Le module maison évite cette dépendance et garantit une démonstration de bout en bout ; son mapping est défini de façon générique, donc directement reportable sur GLPI le jour où une instance est hébergée.
