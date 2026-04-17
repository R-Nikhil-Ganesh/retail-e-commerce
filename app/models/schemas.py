from pydantic import BaseModel
from typing import Optional, List


class ShopperProfile(BaseModel):
    name: str = "Demo Shopper"
    height_cm: float
    weight_kg: float
    body_type: str = "regular"
    usual_size: str = "M"
    fit_preference: str = "regular"
    gender: str = "unisex"

class FitRequest(BaseModel):
    product_id: str
    height_cm: float
    weight_kg: float
    body_type: str = "regular"          # athletic / pear / broad / petite / regular
    usual_brand_size: str = "M"
    fit_preference: str = "regular"     # slim / regular / loose
    gender: str = "unisex"

class FitResponse(BaseModel):
    recommended_size: str
    confidence: int
    explanation: str
    fit_insights: List[str]
    alternate_size: Optional[str] = None
    warning: Optional[str] = None

class RiskRequest(BaseModel):
    product_id: str
    selected_size: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_type: Optional[str] = None
    fit_preference: Optional[str] = "regular"

class RiskResponse(BaseModel):
    score: int
    band: str           # low / medium / high
    top_reasons: List[str]
    recommended_action: str
    explanation: str

class ReviewSummary(BaseModel):
    fit_summary: str
    fit_tag: str
    top_concerns: List[str]
    sentiment_breakdown: dict
    shopper_quote: str
    total_reviews: int

class ProductSummary(BaseModel):
    id: str
    title: str
    category: str
    brand: str
    price: int
    sizes: List[str]
    image: str
    avg_rating: float
    historical_return_rate: float
    risk_band: str

class DashboardMetrics(BaseModel):
    total_orders: int
    estimated_return_rate: float
    high_risk_skus: int
    reduction_potential: float
    products: List[dict]
    category_breakdown: dict
    monthly_trend: List[dict]
    top_actions: List[str]
