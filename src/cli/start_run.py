"""
Démarre un run RTF : INSERT dans cr_runs → retourne le run_id.
Usage : python src/cli/start_run.py --inhibitor 0 --ph 7.0 --notes "Run 1 baseline"
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gdlopwhzigndkmmmuzwr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ASSET_ID     = "sonde-01"

HEADERS = {
    "Content-Type": "application/json",
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Prefer": "return=representation",
}


def start_run(inhibitor_pct: float, ph: float | None, notes: str) -> str:
    payload = {
        "asset_id":      ASSET_ID,
        "started_at":    datetime.now(timezone.utc).isoformat(),
        "inhibitor_pct": inhibitor_pct,
        "notes":         notes,
        "status":        "active",
    }
    if ph is not None:
        payload["ph_run"] = ph

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/cr_runs",
        headers=HEADERS,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    run_id = data[0]["run_id"] if isinstance(data, list) else data["run_id"]
    return run_id


def save_run_id_local(run_id: str):
    """Sauvegarde le run_id actif dans .current_run pour les autres scripts."""
    path = os.path.join(os.path.dirname(__file__), "../../.current_run")
    with open(path, "w") as f:
        json.dump({"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Démarrer un run RTF")
    parser.add_argument("--inhibitor", type=float, default=0.0, help="% inhibiteur (0=baseline)")
    parser.add_argument("--ph",        type=float, default=None, help="pH de la solution")
    parser.add_argument("--notes",     type=str,   default="",   help="Notes libres")
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERREUR: variable SUPABASE_KEY non définie", file=sys.stderr)
        print("  export SUPABASE_KEY='eyJ...'", file=sys.stderr)
        sys.exit(1)

    run_id = start_run(args.inhibitor, args.ph, args.notes)
    save_run_id_local(run_id)

    print(f"✓ Run démarré")
    print(f"  run_id     : {run_id}")
    print(f"  inhibiteur : {args.inhibitor}%")
    if args.ph:
        print(f"  pH         : {args.ph}")
    print(f"  notes      : {args.notes}")
    print()
    print(f"→ Flashez maintenant l'ESP32, il lira ce run_id au boot.")
    print(f"  (ou configurez manuellement via ArduinoOTA si disponible)")


if __name__ == "__main__":
    main()
