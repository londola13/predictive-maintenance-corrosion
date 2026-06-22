"""
Configure le run_id actif dans la NVS de l'ESP32 via un serveur HTTP minimal.
L'ESP32 doit avoir le sketch HTTP config chargé (ou utiliser le firmware actuel
qui lit la NVS au boot — mettre à jour manuellement via ArduinoIDE si besoin).

Alternative simple : génère le code C++ à coller dans secrets.h
Usage : python src/cli/set_run_id.py [--run-id UUID]
"""
import argparse
import json
import os
import sys


def load_current_run_id() -> str | None:
    path = os.path.join(os.path.dirname(__file__), "../../.current_run")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return data.get("run_id")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=str, default=None)
    args = parser.parse_args()

    run_id = args.run_id or load_current_run_id()
    if not run_id:
        print("Aucun run_id trouvé. Lancez d'abord start_run.py", file=sys.stderr)
        sys.exit(1)

    print(f"\nrun_id actif : {run_id}")
    print()
    print("─── Option A — Ligne à ajouter dans secrets.h avant flash ───")
    print(f'#define RUN_ID "{run_id}"')
    print()
    print("─── Option B — Commande ArduinoOTA si disponible ───")
    print(f"  Non implémenté dans ce firmware (NVS mise à jour au prochain flash)")


if __name__ == "__main__":
    main()
