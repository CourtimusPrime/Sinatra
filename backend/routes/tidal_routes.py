# backend/routes/tidal-routes.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/login", tags=["Tidal"], summary="Logs in for tidal")
def tidal_login():
    return {"message": "Tidal login coming soon"}