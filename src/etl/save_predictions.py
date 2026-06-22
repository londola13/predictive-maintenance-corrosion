"""
Insère les prédictions ML dans cr_predictions.
Appelé automatiquement par le pipeline après --mode predict.
Usage : python src/etl/save_predictions.py --run-id UUID --cr 0.12 --rul 4200 --model-version v1
"""
import argparse
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
    "Prefer": "return=minimal",
}


def save_prediction(run_id: str, cr_pred: float, rul_pred: float, model_version: str = "v1"):
    payload = {
        "run_id":        run_id,
        "predicted_at":  datetime.now(timezone.utc).isoformat(),
        "cr_pred":       round(cr_pred, 6),
        "rul_pred":      round(rul_pred, 2),
        "model_version": model_version,
    }
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/cr_predictions",
        headers=HEADERS,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.status_code == 201


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id",        required=True)
    parser.add_argument("--cr",            type=float, required=True, help="CR prédit (mm/an)")
    parser.add_argument("--rul",           type=float, required=True, help="RUL prédit (heures)")
    parser.add_argument("--model-version", default="v1")
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERREUR: SUPABASE_KEY non défini", file=sys.stderr)
        sys.exit(1)

    ok = save_prediction(args.run_id, args.cr, args.rul, args.model_version)
    if ok:
        print(f"✓ Prédiction sauvegardée : CR={args.cr:.4f} mm/an  RUL={args.rul:.1f}h")
    else:
        print("ECHEC insertion", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
