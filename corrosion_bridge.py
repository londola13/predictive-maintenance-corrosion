# -*- coding: utf-8 -*-
"""Pont temps reel : ancien ESP32 (rx fige a 0) -> Run #19 avec R reconstruite depuis vdiff.

L'ancien ESP32 (USB mort, non reflashable) poste dans Run #14 avec rx_ohm=0 (garde-fou),
MAIS vdiff_v est sain. Ce pont, toutes les 30 s :
  1. lit les nouveaux posts de Run #14,
  2. calcule  R = vdiff_v * (R_shunt + R_lift) / VCC,
  3. insere une ligne propre dans Run #19,
  4. retire le parasite de Run #14 (garde Run #14 propre).

Lancer dans un terminal et LAISSER OUVERT pendant tout le run :
    venv/Scripts/python.exe corrosion_bridge.py

Aucune donnee perdue si on l'arrete : vdiff reste dans Run #14, on peut re-synchroniser apres.
"""
import os, time, requests, datetime

URL = "https://gdlopwhzigndkmmmuzwr.supabase.co"
KEY = os.environ.get("SK") or os.environ.get("SUPABASE_KEY")
if not KEY:
    raise SystemExit("Definir SK (service_role) dans l'environnement avant de lancer.")
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

RUN14 = "83760a06-b2c8-4730-8368-18babfcae3e1"          # ou poste l'ancien ESP32
RUN19 = open("dashboard/.run19_id").read().strip()        # destination propre
VCC   = 3.45
RS    = 970.0 + 970.0                                      # R_shunt + R_lift

CUTOFF  = int(time.time()) - 7200    # ne touche jamais aux donnees d'origine de Run #14 (>10j)
last_ts = CUTOFF

def reconstruire_R(vdiff_v):
    return float(vdiff_v) * RS / VCC

print(f"=== Pont ancien ESP32 -> Run #19 ===")
print(f"  source Run #14 : {RUN14[:12]}   dest Run #19 : {RUN19[:12]}")
print(f"  R = vdiff x {RS:.0f}/{VCC} = vdiff x {RS/VCC:.1f}")
print(f"  (Ctrl+C pour arreter ; vdiff reste stocke, aucune perte)\n")

while True:
    try:
        r = requests.get(f"{URL}/rest/v1/cr_measurements", headers=H,
            params={"run_id": f"eq.{RUN14}", "timestamp_s": f"gt.{last_ts}",
                    "select": "timestamp_s,vdiff_v,temp_c", "order": "timestamp_s.asc"},
            timeout=30).json()
        if r:
            rows = []
            for x in r:
                if x.get("vdiff_v") is None:
                    continue
                rows.append({"run_id": RUN19, "asset_id": "sonde-01", "timestamp_s": x["timestamp_s"],
                             "vdiff_v": x["vdiff_v"], "rx_ohm": round(reconstruire_R(x["vdiff_v"]), 4),
                             "temp_c": x["temp_c"]})
            if rows:
                ins = requests.post(f"{URL}/rest/v1/cr_measurements", headers=H, json=rows, timeout=30)
                if ins.status_code in (200, 201):
                    mx = max(int(x["timestamp_s"]) for x in r)
                    # nettoyage Run #14 : borne basse fixe = CUTOFF -> ne touche JAMAIS l'original (>10j)
                    requests.delete(f"{URL}/rest/v1/cr_measurements", headers=H,
                        params={"run_id": f"eq.{RUN14}",
                                "and": f"(timestamp_s.gt.{CUTOFF},timestamp_s.lte.{mx})"},
                        timeout=30)
                    last_ts = mx
                    der = rows[-1]
                    hh = datetime.datetime.utcfromtimestamp(int(der["timestamp_s"])).strftime("%H:%M:%S")
                    print(f"  {hh}  +{len(rows)} pts -> Run#19   R={der['rx_ohm']:.3f} Ohm  T={der['temp_c']} C")
                else:
                    print(f"  ERREUR insert HTTP {ins.status_code}: {ins.text[:120]}")
        time.sleep(30)
    except KeyboardInterrupt:
        print("\nArret. vdiff toujours stocke dans Run #14 -> re-sync possible quand tu veux.")
        break
    except Exception as e:
        print(f"  [warn] {e} -- retry dans 30s")
        time.sleep(30)
