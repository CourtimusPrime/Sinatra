# api/vercel.py
from fastapi import APIRouter

from services.vercel import get_vercel_status

router = APIRouter(tags=["vercel"])


@router.get("/vercel-status")
def vercel_status():
    return get_vercel_status()
