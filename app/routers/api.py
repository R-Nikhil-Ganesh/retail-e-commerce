from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from app.models.schemas import FitRequest, RiskRequest, ShopperProfile
from app.services import fit_engine, risk_engine, review_analyzer, analytics
from app.services import auth
from app import db

router = APIRouter()

@router.get("/products")
async def get_products():
    return db.get_products()

@router.get("/product/{product_id}")
async def get_product(product_id: str):
    p = next((p for p in db.get_products() if p["id"] == product_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

@router.post("/fit-recommendation")
async def fit_recommendation(req: FitRequest, _user: dict = Depends(auth.require_auth)):
    result = fit_engine.recommend(req, db.get_products(), db.get_size_charts())
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result

@router.post("/return-risk")
async def return_risk(req: RiskRequest, _user: dict = Depends(auth.require_auth)):
    products = db.get_products()
    product = next((p for p in products if p["id"] == req.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return risk_engine.compute_risk(req, product, db.get_returns(), db.get_size_charts())

@router.get("/review-summary/{product_id}")
async def review_summary(product_id: str, _user: dict = Depends(auth.require_auth)):
    return review_analyzer.summarize(product_id, db.get_reviews())

@router.get("/dashboard-metrics")
async def dashboard_metrics(_user: dict = Depends(auth.require_auth)):
    return analytics.get_dashboard(db.get_products(), db.get_returns(), db.get_reviews())


@router.get("/profile")
async def get_profile(_user: dict = Depends(auth.require_auth)):
    return db.get_current_profile()


@router.post("/profile")
async def save_profile(profile: ShopperProfile, _user: dict = Depends(auth.require_auth)):
    value = profile.model_dump()
    db.set_current_profile(value)
    return {"message": "Profile saved", "profile": value}


@router.post("/auth/login")
async def login(request: Request, response: Response, profile: ShopperProfile):
    client_ip = request.client.host if request.client else None
    if not auth.check_login_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a minute and try again.",
        )

    name = profile.name.strip()
    if not name or len(name) > 60:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid profile name")

    value = profile.model_dump()
    value["name"] = name
    db.set_current_profile(value)

    token = auth.create_session_token({"name": name, "role": "customer"}, client_ip=client_ip)
    auth.set_session_cookie(response, token)
    return {"message": "Logged in", "user": {"name": name, "role": "customer"}}


@router.post("/auth/logout")
async def logout(response: Response):
    auth.clear_session_cookie(response)
    return {"message": "Logged out"}


@router.get("/auth/me")
async def me(user: dict = Depends(auth.require_auth)):
    return {"user": user}
