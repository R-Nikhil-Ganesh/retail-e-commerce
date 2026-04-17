from pydantic import BaseModel, Field
from typing import Optional, List
from typing import Literal


class ShopperProfile(BaseModel):
    name: str = Field(default="Demo Shopper", min_length=1, max_length=60)
    height_cm: float = Field(ge=120, le=240)
    weight_kg: float = Field(ge=25, le=250)
    body_type: Literal["athletic", "pear", "broad", "petite", "regular"] = "regular"
    usual_size: str = Field(default="M", min_length=1, max_length=8)
    fit_preference: Literal["slim", "regular", "loose"] = "regular"
    gender: Literal["unisex", "men", "women"] = "unisex"

class FitRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=20)
    height_cm: float = Field(ge=120, le=240)
    weight_kg: float = Field(ge=25, le=250)
    body_type: Literal["athletic", "pear", "broad", "petite", "regular"] = "regular"  # athletic / pear / broad / petite / regular
    usual_brand_size: str = Field(default="M", min_length=1, max_length=8)
    fit_preference: Literal["slim", "regular", "loose"] = "regular"  # slim / regular / loose
    gender: Literal["unisex", "men", "women"] = "unisex"

class FitResponse(BaseModel):
    recommended_size: str
    confidence: int
    explanation: str
    fit_insights: List[str]
    alternate_size: Optional[str] = None
    warning: Optional[str] = None

class RiskRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=20)
    selected_size: str = Field(min_length=1, max_length=8)
    height_cm: Optional[float] = Field(default=None, ge=120, le=240)
    weight_kg: Optional[float] = Field(default=None, ge=25, le=250)
    body_type: Optional[Literal["athletic", "pear", "broad", "petite", "regular"]] = None
    fit_preference: Optional[Literal["slim", "regular", "loose"]] = "regular"

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
