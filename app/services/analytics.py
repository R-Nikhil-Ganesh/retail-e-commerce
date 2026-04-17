"""
Analytics Service — aggregates metrics for the retailer dashboard.
"""
import random

RISK_THRESHOLDS = {"low": (0, 33), "medium": (34, 66), "high": (67, 100)}

def _rate_to_score(rate: float) -> int:
    """Convert historical return rate to a 0-100 risk score (simplified)."""
    return min(98, int(rate * 220))

def _band(score: int) -> str:
    if score < 34: return "low"
    if score < 67: return "medium"
    return "high"

def _top_reasons(product: dict) -> list:
    reason_map = {
        "tight_shoulder": "Tight shoulder fit", "runs_small": "Runs small",
        "color_mismatch": "Color mismatch", "waist_too_tight": "Waist too tight",
        "length_issue": "Length issues", "half_size_small": "Half size small",
        "toe_box_tight": "Tight toe box", "thin_fabric": "Thin fabric",
        "sizing_unclear": "Unclear sizing", "runs_large": "Runs large",
        "zipper_issue": "Zipper quality", "narrow_fit": "Narrow fit",
    }
    return [reason_map.get(r, r) for r in product.get("avg_return_reasons", [])[:2]]

def _suggested_action(product: dict) -> str:
    reasons = product.get("avg_return_reasons", [])
    if "color_mismatch" in reasons:
        return "Update product photography to match actual colors"
    if "sizing_unclear" in reasons or "runs_small" in reasons:
        return "Improve size guide with actual measurements"
    if "thin_fabric" in reasons or "quality" in reasons:
        return "Revise product description to set accurate material expectations"
    if "runs_large" in reasons:
        return "Add prominent 'Size Down' advisory to product listing"
    return "Monitor return feedback and update listing copy"

def get_dashboard(products: list, returns: dict, reviews: list) -> dict:
    random.seed(42)  # deterministic demo data

    product_rows = []
    total_return_value = 0
    high_risk_count = 0

    for p in products:
        score = _rate_to_score(p["historical_return_rate"])
        band = _band(score)
        if band == "high":
            high_risk_count += 1
        # simulated orders for demo
        orders = random.randint(280, 950)
        returns_count = int(orders * p["historical_return_rate"])
        total_return_value += returns_count * p["price"]

        product_rows.append({
            "id": p["id"],
            "title": p["title"],
            "brand": p["brand"],
            "category": p["category"],
            "risk_score": score,
            "risk_band": band,
            "return_rate": round(p["historical_return_rate"] * 100, 1),
            "top_reasons": _top_reasons(p),
            "suggested_action": _suggested_action(p),
            "orders": orders,
            "returns": returns_count,
            "avg_rating": p["avg_rating"],
            "price": p["price"],
        })

    product_rows.sort(key=lambda x: x["risk_score"], reverse=True)

    total_orders = sum(r["orders"] for r in product_rows)
    total_returns = sum(r["returns"] for r in product_rows)
    overall_rate = round(total_returns / total_orders * 100, 1) if total_orders else 0
    reduction_potential = round(overall_rate * 0.38, 1)  # ~38% reducible with AI

    # category breakdown
    cat_map = {}
    for r in product_rows:
        cat = r["category"]
        cat_map.setdefault(cat, {"orders": 0, "returns": 0})
        cat_map[cat]["orders"] += r["orders"]
        cat_map[cat]["returns"] += r["returns"]
    category_breakdown = {
        cat: round(v["returns"] / v["orders"] * 100, 1)
        for cat, v in cat_map.items()
    }

    # synthetic monthly trend (last 6 months)
    base = overall_rate
    monthly_trend = []
    for i in range(6, 0, -1):
        import datetime
        month = (datetime.date.today().replace(day=1) -
                 datetime.timedelta(days=30 * (i - 1))).strftime("%b %Y")
        jitter = random.uniform(-2.5, 2.5)
        ai_rate = max(1, base - (6 - i) * 0.6 + jitter * 0.3)
        monthly_trend.append({
            "month": month,
            "return_rate": round(base + jitter, 1),
            "ai_projected": round(ai_rate, 1),
        })

    top_actions = [
        "Add 'Runs Small — Size Up' banner to Men's Oxford Shirt listing",
        "Re-photograph Summer Floral Dress to accurately represent colors",
        "Update size guide for Women's Denim Jeans with waist measurements",
        "Add wide-foot advisory to CloudRun Pro Running Shoes PDP",
        "Flag Fleece Zip Hoodie XXL as high-return-risk in inventory",
    ]

    return dict(
        total_orders=total_orders,
        estimated_return_rate=overall_rate,
        high_risk_skus=high_risk_count,
        reduction_potential=reduction_potential,
        products=product_rows,
        category_breakdown=category_breakdown,
        monthly_trend=monthly_trend,
        top_actions=top_actions,
    )
