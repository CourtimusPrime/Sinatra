# services/vercel.py
import logging
import os

import requests

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT = os.getenv("VERCEL_PROJECT")
VERCEL_TEAM = os.getenv("VERCEL_TEAM")


def get_vercel_status():
    base_url = "https://api.vercel.com"
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}

    try:
        deployments_url = (
            f"{base_url}/v6/deployments?projectId={VERCEL_PROJECT}&teamId={VERCEL_TEAM}&limit=1"
        )
        res = requests.get(deployments_url, headers=headers)
        res.raise_for_status()
        deployments = res.json().get("deployments", [])

        if not deployments:
            return {"vercel": "no deployments"}

        latest = deployments[0]
        deployment_id = latest["uid"]
        detail_url = f"{base_url}/v13/deployments/{deployment_id}?teamId={VERCEL_TEAM}"
        detail_res = requests.get(detail_url, headers=headers)
        detail_res.raise_for_status()
        long_state = detail_res.json().get("readyState")

        logs_url = f"{base_url}/v2/deployments/{deployment_id}/events?teamId={VERCEL_TEAM}&limit=5"
        logs_res = requests.get(logs_url, headers=headers)
        logs = logs_res.json().get("events", [])

        return {
            "vercel": long_state,
            "deploymentUrl": f"https://{latest['url']}",
            "shortState": latest["state"],
            "logs": logs,
        }

    except Exception:
        logging.exception("❌ Error fetching Vercel status")
        return {"vercel": "error", "detail": "Failed to fetch deployment status"}
