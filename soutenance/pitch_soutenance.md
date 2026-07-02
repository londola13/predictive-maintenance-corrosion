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
| 6 | Méthodologie | 0:45 | 5:00 |
| 7 | OS1 — Sonde | 1:00 | 6:00 |
| 8 | OS2 — Modèle | 0:45 | 6:45 |
| 9 | XGBoost, comment il apprend | 0:45 | 7:30 |
| 10 | D'où vient le +0,29 | 0:45 | 8:15 |
| 11 | Résultats OS2 | 1:15 | 9:30 |
| 12 | OS3 — Température | 1:00 | 10:30 |
| 13 | Physique | 0:45 | 11:15 |
| 14 | OS4 — GMAO | 1:00 | 12:15 |
| 15 | Jumeau | 1:15 | 13:30 |
| 16 | Limites | 0:45 | 14:15 |
| 17 | Apports | 0:45 | 15:00 |
| 18 + 19 | Conclusion + Merci | 1:15 | 16:15* |

\* Prévoir une marge : viser 14 min 30 de parole pour rester sous 15-16.

---

## 1 · TITRE *(0:30)*
Monsieur le Président, Messieurs les membres du jury, bonjour. Merci d'être présents. Je m'appelle Ricky Parfait BATOUMBI IKOND, et je vais vous présenter mon travail de Master 2. Son titre : « Maintenance prédictive de la corrosion, une transition Industrie 3.0 vers 4.0 par sonde connectée et apprentissage automatique ». Il a été encadré par Monsieur FEZEU, sous la supervision du Docteur TCHAWE.

## 2 · PLAN *(0:30)*
Je vais suivre six temps. Le contexte et la problématique, d'abord. Puis mes objectifs et ma démarche. Ensuite la méthodologie, les résultats, une discussion. Et je terminerai par la conclusion et les perspectives.

## 3 · CONTEXTE *(1:00)*
Commençons par le contexte. La corrosion coûte environ 2 500 milliards de dollars par an dans le monde. Près de 3,4 % du PIB. Et dans le pétrole, c'est la première cause de dégradation des pipelines. Mon cas d'étude, c'est le pipeline Tchad-Cameroun, exploité par la COTCO : plus de mille kilomètres d'acier en milieu agressif.

Mais voici le point clé. Le verrou n'est plus l'instrumentation. Un opérateur comme COTCO a déjà ses sondes à résistance électrique, et il trace ses interventions. Ce qui lui manque, c'est l'intelligence par-dessus : corréler la résistance, la température et le temps, prédire le taux de corrosion et la durée de vie, puis relier tout ça à l'action. C'est exactement la transition 3.0 vers 4.0 que je propose. Et à coût maîtrisé.

## 4 · PROBLÉMATIQUE *(1:00)*
Le paradoxe est là : des données riches, mais sous-exploitées. Trois manques, concrètement. Aucune corrélation entre les courbes et les variables de procédé. Aucune estimation de la durée de vie restante. Et une boucle qui n'est pas prédictive : les historiques existent, mais rien ne relie la prédiction à l'action.

D'où ma question centrale. Dans quelle mesure un système intégré, une sonde ER instrumentée, un modèle XGBoost qui prédit corrosion et durée de vie en run-to-failure, et une boucle décision-action, permet-il d'opérer cette transition, transposable à la fois à COTCO et aux PME industrielles africaines ?

## 5 · OBJECTIFS *(1:15)*
Pour y répondre, quatre objectifs, calés sur la chaîne de la norme ISO 13381-1 : détection, pronostic, diagnostic, décision, action.

Le premier, OS1, c'est concevoir et valider la sonde ER : un montage 2 fils, un amplificateur HX711 24 bits, un microcontrôleur ESP32, en mesure continue toutes les 30 secondes.

Le deuxième, entraîner un modèle XGBoost du taux de corrosion, validé en leave-one-run-out et interprété par SHAP.

Le troisième, diagnostiquer les régimes de corrosion et identifier ce qui fait la fiabilité de la prédiction.

Et le quatrième, fermer la boucle décision-action, avec un module de maintenance maison transposable à un logiciel open-source.

## 6 · MÉTHODOLOGIE *(0:45)*
La méthode forme une chaîne, du capteur à l'ordre de travail. Le capteur, c'est le fil de fer, le HX711 et la sonde de température, pilotés par l'ESP32. Toutes les 30 secondes, il envoie ses mesures vers une base Supabase. Un pipeline Python prend le relais : il nettoie, compense la température, entraîne XGBoost, produit l'analyse SHAP. Le diagnostic des régimes déclenche des alertes graduées, vert, orange, rouge. Et chaque alerte génère un ordre de travail, toute seule.

## 7 · OS1 — SONDE *(1:00)*
Le premier objectif, donc : la sonde. Le principe est simple. Quand un fil se corrode, sa section diminue et sa résistance augmente, R égale rho L sur pi r carré.

