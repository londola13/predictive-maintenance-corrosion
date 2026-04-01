"""
decision_engine.py
------------------
Moteur de décision RBI (Risk-Based Inspection).
Combine les 3 types de seuils pour générer :
  - Classification risque par CML
  - Plan d'inspection optimisé
  - Recommandations d'action
  - Alertes prioritaires

Normes : API 580/581 | NACE SP0775 | ASME B31.3
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field

# ── Seuils Type 1 — Normatifs (NACE SP0775) ──────────────────────────────────

SEUILS_CR_NACE = [
    (0.025, "Acceptable", "🟢", 24),    # inspection tous les 24 mois
    (0.050, "Faible",     "🟢", 18),
    (0.125, "Modéré",     "🟡", 12),
    (0.250, "Élevé",      "🟠",  6),
    (0.500, "Sévère",     "🔴",  3),
    (9.999, "Critique",   "⛔",  1),    # inspection mensuelle
]

# Priorité numérique pour tri
PRIORITE_MAP = {
    "Acceptable": 1, "Faible": 2, "Modéré": 3,
    "Élevé": 4, "Sévère": 5, "Critique": 6
}


@dataclass
class EvaluationCML:
    """Résultat complet d'évaluation d'un CML."""
    CML_ID:               str
    CR_predit:            float     # mm/an
    RL_median:            float     # années
    RL_pessimiste:        float
    risque_NACE:          str
    emoji:                str
    priorite:             int
    frequence_inspection: int       # mois
    technique:            str
    actions:              list[str] = field(default_factory=list)
    alertes:              list[str] = field(default_factory=list)
    score_anomalie:       int = 0


def evaluer_cml(
    CML_ID:     str,
    CR_predit:  float,
    RL_median:  float,
    RL_pessimiste: float = None,
    t_mm:       float = None,
    t_min_mm:   float = None,
    score_anomalie: int = 0,
    seuils_ml:  dict = None,
) -> EvaluationCML:
    """
    Évalue un CML selon les 3 types de seuils et génère les recommandations.

    Args:
        CML_ID       : identifiant du CML
        CR_predit    : taux de corrosion prédit (mm/an)
        RL_median    : durée de vie résiduelle médiane (ans)
        RL_pessimiste: RL pessimiste (IC 10%)
        t_mm         : épaisseur actuelle (mm)
        t_min_mm     : épaisseur minimale ASME (mm)
        score_anomalie: score anomalie process (0-100)
        seuils_ml    : seuils appris par ML (Type 2)
    """
    if RL_pessimiste is None:
        RL_pessimiste = RL_median * 0.7

    # ── Type 1 : Seuils normatifs ────────────────────────────────────────────
    risque, emoji, freq_mois = _classer_risque_nace(CR_predit)

    # ── Type 2 : Seuils ML (si disponibles) ─────────────────────────────────
    if seuils_ml:
        risque, freq_mois = _appliquer_seuils_ml(CR_predit, risque, freq_mois, seuils_ml)

    # ── Type 3 : Seuils statistiques (RL) ───────────────────────────────────
    # RL pessimiste < 2 ans → escalader risque
    if RL_pessimiste < 2.0 and priorite_de(risque) < priorite_de("Élevé"):
        risque = "Élevé"
        emoji  = "🟠"
        freq_mois = min(freq_mois, 6)

    if RL_pessimiste < 1.0:
        risque = "Critique"
        emoji  = "⛔"
        freq_mois = 1

    priorite = PRIORITE_MAP.get(risque, 3)

    # ── Actions et alertes ───────────────────────────────────────────────────
    actions = _generer_actions(risque, CR_predit, RL_median, t_mm, t_min_mm, score_anomalie)
    alertes = _generer_alertes(risque, RL_pessimiste, score_anomalie, t_mm, t_min_mm)
    technique = _choisir_technique(risque, CR_predit)

    return EvaluationCML(
        CML_ID=CML_ID,
        CR_predit=round(CR_predit, 4),
        RL_median=round(RL_median, 1),
        RL_pessimiste=round(RL_pessimiste, 1),
        risque_NACE=risque,
        emoji=emoji,
        priorite=priorite,
        frequence_inspection=freq_mois,
        technique=technique,
        actions=actions,
        alertes=alertes,
        score_anomalie=score_anomalie,
    )


def generer_plan_inspection(evaluations: list[EvaluationCML]) -> pd.DataFrame:
    """
    Génère le plan d'inspection optimisé (API 580/581).
    Trie par priorité de risque décroissante.

    Returns:
        DataFrame prêt pour affichage dans le dashboard.
    """
    lignes = []
    for ev in sorted(evaluations, key=lambda x: x.priorite, reverse=True):
        lignes.append({
            "Priorité":           ev.emoji,
            "CML_ID":             ev.CML_ID,
            "CR prédit (mm/an)":  ev.CR_predit,
            "RL médiane (ans)":   ev.RL_median,
            "RL pessimiste (ans)": ev.RL_pessimiste,
            "Risque NACE":        ev.risque_NACE,
            "Fréq. inspection":   f"Tous les {ev.frequence_inspection} mois",
            "Technique":          ev.technique,
            "Actions":            " | ".join(ev.actions[:2]),
        })
    return pd.DataFrame(lignes)


def extraire_alertes_critiques(
    evaluations: list[EvaluationCML]
) -> list[dict]:
    """
    Retourne toutes les alertes des CML critiques et sévères.
    Utilisé pour la Page 5 du dashboard.
    """
    alertes_critiques = []
    for ev in evaluations:
        if ev.priorite >= 5:  # Sévère ou Critique
            alertes_critiques.append({
                "CML_ID":    ev.CML_ID,
                "risque":    ev.risque_NACE,
                "emoji":     ev.emoji,
                "alertes":   ev.alertes,
                "actions":   ev.actions,
                "CR":        ev.CR_predit,
                "RL":        ev.RL_pessimiste,
            })
    return alertes_critiques


# ── Fonctions internes ────────────────────────────────────────────────────────

def _classer_risque_nace(CR: float) -> tuple[str, str, int]:
    for seuil, risque, emoji, freq in SEUILS_CR_NACE:
        if CR <= seuil:
            return risque, emoji, freq
    return "Critique", "⛔", 1


def _appliquer_seuils_ml(CR, risque_actuel, freq_actuel, seuils_ml) -> tuple:
    """Ajuste le risque selon les seuils appris par ML (Type 2)."""
    seuil_ml = seuils_ml.get("CR_critique_ml", None)
    if seuil_ml and CR > seuil_ml:
        # ML dit que ce CR est critique pour ce site
        if priorite_de(risque_actuel) < priorite_de("Élevé"):
            return "Élevé", min(freq_actuel, 6)
    return risque_actuel, freq_actuel


def _generer_actions(risque, CR, RL_median, t_mm, t_min_mm, score_anomalie) -> list:
    """Génère les actions recommandées selon le niveau de risque."""
    actions = []

    if risque in ("Critique", "Sévère"):
        actions.append("INSPECTION UT URGENTE — planifier sous 30 jours")
        actions.append("Augmenter dose inhibiteur → viser 80 mg/L")
        if t_mm and t_min_mm and (t_mm - t_min_mm) < 3:
            actions.append("ALERTE ÉPAISSEUR — approche t_min ASME B31.3")
    elif risque == "Élevé":
        actions.append("Planifier inspection UT dans les 3 prochains mois")
        actions.append("Vérifier dosage inhibiteur (CI-5003 > 40 mg/L)")
    elif risque == "Modéré":
        actions.append("Maintenir fréquence inspection à 12 mois")
        actions.append("Surveiller tendance CR sur 3 mesures")
    else:
        actions.append("Continuer surveillance normale")

    if score_anomalie > 70:
        actions.append("CONDITIONS PROCESS ANORMALES — vérifier DCS immédiatement")

    return actions


def _generer_alertes(risque, RL_pessimiste, score_anomalie, t_mm, t_min_mm) -> list:
    alertes = []

    if risque == "Critique":
        alertes.append(f"Taux de corrosion CRITIQUE > 0.5 mm/an")
    if RL_pessimiste < 1.0:
        alertes.append(f"URGENCE : durée de vie résiduelle < 1 an")
    elif RL_pessimiste < 3.0:
        alertes.append(f"Durée de vie résiduelle < 3 ans (scénario pessimiste)")
    if score_anomalie > 70:
        alertes.append(f"Anomalie process détectée (score = {score_anomalie}/100)")
    if t_mm and t_min_mm:
        marge = t_mm - t_min_mm
        if marge < 2.0:
            alertes.append(f"Marge épaisseur critique : {marge:.1f} mm restants")

    return alertes


def _choisir_technique(risque, CR) -> str:
    """Choisit la technique d'inspection selon le risque et le taux de corrosion."""
    if risque in ("Critique", "Sévère"):
        return "UT manuel + TOFD (Time-of-Flight Diffraction)"
    elif risque == "Élevé":
        return "UT manuel (grille 5×5 cm)"
    elif risque == "Modéré":
        return "UT manuel (points fixes CML)"
    else:
        return "UT manuel (inspection standard)"


def priorite_de(risque: str) -> int:
    return PRIORITE_MAP.get(risque, 1)
