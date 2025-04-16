# backend/routes/__init__.py

from fastapi import APIRouter
from .spotify import router as spotify_router
from .user import router as user_router
from .platform import router as platform_router
from .genres import router as genres_router
# from .tidal import router as tidal_router  # if/when needed

router = APIRouter()
router.include_router(spotify_router, prefix="/api/spotify")
router.include_router(user_router, prefix="/api/user")
router.include_router(platform_router, prefix="/api/platform")
router.include_router(genres_router, prefix="/api/genres")
# router.include_router(tidal_router, prefix="/api/tidal")