import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import Response

SESSION_COOKIE_NAME = "dhukan_session"
SESSION_TTL_SECONDS = 60 * 60 * 8

# Simple in-memory rate limiter for login attempts per IP.
_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
_LOGIN_WINDOW_SECONDS = 60
_LOGIN_MAX_ATTEMPTS = 12


def _env_truthy(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _signing_secret() -> str:
    # APP_SECRET is preferred. Fallback keeps local demo runnable but should be overridden in production.
    return os.getenv("APP_SECRET") or os.getenv("SECRET_KEY") or (os.getenv("DATABASE_URL", "") + "-dhukan")


def _sign(message: str) -> str:
    digest = hmac.new(
        _signing_secret().encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def create_session_token(user: dict[str, Any], client_ip: str | None = None) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user.get("name") or "shopper"),
        "role": str(user.get("role") or "customer"),
        "iat": now,
        "exp": now + SESSION_TTL_SECONDS,
    }
    if client_ip:
        payload["ip"] = client_ip

    payload_raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_part = _b64url_encode(payload_raw)
    sig_part = _sign(payload_part)
    return f"{payload_part}.{sig_part}"


def decode_session_token(token: str, client_ip: str | None = None) -> dict[str, Any] | None:
    try:
        payload_part, sig_part = token.split(".", 1)
    except ValueError:
        return None

    expected_sig = _sign(payload_part)
    if not hmac.compare_digest(sig_part, expected_sig):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except Exception:
        return None

    now = int(time.time())
    exp = int(payload.get("exp") or 0)
    if exp < now:
        return None

    bound_ip = payload.get("ip")
    if bound_ip and client_ip and bound_ip != client_ip:
        return None

    return payload


def set_session_cookie(response: Response, token: str) -> None:
    secure_cookie = _env_truthy("COOKIE_SECURE", default=False)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def current_user_from_request(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    client_ip = request.client.host if request.client else None
    payload = decode_session_token(token, client_ip=client_ip)
    if not payload:
        return None
    return {"name": payload.get("sub", "shopper"), "role": payload.get("role", "customer")}


def require_auth(request: Request) -> dict[str, Any]:
    user = getattr(request.state, "user", None) or current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def check_login_rate_limit(client_ip: str | None) -> bool:
    key = client_ip or "unknown"
    now = time.time()
    attempts = [t for t in _LOGIN_ATTEMPTS.get(key, []) if now - t < _LOGIN_WINDOW_SECONDS]
    attempts.append(now)
    _LOGIN_ATTEMPTS[key] = attempts
    return len(attempts) <= _LOGIN_MAX_ATTEMPTS
