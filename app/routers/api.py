from fastapi import APIRouter, HTTPException
from app.models.schemas import FitRequest, RiskRequest, ShopperProfile
from app.services import fit_engine, risk_engine, review_analyzer, analytics
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
async def fit_recommendation(req: FitRequest):
    result = fit_engine.recommend(req, db.get_products(), db.get_size_charts())
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result

@router.post("/return-risk")
async def return_risk(req: RiskRequest):
    products = db.get_products()
    product = next((p for p in products if p["id"] == req.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return risk_engine.compute_risk(req, product, db.get_returns(), db.get_size_charts())

@router.get("/review-summary/{product_id}")
async def review_summary(product_id: str):
    return review_analyzer.summarize(product_id, db.get_reviews())

@router.get("/dashboard-metrics")
async def dashboard_metrics():
    return analytics.get_dashboard(db.get_products(), db.get_returns(), db.get_reviews())


@router.get("/profile")
async def get_profile():
    return db.get_current_profile()


@router.post("/profile")
async def save_profile(profile: ShopperProfile):
    value = profile.model_dump()
    db.set_current_profile(value)
    return {"message": "Profile saved", "profile": value}
