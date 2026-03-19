# core/middleware.py

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI):
    origins = [
        "http://localhost:5173",
        "https://sinatra.live",
        "https://sinatra.vercel.app",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Admin-Secret"],
        expose_headers=["set-cookie"],
    )
