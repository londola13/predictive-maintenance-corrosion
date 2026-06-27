# 🔎 Audit de vérification des références — Mémoire corrosion

> Vérification en ligne de **chaque référence** de la bibliographie, pour ta crédibilité devant le jury.
> Date : 2026-06-27.

## Légende
| Symbole | Signification |
|---|---|
| ✅ **Vérifiée** | Trouvée en ligne, **détails corrects** — lien cliquable fourni |
| ✅ **Officiel/classique** | Source bien établie (norme, datasheet, site officiel, article fondateur) — URL canonique fiable |
| ⚠️ **Réelle mais ERREUR** | Le papier existe, mais **auteurs / année / journal / DOI faux** dans le mémoire → **à corriger** |
| ⚠️ **À contrôler** | Pas confirmée individuellement (littérature grise / blog) — vérifier le lien à la main |
| ❌ **INTROUVABLE / INVENTÉE** | Aucune trace en ligne → **probablement fabriquée, à retirer ou remplacer** |

---

## 🚨 À TRAITER EN PRIORITÉ (le jury peut le voir)

### ❌ Probablement INVENTÉES — à retirer/remplacer
| Réf. mémoire | Verdict |
|---|---|
| **Murphy, K. (2021). The State of Open-Source CMMS for SMEs. *Maintenance World Journal*** | ❌ **Aucune trace.** Journal + article introuvables → **INVENTÉE** |
| **Mayer, A., et al. (2023). LEROY: A low-cost Arduino-based… *Sensors*** | ❌ **Introuvable.** Il existe un vrai article corrosion low-cost 2023 (Sensors) mais de **Komary et al.**, pas « Mayer », et pas nommé « LEROY » → **INVENTÉE** |
| **Cheng, Y. F., & Niu, L. (2018). Predicting corrosion rates… *Corrosion Science*, 145** | ❌ **Introuvable** (Y.F. Cheng est un auteur réel, mais ce papier ML 2018 n'existe pas sous cette forme) |
| **Lu, B. T., & Luo, J. L. (2016). …imidazoline derivatives… *Corrosion Science*, 105** | ❌ **Introuvable** (déjà signalée « non citée » dans le texte) |
| **Ma, Z., Zhao, Y., & Wang, L. (2021). …gradient boosting… *IJPVP*, 192, 104396** | ❌ **Introuvable** sous ces auteurs/numéro |
| **Xu, D., Xia, Y., & Wang, X. (2020). Deep learning… *Corrosion*, 76(8)** | ❌ **Introuvable** sous ces auteurs/volume |

### ⚠️ Vrai papier mais AUTEURS / DÉTAILS FAUX — à corriger absolument
| Réf. mémoire | Réalité vérifiée |
|---|---|
| **Yan, J., & Yan, X. (2024)** — corrosion low-alloy steels, *IJMMM* | ✅ Le papier existe ([Springer](https://link.springer.com/article/10.1007/s12613-023-2679-5)) **mais les vrais auteurs sont Kuang, J. & Long, Z.** — pas « Yan & Yan » ! |
| **Heydari, M., & Talebpour, A. (2024)** — imidazoline Q235, *Sci. Reports* | ✅ Le papier existe ([Nature](https://www.nature.com/articles/s41598-024-64671-8)) **mais les vrais auteurs sont Ma, Y., Qi, W., Yu, M. et al.** |
| **Bagheri, B., Yang, S., Kao, H.-A., & Lee, J. (2024). *Journal of Manufacturing Systems*, 72, 234-248** | ⚠️ Le papier (mêmes auteurs/titre) existe **mais c'est 2015, dans *IFAC-PapersOnLine* 48(3), 1622-1627** — pas 2024/J. Manuf. Syst. → [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2405896315005571) |
| **Liu, J., et al. (2025)** — ResNet pitting, *RESS*, 257, 110548 | ⚠️ Existe ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0951832025005484)) **mais vol. 264, art. 111347** (pas 257/110548) et 1ᵉʳ auteur = **Zheng**, pas Liu |
| **Hu, J., et al. (2024)** — IJPVP, …105400 | ✅ Existe ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0308016124002060)) **mais n° d'article ≈ 105329**, pas 105400 |
| **Tan, Y., et al. (2025)** — transformer, *Comp. Chem. Eng.*, 192, 108600 | ✅ Existe ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0098135425000882)) — 1ᵉʳ auteur **Li Tan** (initiale L), volume à revérifier |

---

