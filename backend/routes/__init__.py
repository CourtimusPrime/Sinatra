# backend/routes/__init__.py

from fastapi import APIRouter
from backend.routes.spotify_routes import router as spotify_router
from backend.routes.user_routes import router as user_router
from backend.routes.genre_routes import router as genre_router

router = APIRouter()
router.include_router(spotify_router)
router.include_router(user_router)
router.include_router(genre_router)
