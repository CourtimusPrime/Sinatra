# core/router.py
from fastapi import FastAPI

from api import (
    admin,
    ai,
    auth,
    cookie,
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


def include_routers(app: FastAPI):
    app.include_router(auth.router)
    app.include_router(user.router)
    app.include_router(playlists.router)
    app.include_router(playback.router)
    app.include_router(genres.router)
    app.include_router(admin.router)
    app.include_router(system.router)
    app.include_router(dashboard.router)
    app.include_router(cookie.router)
    app.include_router(vercel.router)
    app.include_router(spotify.router)
    app.include_router(public.router)
    app.include_router(ai.router)
