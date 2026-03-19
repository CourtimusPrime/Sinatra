# core/router.py
from fastapi import FastAPI

from api import (
    admin,
    ai,
    auth,
    dashboard,
    genres,
    playback,
    playlists,
    public,
    spotify,
    system,
    user,
    vercel,
)

_ROUTERS = [
    auth.router,
    user.router,
    playlists.router,
    playback.router,
    genres.router,
    admin.router,
    system.router,
    dashboard.router,
    vercel.router,
    spotify.router,
    public.router,
    ai.router,
]


def include_routers(app: FastAPI):
    for router in _ROUTERS:
        app.include_router(router, prefix="/api")
