"""
Return Risk Scoring Engine
Produces a 0-100 risk score and human-readable reasons.
"""

REASON_LABELS = {
    "tight_shoulder":   "Tight shoulder fit reported by reviewers",
    "runs_small":       "Item runs small — size mismatch likely",
    "color_mismatch":   "Product color differs from website photos",
    "waist_too_tight":  "Waist measurement tighter than size guide",
    "length_issue":     "Length/inseam inconsistent for height",
    "half_size_small":  "Shoe runs half a size small",
    "toe_box_tight":    "Toe box is narrow for wide feet",
    "narrow_fit":       "Narrow fit — wide feet at risk",
    "thin_fabric":      "Fabric thinner than shown/described",
    "sizing_unclear":   "Size chart inconsistent or misleading",
    "fit_type":         "Item fit doesn't suit all body types",
    "runs_large":       "Item runs large — may feel baggy",
    "zipper_issue":     "Zipper quality issues reported",
    "sleeve_length":    "Sleeve length shorter than expected",
    "inconsistent":     "Sizing inconsistent across the brand's range",
    "too_small":        "Selected size too small for body measurements",
    "too_large":        "Selected size too large",
    "quality":          "Material quality below expectations",
    "fading":           "Color fading reported after washing",
}

CATEGORY_BASELINE = {
    "shirts": 0.25, "jeans": 0.30, "footwear": 0.20, "dresses": 0.35, "hoodies": 0.15
}

FIT_BIAS_RISK = {
    "runs_small": 0.30, "half_size_small": 0.22, "true_to_size": 0.05, "runs_large": 0.18
}

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
SHOE_ORDER = ["6", "7", "8", "9", "10", "11", "12"]

def _size_mismatch_risk(selected_size, product, fit_bias):
    """Risk contribution from whether the selected size aligns with fit bias."""
    sizes = product.get("sizes", [])
    if not sizes or selected_size not in sizes:
        return 0.20
    idx = sizes.index(selected_size)
    middle = len(sizes) / 2
    # Choosing the smallest sizes when item runs small = higher risk
    if fit_bias == "runs_small" and idx <= 1:
        return 0.28
    if fit_bias == "runs_large" and idx >= len(sizes) - 2:
        return 0.28
    if fit_bias == "half_size_small" and idx == 0:
        return 0.22
    return 0.05


def _size_distance(selected_size, recommended_size, category):
    order = SHOE_ORDER if category == "footwear" else SIZE_ORDER
    if selected_size not in order or recommended_size not in order:
        return 0
    return abs(order.index(selected_size) - order.index(recommended_size))


def _shift_size(selected_size, category, delta):
    order = SHOE_ORDER if category == "footwear" else SIZE_ORDER
    if selected_size not in order:
        return selected_size
    idx = order.index(selected_size)
    next_idx = max(0, min(len(order) - 1, idx + delta))
    return order[next_idx]


def _in_range(value, bounds):
    return bounds[0] <= value <= bounds[1]


def _measurement_mismatch(req, category, selected_size, size_charts):
    if req.height_cm is None:
        return 0.0, None

    chart = (size_charts or {}).get(category, {})
    size_bounds = chart.get(selected_size)
    if not size_bounds:
        return 0.08, "sizing_unclear"

    if category == "footwear":
        foot_cm = req.height_cm * 0.154
        lo, hi = size_bounds["foot_cm"]
        if foot_cm < lo - 0.2:
            return 0.20, "too_small"
        if foot_cm > hi + 0.2:
            return 0.20, "too_large"
        return 0.02, None

    penalties = 0.0
    if "height_cm" in size_bounds:
        if not _in_range(req.height_cm, size_bounds["height_cm"]):
            penalties += 0.08

    if req.weight_kg is not None and "weight_kg" in size_bounds:
        if not _in_range(req.weight_kg, size_bounds["weight_kg"]):
            penalties += 0.10

    if penalties >= 0.16:
        if req.weight_kg is not None and "weight_kg" in size_bounds and req.weight_kg > size_bounds["weight_kg"][1]:
            return penalties, "too_small"
        return penalties, "too_large"
    return penalties, None

def _body_mismatch_risk(body_type, fit_pref, category):
    risky = {
        ("pear", "jeans"): 0.15, ("broad", "shirts"): 0.12,
        ("petite", "dresses"): 0.08, ("athletic", "shirts"): 0.10,
    }
    risk = risky.get((body_type, category), 0.0)
    if fit_pref == "slim" and body_type in ["broad", "athletic"]:
        risk += 0.05
    if fit_pref == "loose" and category in ["hoodies", "dresses"]:
        risk += 0.03
    return risk

def _sku_return_rate(product_id, selected_size, returns):
    sku = returns.get(product_id, {}).get(selected_size, {})
    return sku.get("return_rate", 0.0), sku.get("reasons", [])