## ✅ Articles récents VÉRIFIÉS corrects
| Réf. | Lien |
|---|---|
| Wei, X., et al. (2024). *Sensors*, 24(11), 3564 | [mdpi.com/1424-8220/24/11/3564](https://www.mdpi.com/1424-8220/24/11/3564) ✅ DOI exact |
| Hassanzadeh, S., et al. (2024). ER probes offshore, *Materials and Corrosion* | [Wiley 10.1002/maco.70138](https://onlinelibrary.wiley.com/doi/10.1002/maco.70138) ✅ |
| Wang, Y., et al. (2023). imidazoline A572, *Langmuir* | [pubs.acs.org/…langmuir.3c02781](https://pubs.acs.org/doi/10.1021/acs.langmuir.3c02781) ✅ |
| Liu, Y., et al. (2022). RUL review, *J. Fail. Anal. Prev.* | [doi.org/10.1007/s11668-022-01532-4](https://doi.org/10.1007/s11668-022-01532-4) ✅ |
| Coelho, L. B. (2022). ML corrosion review, *npj Mater. Degrad.* | [doi.org/10.1038/s41529-022-00218-4](https://doi.org/10.1038/s41529-022-00218-4) ✅ |

⚠️ **Ossai, C. I., Boswell, B., & Davies, I. J. (2017). ANN pipeline corrosion, *Eng. Failure Analysis*, 82** : auteurs **réels** (publications voisines confirmées en 2015-2016) mais **ce titre/volume 2017 exact non confirmé** — à vérifier.

---

## 📚 Classiques & fondateurs — URL canonique (fiables)
| Réf. | Lien vérifiable |
|---|---|
| Faraday, M. (1834). *Phil. Trans. R. Soc.* | [doi.org/10.1098/rstl.1834.0008](https://doi.org/10.1098/rstl.1834.0008) |
| Wagner, C., & Traud, W. (1938). Électrodes mixtes | [doi.org/10.1149/1.2168253](https://doi.org/10.1149/1.2168253) (réédition trad.) |
| Avrami, M. (1939). *J. Chem. Phys.* | [doi.org/10.1063/1.1750380](https://doi.org/10.1063/1.1750380) |
| Savitzky, A., & Golay, M. (1964). *Anal. Chem.* | [doi.org/10.1021/ac60214a047](https://doi.org/10.1021/ac60214a047) |
| de Waard, C., & Milliams, D. E. (1975). *Corrosion* | [doi.org/10.5006/0010-9312-31.5.177](https://doi.org/10.5006/0010-9312-31.5.177) |
| de Waard, Lotz & Milliams (1991). *Corrosion* 47(12) | NACE — *Corrosion* journal (réel, ouvrage de référence CO₂) |
| Tukey, J. W. (1977). *Exploratory Data Analysis* | Ouvrage Addison-Wesley (ISBN 0-201-07616-0) |
| Bard, A. J., & Faulkner, L. R. (2001). *Electrochemical Methods* | Ouvrage Wiley (réf. mondiale électrochimie) |
| Pollock, D. D. (1991). *Physical Properties of Materials…* | Ouvrage CRC Press |
| Roberge, P. R. (2008). *Corrosion Engineering* | Ouvrage McGraw-Hill |
| Schweitzer, P. A. (2010). *Fundamentals of Corrosion* | Ouvrage CRC Press |
| Webster, J. G. (2014). *Measurement… Sensors Handbook* | Ouvrage CRC Press |
| Bergmeir, C., & Benítez, J. M. (2012). *Information Sciences* | [doi.org/10.1016/j.ins.2011.12.028](https://doi.org/10.1016/j.ins.2011.12.028) |
| Hyndman, R. J., & Koehler, A. B. (2006). *Int. J. Forecasting* | [doi.org/10.1016/j.ijforecast.2006.03.001](https://doi.org/10.1016/j.ijforecast.2006.03.001) |
| Chen, T., & Guestrin, C. (2016). XGBoost, *KDD* | [doi.org/10.1145/2939672.2939785](https://doi.org/10.1145/2939672.2939785) |
| Lundberg, S. M., & Lee, S. I. (2017). SHAP, *NeurIPS* | [arxiv.org/abs/1705.07874](https://arxiv.org/abs/1705.07874) |
| He, H., & Garcia, E. A. (2009). Imbalanced data, *IEEE TKDE* | [doi.org/10.1109/TKDE.2008.239](https://doi.org/10.1109/TKDE.2008.239) |
| Montgomery, D. C. (2017). *Design and Analysis of Experiments* | Ouvrage Wiley (réf. DOE) |
| Saxena, A., et al. (2008). C-MAPSS, *PHM Conf.* | [doi.org/10.1109/PHM.2008.4711414](https://doi.org/10.1109/PHM.2008.4711414) |
| Khadom, A. A., et al. (2009). T°/HCl, *Am. J. Appl. Sci.* | [thescipub — ajassp.2009.1403.1409](https://thescipub.com/abstract/10.3844/ajassp.2009.1403.1409) ✅ |
| Koch, G. H., et al. (2016). IMPACT Study, NACE | [impact.nace.org](http://impact.nace.org/) |
| Lasi, H., et al. (2014). Industry 4.0, *BISE* | [doi.org/10.1007/s12599-014-0334-4](https://doi.org/10.1007/s12599-014-0334-4) |
| Lu, Y. (2017). Industry 4.0 survey, *JII* | [doi.org/10.1016/j.jii.2017.04.005](https://doi.org/10.1016/j.jii.2017.04.005) |
| Xu, L. D., Xu, E. L., & Li, L. (2018). Industry 4.0, *IJPR* | [doi.org/10.1080/00207543.2018.1444806](https://doi.org/10.1080/00207543.2018.1444806) |

---

## 📐 Normes & lois — millésimes vérifiés cette session (officiels)
| Réf. | Lien officiel |
|---|---|
| ISO 8044:2024 — Vocabulaire corrosion | [iso.org/standard/82270](https://www.iso.org/standard/82270.html) |
| ISO 13381-1:2025 — Pronostic | [iso.org (catalogue 13381-1)](https://www.iso.org/standard/85944.html) |
| ISO 15156-1:2020 — H₂S | [iso.org/standard/71731](https://www.iso.org/standard/71731.html) |
| ISO 14224:2016 — fiabilité/maintenance O&G | [iso.org/standard/64076](https://www.iso.org/standard/64076.html) |
| ASTM G1-03 — éprouvettes corrosion | [astm.org/g0001-03r17e01](https://www.astm.org/g0001-03r17e01.html) |
| ASTM G31 — immersion labo | [astm.org/g0031-21](https://www.astm.org/g0031-21.html) |
| ASTM G96 — surveillance ER en service | [astm.org/g0096-90](https://www.astm.org/g0096-90.html) |
| NACE/AMPP SP0775-2023 — coupons | [store.ampp.org (SP0775)](https://store.ampp.org/sp0775-2023) |
| API 570 (5ᵉ éd. 2024) | [api.org — std570](https://www.api.org/products-and-services/standards/important-standards-announcements/std570) |
| API RP 580 (4ᵉ éd. 2023) | [api.org — API 580](https://www.api.org/products-and-services/individual-certification-programs/certifications/api580) |
| API RP 581 (4ᵉ éd. 2025) | api.org — API RP 581 (catalogue) |
| EN 13306:2017 — terminologie maintenance | [standards CEN/iteh (EN 13306:2017)](https://standards.iteh.ai/catalog/standards/cen/5af77559-ca38-483a-9310-823e8c517ee7/en-13306-2017) |
| NORSOK M-506 (rév. 3, 2017) | standards.no — NORSOK M-506 (catalogue) |
| **Loi n° 2019/008 du 25/04/2019 (Code Pétrolier)** | [prc.cm — loi 2019-008](https://www.prc.cm/fr/actualites/actes/lois/3572-loi-n-2019-008-du-25-avril-2019-portant-code-petrolier) ✅ |
| **Décret n° 2023/232 du 04/05/2023** | [prc.cm — décret 2023-232](https://www.prc.cm/fr/actualites/actes/decrets/6480-decret-n-2023-232-du-04-mai-2023-fixant-les-modalites-d-application-de-la-loi-n-2019-008-du-25-avril-2019-portant-code-petrolier) ✅ |
| **Loi-cadre n° 96/12 du 05/08/1996 (environnement)** | [minepded.gov.cm (PDF loi 96-12)](https://minepded.gov.cm/wp-content/uploads/2020/01/Loi-N%C2%B096-12-du-05-ao%C3%BBt-1996-portant-loi-cadre-relative-%C3%A0-la-gestion-de-l%E2%80%99environnement.pdf) ✅ |

---

## 🌐 Datasheets & sites officiels (liens du mémoire — à ouvrir pour confirmer)
| Réf. | Lien |
|---|---|
| Adafruit HX711 | [learn.adafruit.com/adafruit-hx711-24-bit-adc](https://learn.adafruit.com/adafruit-hx711-24-bit-adc) ✅ |
| AVIA Semiconductor — HX711 datasheet | Datasheet officielle (PDF largement disponible) ✅ |
| Espressif — ESP32 datasheet | [espressif.com/…/esp32](https://www.espressif.com/en/products/socs/esp32) ✅ |
| Cosasco — sondes ER | [cosasco.com/…er-temperature-probes](https://www.cosasco.com/product/dual-sensor-electrical-resistance-er-temperature-probes) ✅ |
| COTCO — présentation | [cotco-sa.cm/en/cotco-in-brief](https://cotco-sa.cm/en/cotco-in-brief/) ✅ |
| GLPI Project | [glpi-project.org](https://glpi-project.org/) ✅ |
| Streamlit | [docs.streamlit.io](https://docs.streamlit.io/) ✅ |
| Supabase | [supabase.com](https://supabase.com/) ✅ |
| XGBoost docs | [xgboost.readthedocs.io](https://xgboost.readthedocs.io/) ✅ |
| Wikipedia — Chad-Cameroon Pipeline | [en.wikipedia.org/…Pipeline_Project](https://en.wikipedia.org/wiki/Chad%E2%80%93Cameroon_Petroleum_Development_and_Pipeline_Project) ✅ |
| Wikipedia — CMMS | [en.wikipedia.org/…maintenance_management_system](https://en.wikipedia.org/wiki/Computerized_maintenance_management_system) ✅ |
| Inspectioneering — coût corrosion 2,5 T$ | [inspectioneering.com/news/2016-03-08/5202](https://inspectioneering.com/news/2016-03-08/5202) ✅ |
| Akash, S. (2024). ISO 13381 (LinkedIn Pulse) | ⚠️ Billet de blog LinkedIn — **source faible pour un mémoire**, préférer la norme ISO elle-même |
| **Next.js / Vercel** | ⚠️ **Hors-sujet** : ces technos ne sont PAS utilisées (stack = Streamlit/Supabase) → à **retirer** de la biblio |

---

## ⚠️ Littérature grise / régionale — à vérifier à la main
| Réf. | Note |
|---|---|
| Aniobi, C. C. (2018) & Egbule, P. E., et al. (2018) — NNPC/PPMC, *Academia.edu* | ⚠️ **Deux entrées quasi identiques** (même cas NNPC/PPMC) → doublon suspect ; *Academia.edu* = source non revue par les pairs |
| Onyebuchi, V., et al. (2018) — *Unizik J. of Eng.* | ⚠️ Revue régionale — vérifier l'existence |
| ExxonMobil (2011). Chad/Cameroon Project Update No. 30 | ⚠️ Rapport — vérifier l'archive |
| HSPublishing (2023) ; Pumps Africa (2024) ; Persian Utab (2023) | ⚠️ Blogs/sites commerciaux (liens fournis dans le mémoire) — **sources faibles**, à ouvrir pour confirmer |
| Mansfeld, F. (2014). *Materials and Corrosion* ; Lopes et al. (2016). *Procedia CIRP* ; Roda & Macchi (2018) | ⚠️ Auteurs/revues **réels et plausibles** mais **détails non confirmés individuellement** — à recontrôler |

---

## 🧭 Recommandations
1. **Retirer** les 6 références ❌ (Murphy, Mayer/LEROY, Cheng & Niu, Lu & Luo, Ma 2021, Xu 2020) — ce sont les plus dangereuses devant un jury.
2. **Corriger** les auteurs/années faux : Yan&Yan→Kuang&Long ; Heydari&Talebpour→Ma et al. ; Bagheri 2024→2015 IFAC ; Liu 2025 vol/art ; Hu 2024 n° d'article.
3. **Retirer** Next.js/Vercel (hors-sujet) et **remplacer** les blogs (Akash, Persian Utab…) par des sources primaires.
4. Garder tous les **classiques, normes et lois** — ils sont solides (liens ci-dessus).
5. Vérifier toi-même les ⚠️ « à contrôler » via les liens.

> **Note d'honnêteté** : j'ai cherché en ligne individuellement les ~20 références à risque (articles récents, revues obscures). Les classiques, normes, lois et sites officiels sont des sources établies dont je fournis l'URL canonique — fiables, mais ouvre chaque lien pour confirmation finale.
