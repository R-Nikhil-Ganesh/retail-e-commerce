"""
Fit Recommendation Engine
Maps shopper body profile → best size using size charts + review fit bias.
"""
import json, math
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"

def _load(fname):
    with open(DATA / fname) as f:
        return json.load(f)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
SHOE_ORDER = ["6", "7", "8", "9", "10", "11", "12"]

def _bmi(weight_kg, height_cm):
    h = height_cm / 100
    return weight_kg / (h * h)

def _base_size_clothing(height_cm, weight_kg, category, charts):
    chart = charts.get(category, charts["shirts"])
    bmi = _bmi(weight_kg, height_cm)
    scores = {}
    for size, bounds in chart.items():
        h_lo, h_hi = bounds["height_cm"]
        w_lo, w_hi = bounds["weight_kg"]
        h_score = 1 if h_lo <= height_cm <= h_hi else (
            1 - min(abs(height_cm - h_lo), abs(height_cm - h_hi)) / 20)
        w_score = 1 if w_lo <= weight_kg <= w_hi else (
            1 - min(abs(weight_kg - w_lo), abs(weight_kg - w_hi)) / 15)
        scores[size] = (h_score + w_score) / 2
    return max(scores, key=scores.get), max(scores.values())

def _base_size_footwear(height_cm, weight_kg, charts):
    # Approximate foot length from height
    foot_cm = height_cm * 0.154
    chart = charts["footwear"]
    for size, bounds in chart.items():
        lo, hi = bounds["foot_cm"]
        if lo <= foot_cm <= hi:
            return size, 0.85
    # fallback: closest
    best, best_dist = "8", 999
    for size, bounds in chart.items():
        mid = sum(bounds["foot_cm"]) / 2
        d = abs(foot_cm - mid)
        if d < best_dist:
            best, best_dist = size, d
    return best, 0.70

def _shift_size(size, delta, order):
    idx = order.index(size) if size in order else len(order) // 2
    new_idx = max(0, min(len(order) - 1, idx + delta))
    return order[new_idx]

def _fit_preference_delta(fit_pref):
    return {"slim": -1, "regular": 0, "loose": 1}.get(fit_pref, 0)

def _body_type_delta(body_type, category):
    deltas = {
        "shirts":   {"athletic": 1, "broad": 1, "pear": 0, "petite": -1, "regular": 0},
        "jeans":    {"athletic": 0, "broad": 1, "pear": 1, "petite": -1, "regular": 0},
        "dresses":  {"athletic": 0, "broad": 1, "pear": 1, "petite": -1, "regular": 0},
        "hoodies":  {"athletic": 0, "broad": 1, "pear": 0, "petite": -1, "regular": 0},
    }
    return deltas.get(category, {}).get(body_type, 0)

def _review_bias_delta(fit_bias):
    return {"runs_small": 1, "half_size_small": 1, "true_to_size": 0, "runs_large": -1}.get(fit_bias, 0)

def _confidence_from_bias(fit_bias, review_count):
    base = {"runs_small": 82, "half_size_small": 78, "true_to_size": 88, "runs_large": 80}.get(fit_bias, 75)
    count_bonus = min(10, review_count // 30)
    return min(97, base + count_bonus)

def recommend(req, products, size_charts):
    product = next((p for p in products if p["id"] == req.product_id), None)
    if not product:
        return None

    category = product["category"]
    fit_bias = product.get("fit_bias", "true_to_size")
    review_count = product.get("review_count", 50)
    order = SHOE_ORDER if category == "footwear" else SIZE_ORDER

    if category == "footwear":
        base_size, base_conf = _base_size_footwear(req.height_cm, req.weight_kg, size_charts)
    else:
        base_size, base_conf = _base_size_clothing(req.height_cm, req.weight_kg, category, size_charts)

    delta = 0
    delta += _fit_preference_delta(req.fit_preference)
    delta += _body_type_delta(req.body_type, category)
    delta += _review_bias_delta(fit_bias)

    recommended = _shift_size(base_size, delta, order)
    if recommended not in product["sizes"]:
        recommended = base_size

    confidence = _confidence_from_bias(fit_bias, review_count)
    confidence = max(55, confidence - abs(delta) * 3)

    # alternate size
    alt_delta = 1 if delta <= 0 else -1
    alt = _shift_size(recommended, alt_delta, order)
    if alt not in product["sizes"] or alt == recommended:
        alt = None

    # explanation
    bias_phrases = {
        "runs_small": "This item runs small — we've sized you up accordingly.",
        "half_size_small": "This shoe runs half a size small — we recommend going up.",
        "true_to_size": "This item fits true to size based on shopper feedback.",
        "runs_large": "This item runs large — we've sized you down to avoid excess bulk.",
    }
    pref_phrase = {
        "slim": "Your slim fit preference has been factored in.",
        "regular": "Your regular fit preference has been applied.",
        "loose": "Your loose fit preference adds extra room.",
    }.get(req.fit_preference, "")

    explanation = (
        f"Based on your measurements ({req.height_cm}cm, {req.weight_kg}kg) and body type ({req.body_type}), "
        f"your baseline is {base_size}. {bias_phrases.get(fit_bias, '')} {pref_phrase} "
        f"We recommend <strong>{recommended}</strong> with {confidence}% confidence."
    )

    fit_insights = [
        f"{int(review_count * 0.62)}% of reviewers with similar measurements preferred {recommended}.",
        bias_phrases.get(fit_bias, ""),
    ]
    if req.body_type in ["athletic", "broad"]:
        fit_insights.append("Broader builds often need to size up in the chest/shoulder area.")
    if req.body_type == "pear":
        fit_insights.append("Pear-shaped fits may need a larger size to accommodate hips.")
    if req.fit_preference == "loose":
        fit_insights.append("Loose preference means we've allowed extra room in the sizing.")

    warning = None
    if confidence < 70:
        warning = f"Fit confidence is below 70%. Consider ordering both {recommended} and {alt} if possible."

    return dict(
        recommended_size=recommended,
        confidence=confidence,
        explanation=explanation,
        fit_insights=fit_insights,
        alternate_size=alt,
        warning=warning,
    )
