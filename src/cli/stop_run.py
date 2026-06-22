"""
Termine le run actif : UPDATE cr_runs SET ended_at, status='completed'.
Usage : python src/cli/stop_run.py [--run-id UUID]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gdlopwhzigndkmmmuzwr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

HEADERS = {
    "Content-Type": "application/json",
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Prefer": "return=representation",
}


def load_current_run_id() -> str | None:
    path = os.path.join(os.path.dirname(__file__), "../../.current_run")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return data.get("run_id")


def stop_run(run_id: str):
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/cr_runs?run_id=eq.{run_id}",
        headers=HEADERS,
        json={"ended_at": datetime.now(timezone.utc).isoformat(), "status": "completed"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def clear_current_run():
    path = os.path.join(os.path.dirname(__file__), "../../.current_run")
    if os.path.exists(path):
        os.remove(path)


def main():
    parser = argparse.ArgumentParser(description="Terminer le run RTF actif")
    parser.add_argument("--run-id", type=str, default=None, help="UUID du run (optionnel, lu depuis .current_run)")
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERREUR: variable SUPABASE_KEY non définie", file=sys.stderr)
        sys.exit(1)

    run_id = args.run_id or load_current_run_id()
    if not run_id:
        print("ERREUR: aucun run actif trouvé. Passez --run-id UUID", file=sys.stderr)
        sys.exit(1)

    data = stop_run(run_id)
    clear_current_run()

    print(f"✓ Run terminé")
    print(f"  run_id   : {run_id}")
    if data and isinstance(data, list) and data:
        row = data[0]
        print(f"  démarré  : {row.get('started_at', '?')}")
        print(f"  terminé  : {row.get('ended_at', '?')}")


if __name__ == "__main__":
    main()
