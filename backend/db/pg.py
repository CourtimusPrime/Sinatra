# db/pg.py
import os
from contextlib import contextmanager
from functools import lru_cache

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


@lru_cache
def get_pool() -> ConnectionPool:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return ConnectionPool(url, min_size=2, max_size=10, kwargs={"row_factory": dict_row})


@contextmanager
def get_conn():
    with get_pool().connection() as conn:
        yield conn


def check_connection() -> bool:
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
