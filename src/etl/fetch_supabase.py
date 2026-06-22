"""
Récupère les mesures d'un run depuis Supabase → DataFrame compatible pipeline.
Usage : python src/etl/fetch_supabase.py --run-id UUID [--output data/run.csv]
"""
import argparse
import os
import sys

import pandas as pd
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gdlopwhzigndkmmmuzwr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

COLUMNS = ["timestamp_s", "vdiff_v", "rx_ohm", "temp_c", "delta_r_per_h"]


def fix_rx_from_vdiff(df: pd.DataFrame, r_shunt: float = 970.0,
                      cal: float = 33.7, vcc: float = 3.45) -> pd.DataFrame:
    """Recalcule rx_ohm depuis vdiff_v là où le firmware l'a figé à 0.

    Sur l'ancien ESP32 (USB mort, non reflashable), le garde-fou firmware (Rx>100)
    gèle rx_ohm à 0 dès que la résistance dépasse la plage — MAIS vdiff_v reste sain.
    On reconstruit alors la valeur que le firmware aurait dû calculer :
        rx = vdiff × (2·R_shunt·CAL / VCC)        (formule firmware, R_shunt=R_lift)
    N'affecte QUE les lignes figées (rx≈0 & vdiff>1 mV positif) : les runs valides
    (firmware qui calcule un rx correct) sont laissés strictement intacts.
    Principe : ne jamais faire confiance au rx_ohm buggé — vdiff est la vérité.
    """
    if "vdiff_v" not in df.columns or "rx_ohm" not in df.columns:
        return df
    rx = pd.to_numeric(df["rx_ohm"], errors="coerce")
    vd = pd.to_numeric(df["vdiff_v"], errors="coerce")
    fige = (rx.abs() < 1e-9) & (vd > 1e-3)
    if fige.any():
        df.loc[fige, "rx_ohm"] = vd[fige] * (2.0 * r_shunt * cal / vcc)
    return df


def fetch_run(run_id: str) -> pd.DataFrame:
    # Pagination par tranches de 1000 (limite PostgREST par defaut)
    page = 1000
    offset = 0
    rows = []
    while True:
        params = {
            "run_id": f"eq.{run_id}",
            "order":  "timestamp_s.asc",
            "select": ",".join(COLUMNS),
            "limit":  str(page),
            "offset": str(offset),
        }
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/cr_measurements",
            headers=HEADERS,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data)
        if len(data) < page:
            break
        offset += page
    if not rows:
        raise ValueError(f"Aucune mesure pour run_id={run_id}")
    df = pd.DataFrame(rows)[COLUMNS]
    for col in COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = fix_rx_from_vdiff(df)   # rx figé par le garde-fou -> recalculé depuis vdiff
    return df


def fetch_all_runs() -> pd.DataFrame:
    """Retourne la liste de tous les runs (pour le sélecteur Streamlit)."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/cr_runs",
        headers=HEADERS,
        params={"order": "started_at.desc", "select": "run_id,started_at,ended_at,inhibitor_pct,ph_run,notes,status"},
        timeout=10,
    )
    resp.raise_for_status()
    return pd.DataFrame(resp.json())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", default=None, help="Chemin CSV de sortie (optionnel)")
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERREUR: SUPABASE_KEY non défini", file=sys.stderr)
        sys.exit(1)

    df = fetch_run(args.run_id)
    print(f"✓ {len(df)} mesures récupérées pour run {args.run_id}")
    print(df.describe().to_string())

    if args.output:
        df.to_csv(args.output, sep=";", index=False)
        print(f"✓ Sauvegardé → {args.output}")


if __name__ == "__main__":
    main()