J'ai retenu un montage 2 fils à injection de courant, lu en différentiel par le HX711. J'avais d'abord tenté un pont de Wheatstone. Il n'a pas tenu : couplé au HX711, le signal utile se noyait dans le bruit. Je l'ai abandonné, et c'est un résultat en soi. Le reste est justifié : 970 ohms, pour un courant faible qui n'échauffe pas le fil, mais une tension encore lisible. Et la température, mesurée par un DS18B20 protégé.

## 8 · OS2 — MODÈLE *(0:45)*
Deuxième objectif : le modèle. Pourquoi XGBoost, et pas un réseau de neurones ? Parce que chaque essai me donne un à deux milliers de points, mais que j'ai peu d'essais. Beaucoup de points, peu de runs. Là-dessus, un réseau de neurones sur-apprend. XGBoost, lui, des arbres boostés, est taillé pour le tabulaire à faible volume. Et il est interprétable par SHAP.

Reste deux questions : comment il apprend, et comment on le note. Les deux slides suivantes y répondent.

## 9 · XGBOOST, COMMENT IL APPREND *(0:45)*
Concrètement, comment ça marche ? Le premier arbre fait une prédiction grossière. On regarde ses erreurs. Le deuxième arbre n'apprend pas les données : il apprend ces erreurs-là. Puis un troisième, sur ce qui reste. Et ainsi de suite, cinq cents fois, avec des arbres peu profonds et des corrections minuscules. La prédiction finale, c'est la somme de toutes ces petites corrections. Voilà le gradient boosting.

## 10 · D'OÙ VIENT LE +0,29 *(0:45)*
Et ce +0,29, d'où sort-il ? De deux plis. Premier pli : je cache le Run 12, j'entraîne sur tout le reste, et je le prédis. R² : +0,50. Deuxième pli : même chose avec le Run 16. R² : +0,07. La moyenne des deux donne +0,29. Le point essentiel, c'est que dans chaque pli, l'essai testé n'a jamais été vu à l'entraînement. Ce chiffre note la généralisation, pas la mémorisation.

## 11 · RÉSULTATS OS2 *(1:15)*, temps fort
Et voilà le résultat le plus important du travail. En leave-one-run-out, le R² moyen atteint +0,29, et il bat les méthodes de référence. Mais ce chiffre, je ne l'ai pas eu d'emblée. C'est une trajectoire.

Au début, sur la seule série à 30 degrés, sans couvrir les conditions, le modèle s'effondrait : moins 1,77. En ajoutant des essais qui couvrent et répètent les conditions, je suis remonté à +0,29.

Ce qui compte, ce n'est donc pas la valeur du R². C'est sa structure. Il est positif quand les conditions sont couvertes et répétées, négatif sinon. Autrement dit : ce n'est pas le volume de données qui fait la fiabilité, c'est la répétabilité.

Et j'assume une nuance. Ajouter une morphologie différente le ramène vers +0,20. La métrique reste bruitée, j'ai encore peu d'essais. Cette lecture-là, on la trouve rarement dans la littérature. C'est, pour moi, la contribution centrale du travail.

## 12 · OS3 — TEMPÉRATURE *(1:00)*
Troisième objectif : comprendre ce qui gouverne cette fiabilité. La variable dominante, c'est la température. Loi d'Arrhenius : la vitesse de corrosion grimpe exponentiellement avec elle.

Deux essais ont résisté au modèle, et chacun m'a isolé un facteur. Le Run 15 : une régulation qui dérivait, de 31 à 28 degrés. Le Run 17 : un acide qui avait perdu de sa concentration, le HCl s'étant évaporé avant l'immersion. La leçon tient en une phrase. Il faut maîtriser tous les facteurs en même temps, pas seulement la température.

## 13 · PHYSIQUE *(0:45)*
J'ai aussi voulu comprendre la physique de la rupture. L'emballement final n'est pas une accélération chimique. C'est une divergence géométrique. La section varie en r carré, donc la résistance s'emballe en 1 sur r cube. Voilà pourquoi la rupture mécanique tombe pile au début de l'emballement : « section qui tend vers zéro », c'est à la fois la résistance qui explose et le fil qui lâche. Après la rupture, l'électrolyte continue de conduire un peu. Ce bout de signal n'est plus métallique ; je l'écarte de l'apprentissage.

## 14 · OS4 — GMAO *(1:00)*
Quatrième objectif : fermer la boucle, de la prédiction à l'action. Un constat, d'abord : aucun logiciel de GMAO open-source ne donne d'API exploitable en version gratuite. J'ai donc écrit mon propre module. À chaque alerte, il génère un ordre de travail complet, avec le taux de corrosion, la durée de vie, le régime, la section perdue. Et il le trace, sans le moindre appel externe. Les indicateurs MTBF, MTTR, disponibilité se calculent sur l'historique. Coût de licence : zéro. Donc à portée d'une PME africaine. Et le mécanisme reste transposable à un outil open-source.

