from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
import app.main as state
from app import db

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return state.templates.TemplateResponse("landing.html", {
        "request": request,
    })


@router.get("/store", response_class=HTMLResponse)
async def store_page(request: Request, category: str | None = Query(default=None)):
    all_products = db.get_products()
    categories = sorted({
        str(p.get("category", "")).strip().lower()
        for p in all_products
        if str(p.get("category", "")).strip()
    })

    products = all_products
    selected_category = (category or "").strip().lower()
    if selected_category:
        products = [
            p for p in products
            if str(p.get("category", "")).strip().lower() == selected_category
        ]

    return state.templates.TemplateResponse("store.html", {
        "request": request,
        "products": products,
        "categories": categories,
        "selected_category": selected_category,
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
