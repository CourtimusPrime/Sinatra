# main.py
import sys

sys.stdout.reconfigure(encoding="utf-8")

from core.env import load_env  # noqa: E402

load_env()  # Must run before importing anything that depends on env vars

from fastapi import FastAPI  # noqa: E402

from core.middleware import add_cors_middleware  # noqa: E402
from core.router import include_routers  # noqa: E402

app = FastAPI()
add_cors_middleware(app)
include_routers(app)
