# -*- coding: utf-8 -*-
"""
CMMS maison minimal — ordres de travail (cr_work_orders) à partir de l'état du fil.

Remplace l'intégration GLPI (`src/integrations/glpi_api.py`) : les CMMS gratuits
n'exposent pas d'API (réservée au plan pro). Ici, un ordre de travail (OT) est créé
dans Supabase quand le fil dépasse un seuil (section perdue / RUL), avec dédoublonnage
(un seul OT ouvert par run et par niveau).

API :
  create_work_order(run_id, niveau, cr, rul, section, alert_id=None) -> wo_id | None
  list_work_orders(statut=None, run_id=None) -> list[dict]
  update_statut(wo_id, statut, assignee=None) -> bool

Secrets : SUPABASE_URL / SUPABASE_KEY via l'environnement (jamais en dur).
"""
import os
from datetime import datetime, timezone

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gdlopwhzigndkmmmuzwr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_H = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
_HW = {**_H, "Content-Type": "application/json", "Prefer": "return=representation"}

PRIORITE = {"rouge": 1, "orange": 3, "vert": 5}


def _description(niveau: str, cr: float, rul: float, section: float) -> str:
    if niveau == "rouge":
        action = ("INTERVENTION URGENTE — le fil est proche de la rupture. "
                  "Préparer le remplacement du coupon / clôturer le run.")
    elif niveau == "orange":
        action = "Planifier une inspection — corrosion avancée, surveiller de près."
    else:
        action = "Surveillance nominale."
    return (
        "Sonde ER — état du fil corrodé.\n"
        f"Niveau         : {niveau.upper()}\n"
        f"CR (ML)        : {cr:.1f}\n"
        f"RUL estimé     : {rul:.1f} h\n"
        f"Section perdue : {section:.0f} %\n"
        f"Action         : {action}"
    )


def _existe_ouvert(run_id: str, niveau: str) -> bool:
    """True si un OT OUVERT de ce niveau existe déjà pour ce run (dédoublonnage)."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/cr_work_orders",
        headers=_H,
        params={"run_id": f"eq.{run_id}", "niveau": f"eq.{niveau}",
                "statut": "eq.ouvert", "select": "wo_id", "limit": "1"},
        timeout=10,
    )
    r.raise_for_status()
    return len(r.json()) > 0


def create_work_order(run_id: str, niveau: str, cr: float, rul: float,
                      section: float, alert_id: str | None = None) -> str | None:
    """Crée un OT si le niveau est orange/rouge ET qu'aucun OT ouvert de même
    niveau n'existe pour ce run. Retourne wo_id, ou None si rien créé."""
    if niveau == "vert":
        return None
    if _existe_ouvert(run_id, niveau):
        return None
    titre = f"[CORROSION] {niveau.upper()} — Run {str(run_id)[:8]} — section {section:.0f}%"
    payload = {
        "run_id": run_id, "alert_id": alert_id, "niveau": niveau,
        "titre": titre, "description": _description(niveau, cr, rul, section),
        "cr_pred": round(float(cr), 4), "rul_pred": round(float(rul), 2),
        "section_pct": round(float(section), 1),
        "priorite": PRIORITE.get(niveau, 3), "statut": "ouvert",
    }
    r = requests.post(f"{SUPABASE_URL}/rest/v1/cr_work_orders",
                      headers=_HW, json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data[0]["wo_id"] if data else None


def list_work_orders(statut: str | None = None, run_id: str | None = None) -> list[dict]:
    params = {"order": "created_at.desc", "select": "*"}
    if statut:
        params["statut"] = f"eq.{statut}"
    if run_id:
        params["run_id"] = f"eq.{run_id}"
    r = requests.get(f"{SUPABASE_URL}/rest/v1/cr_work_orders",
                     headers=_H, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def update_statut(wo_id: str, statut: str, assignee: str | None = None) -> bool:
    body: dict = {"statut": statut}
    if statut == "ferme":
        body["closed_at"] = datetime.now(timezone.utc).isoformat()
    if assignee is not None:
        body["assignee"] = assignee
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/cr_work_orders?wo_id=eq.{wo_id}",
        headers={**_H, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=body, timeout=10,
    )
    r.raise_for_status()
    return True
