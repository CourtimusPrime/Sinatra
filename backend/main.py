# main.py
import sys
from contextlib import asynccontextmanager

sys.stdout.reconfigure(encoding="utf-8")

from core.env import load_env  # noqa: E402

load_env()  # Must run before importing anything that depends on env vars

from fastapi import FastAPI  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

from core.middleware import add_cors_middleware  # noqa: E402
from core.rate_limit import limiter  # noqa: E402
from core.router import include_routers  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.queries import ensure_sessions_table

    ensure_sessions_table()
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
add_cors_middleware(app)
include_routers(app)
