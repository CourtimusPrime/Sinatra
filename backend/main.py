# backend/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routes import router as platform_router
from backend.routes import spotify_routes as spotify
from backend.routes import user

app = FastAPI(
    title="Sinatra",
    description="A cross-platform music sharing and streaming API",
    version="2.0.1",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc UI
)

app.include_router(platform_router)
app.include_router(user.router, prefix="/api/user")
app.include_router(spotify.router, prefix="/api/spotify")

app.mount("/static/js", StaticFiles(directory="frontend/js"), name="frontend-js")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index(): return FileResponse("frontend/index.html")

@app.get("/login-page")
def serve_login(): return FileResponse("frontend/login.html")

@app.get("/onboard")
def serve_onboard(): return FileResponse("frontend/onboard.html")

@app.get("/home")
def serve_home(): return FileResponse("frontend/home.html")

@app.get("/my-playlists")
def serve_my_playlists(): return FileResponse("frontend/my-playlists.html")