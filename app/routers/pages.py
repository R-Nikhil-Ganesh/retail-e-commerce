from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import app.main as state
from app import db

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def login_root(request: Request):
    return state.templates.TemplateResponse("login.html", {
        "request": request,
        "users": db.get_users(),
    })


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return state.templates.TemplateResponse("login.html", {
        "request": request,
        "users": db.get_users(),
    })

@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(request: Request, product_id: str):
    products = db.get_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)
    prod_reviews = [r for r in db.get_reviews() if r["product_id"] == product_id]
    return state.templates.TemplateResponse("product.html", {
        "request": request,
        "product": product,
        "reviews": prod_reviews,
        "profile": db.get_current_profile(),
        "all_products": products,
    })


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return state.templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": db.get_current_profile(),
        "users": db.get_users(),
    })

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return state.templates.TemplateResponse("dashboard.html", {
        "request": request,
        "products": db.get_products(),
    })
