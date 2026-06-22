"""
Évalue les seuils sur la dernière prédiction et insère dans cr_alerts.
Usage : python src/etl/trigger_alerts.py --run-id UUID
"""
import argparse
import os
import sys
from datetime import datetime, timezone

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gdlopwhzigndkmmmuzwr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

HEADERS_READ = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}
HEADERS_WRITE = {**HEADERS_READ, "Content-Type": "application/json", "Prefer": "return=minimal"}

# Seuils NACE SP0775
CR_ORANGE = 0.10   # mm/an
CR_ROUGE  = 0.25   # mm/an
RUL_ORANGE = 2000  # heures
RUL_ROUGE  = 500   # heures


def get_latest_prediction(run_id: str) -> dict | None:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/cr_predictions",
        headers=HEADERS_READ,
        params={"run_id": f"eq.{run_id}", "order": "predicted_at.desc", "limit": "1"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data[0] if data else None


def insert_alert(run_id: str, niveau: str, message: str):
    payload = {
        "run_id":     run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "niveau":     niveau,
        "message":    message,
    }
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/cr_alerts",
        headers=HEADERS_WRITE,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()


def evaluer(cr: float, rul: float) -> tuple[str, str]:
    if cr >= CR_ROUGE or rul <= RUL_ROUGE:
        return "rouge", f"CR={cr:.4f} mm/an ≥ {CR_ROUGE} ou RUL={rul:.0f}h ≤ {RUL_ROUGE}h — INTERVENTION URGENTE"
    if cr >= CR_ORANGE or rul <= RUL_ORANGE:
        return "orange", f"CR={cr:.4f} mm/an ≥ {CR_ORANGE} ou RUL={rul:.0f}h ≤ {RUL_ORANGE}h — Planifier inspection"
    return "vert", f"CR={cr:.4f} mm/an — RUL={rul:.0f}h — Nominal"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERREUR: SUPABASE_KEY non défini", file=sys.stderr)
        sys.exit(1)

    pred = get_latest_prediction(args.run_id)
    if not pred:
        print(f"Aucune prédiction pour run_id={args.run_id}", file=sys.stderr)
        sys.exit(1)

    niveau, message = evaluer(float(pred["cr_pred"]), float(pred["rul_pred"]))
    insert_alert(args.run_id, niveau, message)
    print(f"✓ Alerte [{niveau.upper()}] : {message}")


if __name__ == "__main__":
    main()
