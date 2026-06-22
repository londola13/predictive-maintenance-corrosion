"""
Client GLPI minimal — crée des tickets de maintenance à partir des alertes cr_alerts.

Prérequis GLPI :
  - URL de l'instance (self-hosted ou GLPI Network cloud)
  - App token (Administration > API > Ajouter une application)
  - User token (utilisateur GLPI → Profil → API token)

Variables d'environnement :
  GLPI_URL         ex. https://glpi.example.com  ou  https://support.glpi.cloud
  GLPI_APP_TOKEN   token applicatif
  GLPI_USER_TOKEN  token utilisateur

Usage :
  python src/integrations/glpi_api.py --run-id UUID
"""

import os
import sys
import argparse
import requests

GLPI_URL        = os.environ.get("GLPI_URL", "")
GLPI_APP_TOKEN  = os.environ.get("GLPI_APP_TOKEN", "")
GLPI_USER_TOKEN = os.environ.get("GLPI_USER_TOKEN", "")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gdlopwhzigndkmmmuzwr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Mapping niveau → urgence/impact GLPI (1=très haut, 5=très bas)
NIVEAU_TO_URGENCY = {"rouge": 2, "orange": 3, "vert": 5}
NIVEAU_TO_PRIORITY = {"rouge": 2, "orange": 3, "vert": 5}


class GLPIClient:
    def __init__(self):
        if not all([GLPI_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN]):
            raise EnvironmentError(
                "Variables manquantes: GLPI_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN"
            )
        self.base = GLPI_URL.rstrip("/")
        self.session_token = None

    def init_session(self):
        resp = requests.get(
            f"{self.base}/apirest.php/initSession",
            headers={
                "App-Token":        GLPI_APP_TOKEN,
                "Authorization":    f"user_token {GLPI_USER_TOKEN}",
                "Content-Type":     "application/json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        self.session_token = resp.json()["session_token"]

    def kill_session(self):
        if self.session_token:
            requests.get(
                f"{self.base}/apirest.php/killSession",
                headers=self._headers(),
                timeout=5,
            )

    def _headers(self):
        return {
            "App-Token":     GLPI_APP_TOKEN,
            "Session-Token": self.session_token,
            "Content-Type":  "application/json",
        }

    def create_ticket(self, titre: str, contenu: str, urgence: int = 3, impact: int = 3) -> int:
        payload = {
            "input": {
                "name":     titre,
                "content":  contenu,
                "urgency":  urgence,
                "impact":   impact,
                "priority": urgence,
                "type":     1,       # 1=Incident, 2=Demande
                "itilcategories_id": 0,
            }
        }
        resp = requests.post(
            f"{self.base}/apirest.php/Ticket",
            headers=self._headers(),
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        ticket_id = resp.json()["id"]
        return ticket_id


def create_ticket(alert: dict) -> str:
    """
    Crée un ticket GLPI à partir d'une alerte cr_alerts.
    Retourne le ticket_id (str) ou raise en cas d'erreur.
    """
    niveau  = alert.get("niveau", "vert")
    message = alert.get("message", "Alerte corrosion")
    run_id  = alert.get("run_id", "?")

    titre   = f"[CORROSION] {niveau.upper()} — Run {str(run_id)[:8]}"
    contenu = (
        f"<b>Alerte maintenance prédictive — Sonde ER</b><br><br>"
        f"Niveau    : {niveau.upper()}<br>"
        f"Run ID    : {run_id}<br>"
        f"Message   : {message}<br><br>"
        f"Action recommandée : {'Intervention urgente' if niveau == 'rouge' else 'Planifier inspection'}<br>"
        f"Système   : Pipeline Corrosion ML — ESTL Douala"
    )

    client = GLPIClient()
    client.init_session()
    try:
        ticket_id = client.create_ticket(
            titre=titre,
            contenu=contenu,
            urgence=NIVEAU_TO_URGENCY.get(niveau, 3),
            impact=NIVEAU_TO_PRIORITY.get(niveau, 3),
        )
    finally:
        client.kill_session()

    return str(ticket_id)


def get_pending_alerts(run_id: str) -> list:
    """Récupère les alertes sans ticket GLPI pour un run donné."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/cr_alerts",
        headers=headers,
        params={"run_id": f"eq.{run_id}", "glpi_ticket_id": "is.null", "order": "created_at.desc"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def update_alert_ticket(alert_id: str, ticket_id: str):
    """Met à jour glpi_ticket_id dans cr_alerts."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/cr_alerts?alert_id=eq.{alert_id}",
        headers=headers,
        json={"glpi_ticket_id": ticket_id},
        timeout=10,
    ).raise_for_status()


def process_run_alerts(run_id: str):
    alerts = get_pending_alerts(run_id)
    if not alerts:
        print(f"Aucune alerte en attente pour run {run_id}")
        return

    print(f"{len(alerts)} alerte(s) à traiter...")
    for alert in alerts:
        try:
            ticket_id = create_ticket(alert)
            update_alert_ticket(alert["alert_id"], ticket_id)
            print(f"  ✓ [{alert['niveau'].upper()}] → GLPI ticket #{ticket_id}")
        except Exception as e:
            print(f"  ✗ Erreur ticket pour {alert['alert_id']}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Créer tickets GLPI depuis cr_alerts")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("ERREUR: SUPABASE_KEY non défini", file=sys.stderr)
        sys.exit(1)
    if not all([GLPI_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN]):
        print("ERREUR: GLPI_URL / GLPI_APP_TOKEN / GLPI_USER_TOKEN non définis", file=sys.stderr)
        print("  → Démo GLPI Network : https://www.glpi-network.cloud (30j gratuit)", file=sys.stderr)
        sys.exit(1)

    process_run_alerts(args.run_id)


if __name__ == "__main__":
    main()
