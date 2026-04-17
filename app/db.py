import os
import time
import threading
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import Json
from psycopg2.pool import ThreadedConnectionPool

REQUIRED_KEYS = [
    "products",
    "reviews",
    "returns",
    "size_charts",
    "users",
    "current_profile",
]

STATIC_KEYS = {"products", "reviews", "returns", "size_charts", "users"}
STATIC_CACHE_TTL_SECONDS = 300
PROFILE_CACHE_TTL_SECONDS = 10

_POOL: ThreadedConnectionPool | None = None
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_LOCK = threading.RLock()


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required. Configure your Render PostgreSQL URL in environment variables.")
    return url


def _get_pool() -> ThreadedConnectionPool:
    global _POOL
    if _POOL is not None:
        return _POOL

    # Use a small pool since this is a single-service demo app.
    _POOL = ThreadedConnectionPool(
        minconn=1,
        maxconn=8,
        dsn=_database_url(),
    )
    return _POOL


@contextmanager
def get_conn():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


def _cache_get(key: str) -> Any | None:
    now = time.time()
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if not cached:
            return None
        expires_at, value = cached
        if expires_at < now:
            _CACHE.pop(key, None)
            return None
        return value


def _cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time() + ttl_seconds, value)


def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute("SELECT key FROM app_state")
            existing_keys = {row[0] for row in cursor.fetchall()}
        conn.commit()

    missing = [key for key in REQUIRED_KEYS if key not in existing_keys]
    if missing:
        missing_keys = ", ".join(missing)
        raise RuntimeError(
            "PostgreSQL app_state is missing required keys: "
            f"{missing_keys}. "
            "Populate app_state in the database before starting the app."
        )

    # Prime cache so first user request is fast.
    for key in STATIC_KEYS:
        _get_state(key)
    _get_state("current_profile")


def _get_state(key: str) -> Any:
    cached = _cache_get(key)
    if cached is not None:
        return cached

    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT value FROM app_state WHERE key = %s", (key,))
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Missing app_state key: {key}")
            value = row[0]

    ttl = STATIC_CACHE_TTL_SECONDS if key in STATIC_KEYS else PROFILE_CACHE_TTL_SECONDS
    _cache_set(key, value, ttl)
    return value


def _set_state(key: str, value: Any) -> None:
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO app_state (key, value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key)
                DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                """,
                (key, Json(value)),
            )
        conn.commit()

    # Keep DB authoritative and update local cache immediately after write.
    ttl = STATIC_CACHE_TTL_SECONDS if key in STATIC_KEYS else PROFILE_CACHE_TTL_SECONDS
    _cache_set(key, value, ttl)


def get_products() -> list[dict]:
    return _get_state("products")


def get_reviews() -> list[dict]:
    return _get_state("reviews")


def get_returns() -> dict[str, Any]:
    return _get_state("returns")


def get_size_charts() -> dict[str, Any]:
    return _get_state("size_charts")


def get_users() -> list[dict]:
    return _get_state("users")


def get_current_profile() -> dict[str, Any]:
    return _get_state("current_profile")


def set_current_profile(profile: dict[str, Any]) -> None:
    _set_state("current_profile", profile)
