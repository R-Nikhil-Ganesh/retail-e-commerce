from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import db

BASE = Path(__file__).parent
STATIC_DIR = BASE / "static"
TEMPLATE_DIR = BASE / "templates"

db.init_db()

app = FastAPI(title="dhukan", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

from app.routers import pages, api
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