## 15 · JUMEAU *(1:15)*, temps fort (honnêteté)
En perspective, j'ai exploré un jumeau numérique. Calibré sur les essais réels, il produit une bande de durée de vie prédite. C'est l'un des trois estimateurs que je confronte en temps réel.

J'ai fait deux tests « prédire, puis confirmer ». Et j'ai choisi de vous montrer les deux, même le raté. Le Run 21 : annoncé dans la bande avant l'essai, il a rompu à 13,1 heures, dans la bande. Le Run 22, lui, a rompu à 11,95 heures, sous la bande. C'est l'essai le plus rapide de toute la campagne.

Ce raté ne casse pas la démarche. Il en trace la limite. Le jumeau interpole entre les morphologies qu'il a vues, il n'extrapole pas au-delà. La leçon : ce qui rend prédictible, c'est de répéter une même morphologie, pas d'accumuler des essais.

## 16 · LIMITES *(0:45)*
J'assume les limites de cette preuve de concept. Le fil de fer n'est pas l'acier API 5L des pipelines : les valeurs absolues de corrosion ne se transposent pas telles quelles. En HCl concentré, l'électrolyte court-circuite un peu la mesure, d'où le fil fin. Le jeu de données est encore mince, les métriques bruitées. Et une seule plage de température est bien couverte. Rien de tout cela n'est intrinsèque à la méthode. Ce sont les conditions du passage à l'échelle.

## 17 · APPORTS *(0:45)*
Je retiens quatre apports. Le premier est méthodologique : la fiabilité d'un modèle se lit dans la structure de son R². Le deuxième, une chaîne complète et bon marché, de la mesure à l'ordre de travail, avec des composants qu'on trouve sur place. Le troisième, une double transposabilité : un saut surtout logiciel chez COTCO, un déploiement autonome pour les PME. Le dernier, la rigueur : chaque donnée, chaque seuil, chaque décision renvoie à une source.

## 18 · CONCLUSION *(1:00)*
Pour conclure. OS1, la chaîne d'acquisition fonctionne, elle a suivi des essais complets jusqu'à la rupture. OS2, XGBoost prédit la corrosion et bat les références, à condition que les conditions soient couvertes. OS3, la température domine, et c'est la répétabilité qui fait la fiabilité. OS4, la boucle décision-action est démontrée, par un module maison à coût nul.

Les objectifs sont partiellement atteints, en cours de consolidation. Mais l'essentiel est là : un prototype qui va de la mesure à la décision, transposable des deux côtés, et une lecture claire des conditions sous lesquelles la maintenance prédictive de la corrosion devient fiable.

## 19 · MERCI *(0:15)*
Je vous remercie de votre attention. Je reste à votre disposition pour vos questions.

---

## Questions probables du jury, réponses prêtes

« Pourquoi du fil de fer et pas de l'acier de pipeline ? »
> C'est une preuve de concept : elle valide la chaîne et la méthode, pas les valeurs absolues. Le fil de fer en HCl corrode vite, quelques dizaines d'heures au lieu de plusieurs mois, ce qui me donne des courbes run-to-failure complètes. La transposition à l'acier API 5L, ce sera l'objet du stage.

« Votre R² de 0,29 est faible. »
> En valeur absolue, oui, et je l'assume. Mais ma validation est inter-essais, le leave-one-run-out, bien plus exigeante que les R² supérieurs à 0,96 de la littérature, obtenus eux en validation intra-jeu. Et surtout, mon résultat n'est pas la valeur, c'est sa structure : positif quand les conditions sont couvertes et répétées. C'est là qu'est l'apport.

« L'objectif RMSE inférieur à 15 % est-il atteint ? »
> Pas encore de façon stabilisée. C'était un objectif de conception fixé a priori, pas une exigence normative. Le faible nombre d'essais rend les métriques bruitées ; leur consolidation est en cours.

« Le Run 22 manqué, n'est-ce pas un échec du jumeau ? »
> Non. C'est un résultat honnête, et instructif. Le jumeau interpole entre les morphologies qu'il a observées, il n'extrapole pas. Le Run 22, le plus rapide de la campagne, tombe sous l'enveloppe des donneurs. Cela délimite précisément le domaine de validité, et confirme qu'il faut répéter chaque morphologie.

« Pourquoi pas GLPI directement ? »
> Parce qu'aucun CMMS open-source n'expose d'API en version gratuite déployable dans ce cadre. Le module maison évite cette dépendance et garantit une démonstration de bout en bout. Son mapping est générique : le jour où une instance est hébergée, il se reporte directement sur GLPI.