def _reason_score_bucket(product, sku_reasons, fit_bias, mismatch_reason, size_risk, body_risk):
    reason_scores = {}

    # Product and SKU evidence from historical data.
    for idx, code in enumerate(product.get("avg_return_reasons", [])):
        reason_scores[code] = reason_scores.get(code, 0.0) + max(0.0, 0.14 - idx * 0.02)

    for idx, code in enumerate(sku_reasons):
        reason_scores[code] = reason_scores.get(code, 0.0) + max(0.0, 0.16 - idx * 0.03)

    if fit_bias in ["runs_small", "runs_large", "half_size_small"]:
        reason_scores[fit_bias] = reason_scores.get(fit_bias, 0.0) + 0.11

    if mismatch_reason:
        reason_scores[mismatch_reason] = reason_scores.get(mismatch_reason, 0.0) + 0.13

    if size_risk >= 0.22 and fit_bias == "runs_small":
        reason_scores["too_small"] = reason_scores.get("too_small", 0.0) + 0.10
    if size_risk >= 0.22 and fit_bias == "runs_large":
        reason_scores["too_large"] = reason_scores.get("too_large", 0.0) + 0.10

    if body_risk >= 0.12:
        reason_scores["fit_type"] = reason_scores.get("fit_type", 0.0) + 0.08

    ranked = sorted(reason_scores.items(), key=lambda x: x[1], reverse=True)
    top_codes = [code for code, _ in ranked[:3]]
    return [REASON_LABELS.get(code, code.replace("_", " ").title()) for code in top_codes]

def compute_risk(req, product, returns, size_charts=None):
    category = product.get("category", "shirts")
    fit_bias = product.get("fit_bias", "true_to_size")
    hist_rate = product.get("historical_return_rate", 0.20)
    cat_base = CATEGORY_BASELINE.get(category, 0.25)

    sku_rate, sku_reasons = _sku_return_rate(req.product_id, req.selected_size, returns)
    bias_risk = FIT_BIAS_RISK.get(fit_bias, 0.05)
    size_risk = _size_mismatch_risk(req.selected_size, product, fit_bias)
    body_risk = _body_mismatch_risk(req.body_type or "regular", req.fit_preference or "regular", category)
    measurement_risk, mismatch_reason = _measurement_mismatch(req, category, req.selected_size, size_charts)

    # Build an internal recommended direction from known fit bias to compare with selected size.
    recommended_size = req.selected_size
    if fit_bias in ["runs_small", "half_size_small"]:
        recommended_size = _shift_size(req.selected_size, category, 1)
    elif fit_bias == "runs_large":
        recommended_size = _shift_size(req.selected_size, category, -1)

    distance = _size_distance(req.selected_size, recommended_size, category)
    distance_risk = min(0.16, distance * 0.08)

    # weighted composite
    score_raw = (
        hist_rate * 0.24 +
        sku_rate * 0.28 +
        bias_risk * 0.18 +
        size_risk * 0.12 +
        measurement_risk * 0.10 +
        distance_risk * 0.05 +
        cat_base * 0.02 +
        body_risk * 0.01
    )
    score = min(99, max(5, int(score_raw * 230)))

    band = "low" if score < 34 else ("medium" if score < 67 else "high")

    top_reasons = _reason_score_bucket(product, sku_reasons, fit_bias, mismatch_reason, size_risk, body_risk)

    # recommended action
    if band == "high":
        sizes = product.get("sizes", [])
        if req.selected_size in sizes:
            idx = sizes.index(req.selected_size)
            if fit_bias == "runs_small" and idx < len(sizes) - 1:
                action = f"Consider sizing up to {sizes[idx + 1]} — most similar shoppers had fewer returns with a larger size."
            elif fit_bias == "runs_large" and idx > 0:
                action = f"Consider sizing down to {sizes[idx - 1]} — this item runs large."
            elif mismatch_reason == "too_small" and idx < len(sizes) - 1:
                action = f"Your measurements suggest this may fit tight. Try {sizes[idx + 1]} and verify against the size chart."
            elif mismatch_reason == "too_large" and idx > 0:
                action = f"Your measurements suggest this may run loose. Try {sizes[idx - 1]} for a safer fit."
            else:
                action = "Review the size chart carefully and compare against your measurements before ordering."
        else:
            action = "This size is unavailable. Check alternate sizes."
    elif band == "medium":
        action = "Check the size guide and read recent reviews before confirming your size."
    else:
        action = "You're in good shape! This selection has a low return probability."

    explanation = (
        f"This product has a historical return rate of {int(hist_rate*100)}%. "
        f"SKU-level return rate for size {req.selected_size} is {int(sku_rate*100)}%, and fit bias is {fit_bias.replace('_', ' ')}. "
        f"Rule-based factors used: historical returns, SKU return trend, size/fit bias alignment, measurement mismatch, and body-type fit profile."
    )

    return dict(score=score, band=band, top_reasons=top_reasons,
                recommended_action=action, explanation=explanation)
