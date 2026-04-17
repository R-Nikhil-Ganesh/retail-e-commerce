"""
Review Analyzer — keyword-based sentiment extraction + structured summarization.
LLM-ready: replace _extract_signals() with an LLM call for richer output.
"""
from collections import Counter

FIT_KEYWORDS = {
    "runs_small":  ["runs small", "too small", "size up", "sized up", "tight", "snug", "narrow"],
    "runs_large":  ["runs large", "too big", "size down", "sized down", "baggy", "oversized", "enormous"],
    "half_size_small": ["half size small", "half size down", "half a size"],
    "true_to_size": ["true to size", "fits perfectly", "fits well", "perfect fit", "right size"],
}

CONCERN_KEYWORDS = {
    "color_mismatch":  ["different color", "different shade", "color is off", "darker", "lighter", "misleading photo", "not as shown"],
    "thin_fabric":     ["thin fabric", "see-through", "transparent", "cheap material", "flimsy", "thinner than"],
    "quality":         ["quality", "cheap", "poor quality", "falls apart", "stitching"],
    "length_issue":    ["too long", "too short", "length", "inseam", "sleeve"],
    "zipper_issue":    ["zipper", "zip", "stuck"],
}

SENTIMENT_WORDS = {
    "positive": ["great", "love", "perfect", "excellent", "amazing", "comfortable", "happy", "recommend", "best", "good"],
    "negative": ["return", "disappointed", "terrible", "bad", "wrong", "hate", "waste", "horrible", "poor"],
}

def _classify_fit(text: str) -> str:
    text_l = text.lower()
    scores = {tag: sum(1 for kw in kws if kw in text_l) for tag, kws in FIT_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "true_to_size"

def _extract_concerns(text: str) -> list:
    text_l = text.lower()
    return [concern for concern, kws in CONCERN_KEYWORDS.items() if any(kw in text_l for kw in kws)]

def _sentiment(text: str) -> str:
    text_l = text.lower()
    pos = sum(1 for w in SENTIMENT_WORDS["positive"] if w in text_l)
    neg = sum(1 for w in SENTIMENT_WORDS["negative"] if w in text_l)
    if pos > neg: return "positive"
    if neg > pos: return "negative"
    return "neutral"

FIT_TAG_LABELS = {
    "runs_small":      "Runs Small",
    "runs_large":      "Runs Large",
    "half_size_small": "Half Size Small",
    "true_to_size":    "True to Size",
}

CONCERN_LABELS = {
    "color_mismatch": "Color differs from photos",
    "thin_fabric":    "Fabric thinner than expected",
    "quality":        "Material quality concerns",
    "length_issue":   "Length or inseam issues",
    "zipper_issue":   "Zipper quality problems",
}

def summarize(product_id: str, reviews: list) -> dict:
    prod_reviews = [r for r in reviews if r["product_id"] == product_id]
    if not prod_reviews:
        return {"error": "No reviews found"}

    fit_tags = [_classify_fit(r["text"]) for r in prod_reviews]
    sentiments = [_sentiment(r["text"]) for r in prod_reviews]
    concerns_flat = [c for r in prod_reviews for c in _extract_concerns(r["text"])]

    fit_counter = Counter(fit_tags)
    sentiment_counter = Counter(sentiments)
    concern_counter = Counter(concerns_flat)

    dominant_fit = fit_counter.most_common(1)[0][0]
    dominant_pct = int(fit_counter[dominant_fit] / len(fit_tags) * 100)

    top_concerns = [CONCERN_LABELS.get(c, c) for c, _ in concern_counter.most_common(3)]

    # Representative shopper quote
    best_review = max(prod_reviews, key=lambda r: len(r["text"]))
    quote = best_review["text"][:160] + ("…" if len(best_review["text"]) > 160 else "")

    fit_phrases = {
        "runs_small":      f"{dominant_pct}% of shoppers say this item runs small — size up for best fit.",
        "runs_large":      f"{dominant_pct}% of shoppers say this item runs large — consider sizing down.",
        "half_size_small": f"{dominant_pct}% of shoppers found this shoe runs half a size small.",
        "true_to_size":    f"{dominant_pct}% of shoppers say this fits true to size.",
    }

    return dict(
        fit_summary=fit_phrases.get(dominant_fit, "Sizing feedback varies across shoppers."),
        fit_tag=FIT_TAG_LABELS.get(dominant_fit, dominant_fit),
        top_concerns=top_concerns,
        sentiment_breakdown={
            "positive": sentiment_counter.get("positive", 0),
            "neutral":  sentiment_counter.get("neutral", 0),
            "negative": sentiment_counter.get("negative", 0),
        },
        shopper_quote=quote,
        total_reviews=len(prod_reviews),
    )
