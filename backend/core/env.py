# backend/core/env.py
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    """Load environment variables from the repo root .env file."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)
