import os
import sys
from pathlib import Path

import pytest

# Ensure backend/ is on sys.path so imports like `from core.env import ...` resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set test environment before anything reads env vars
os.environ.setdefault("NODE_ENV", "test")


@pytest.fixture()
def app():
    """Create a FastAPI test application."""
    from main import app

    return app


@pytest.fixture()
async def client(app):
    """Async test client for FastAPI endpoints."""
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
