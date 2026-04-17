from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
import app.main as state
from app import db
from app.services import auth
from urllib.parse import quote
from fastapi.responses import RedirectResponse

router = APIRouter()


def _redirect_to_login(next_path: str = "/login"):
    safe_next = quote(next_path, safe="/?=&")
    return RedirectResponse(url=f"/login?next={safe_next}", status_code=303)


def _require_user_or_redirect(request: Request):
    user = getattr(request.state, "user", None)
    if user:
        return user
    next_path = str(request.url.path)
    if request.url.query:
        next_path = f"{next_path}?{request.url.query}"
    return _redirect_to_login(next_path)

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return state.templates.TemplateResponse("landing.html", {
        "request": request,
    })


@router.get("/store", response_class=HTMLResponse)
async def store_page(request: Request, category: str | None = Query(default=None)):
    guard = _require_user_or_redirect(request)
    if isinstance(guard, RedirectResponse):
        return guard

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
    if getattr(request.state, "user", None):
        return RedirectResponse(url="/store", status_code=303)

    return state.templates.TemplateResponse("login.html", {
        "request": request,
        "users": db.get_users(),
        "next_path": request.query_params.get("next", "/store"),
    })

@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(request: Request, product_id: str):
    guard = _require_user_or_redirect(request)
    if isinstance(guard, RedirectResponse):
        return guard

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
    guard = _require_user_or_redirect(request)
    if isinstance(guard, RedirectResponse):
        return guard

    return state.templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": db.get_current_profile(),
        "users": db.get_users(),
    })

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    guard = _require_user_or_redirect(request)
    if isinstance(guard, RedirectResponse):
        return guard

    return state.templates.TemplateResponse("dashboard.html", {
        "request": request,
        "products": db.get_products(),
    })
