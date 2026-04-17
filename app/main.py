from pathlib import Path
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import db
from app.services import auth

BASE = Path(__file__).parent
STATIC_DIR = BASE / "static"
TEMPLATE_DIR = BASE / "templates"

db.init_db()

app = FastAPI(title="dhukan", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    request.state.user = auth.current_user_from_request(request)
    response: Response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; frame-ancestors 'none'"
    )

    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

from app.routers import pages, api
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
