# -*- coding: utf-8 -*-
"""
Calculateur INDICATIF : effet d'un acide moins agressif (dilution / inhibiteur)
sur la durée de vie du fil.

Principe physique simple : le fil se corrode à la vitesse CR ; sa durée de vie est
donc ~ inversement proportionnelle au CR. Réduire l'agressivité du milieu (diluer,
ou ajouter un inhibiteur qui adsorbe sur le métal) abaisse le CR, donc allonge la vie :

        durée  ≈  durée_acide_pur × 1 / (1 − réduction_CR)

Les points d'ancrage proviennent des RUNS RÉELS (durées jusqu'à rupture) :

  - Acide pur            → 10–15 h (médiane ≈ 12,5 h)   [tous les runs non dilués]
  - Run #1 (dilué)       → 22,3 h                        proportion INCONNUE
  - Run #2 (≈ 1:1)       → ~62 h                         (biais gravité — durée indicative)
  - Run #3 (≈ 2:1)       → ~93 h

⚠️ ESTIMATION INDICATIVE, non contractuelle :
  - peu de points (4) et proportions partiellement inconnues (Run #1) ;
  - la dilution est un PROXY de l'effet « acide moins agressif » d'un inhibiteur réel,
    pas un dosage d'inhibiteur (qui exigerait une campagne dédiée, imidazoline dosée) ;
  - Run #2 est biaisé (rupture par traction) — sa durée est seulement indicative.
"""

# Médiane des runs à acide pur (non dilués), durée jusqu'à rupture
BASELINE_PURE_H = 12.5

# Ancres empiriques (runs réels) : durée de vie vs niveau de dilution
ANCRES = [
    {"label": "Acide pur",       "duree_h": 12.5, "dilution": "0 (référence)"},
    {"label": "Run #1",          "duree_h": 22.3, "dilution": "dilué — proportion inconnue"},
    {"label": "Run #2",          "duree_h": 62.0, "dilution": "≈ 1:1 (acide:eau)"},
    {"label": "Run #3",          "duree_h": 93.0, "dilution": "≈ 2:1 (eau:acide)"},
]

CAVEATS = (
    "Estimation indicative : 4 points seulement, proportions partiellement inconnues "
    "(Run #1), dilution = proxy de l'effet d'un inhibiteur réel (pas un dosage), "
    "Run #2 biaisé (traction). Un dosage précis exige une campagne avec inhibiteur calibré."
)


def _ancre_la_plus_proche(duree_h: float) -> dict:
    return min(ANCRES, key=lambda a: abs(a["duree_h"] - duree_h))


def facteur_vie(reduction_cr_pct: float) -> float:
    """Facteur multiplicatif de durée pour une réduction de CR de `reduction_cr_pct` %."""
    f = max(1e-3, 1.0 - reduction_cr_pct / 100.0)
    return 1.0 / f


def estimer_par_reduction(reduction_cr_pct: float, baseline_h: float = BASELINE_PURE_H) -> dict:
    """À partir d'une réduction de CR visée (%), estime la durée de vie obtenue."""
    fac = facteur_vie(reduction_cr_pct)
    duree = baseline_h * fac
    return {
        "reduction_cr_pct": round(reduction_cr_pct, 1),
        "facteur_vie": round(fac, 2),
        "duree_estimee_h": round(duree, 1),
        "gain_h": round(duree - baseline_h, 1),
        "analogue": _ancre_la_plus_proche(duree),
    }


def estimer_par_duree_cible(duree_cible_h: float, baseline_h: float = BASELINE_PURE_H) -> dict:
    """À partir d'une durée de vie cible (h), estime la réduction de CR nécessaire."""
    fac = max(1.0, duree_cible_h / baseline_h)
    reduction = (1.0 - 1.0 / fac) * 100.0
    return {
        "duree_cible_h": round(duree_cible_h, 1),
        "facteur_vie": round(fac, 2),
        "reduction_cr_pct": round(reduction, 1),
        "analogue": _ancre_la_plus_proche(duree_cible_h),
    }
