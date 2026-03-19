# api/vercel.py
import logging
import os

import requests
from fastapi import APIRouter

router = APIRouter(tags=["vercel"])

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT = os.getenv("VERCEL_PROJECT")
VERCEL_TEAM = os.getenv("VERCEL_TEAM")


@router.get("/vercel-status")
def get_vercel_status():
    base_url = "https://api.vercel.com"
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}

    try:
        deployments_url = (
            f"{base_url}/v6/deployments?projectId={VERCEL_PROJECT}&teamId={VERCEL_TEAM}&limit=1"
        )
        deployments_res = requests.get(deployments_url, headers=headers)
        deployments_res.raise_for_status()
        deployments_data = deployments_res.json()

        if not deployments_data.get("deployments"):
            return {"vercel": "no deployments"}

        latest = deployments_data["deployments"][0]
        deployment_id = latest["uid"]
        deployment_url = latest["url"]
        short_state = latest["state"]

        detail_url = f"{base_url}/v13/deployments/{deployment_id}?teamId={VERCEL_TEAM}"
        detail_res = requests.get(detail_url, headers=headers)
        detail_res.raise_for_status()
        long_state = detail_res.json().get("readyState")

        logs_url = f"{base_url}/v2/deployments/{deployment_id}/events?teamId={VERCEL_TEAM}&limit=5"
        logs_res = requests.get(logs_url, headers=headers)
        logs = logs_res.json().get("events", [])

        return {
            "vercel": long_state,
            "deploymentUrl": f"https://{deployment_url}",
            "shortState": short_state,
            "logs": logs,
        }

    except Exception as e:
        logging.exception("❌ Error fetching Vercel deployment status")
        return {"vercel": "error", "detail": str(e)}
