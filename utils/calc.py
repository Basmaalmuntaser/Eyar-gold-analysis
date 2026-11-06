"""Gold piece calculator (pure Python, no Streamlit, so it can be unit-tested).

Formulas
--------
gram price for a karat (SAR)  = ounce price (USD) x 3.75 / 31.1035 x karat / 24
lowest price                  = weight x (gram price + lowest add-on per gram)  x (1 + VAT)
highest price                 = weight x (gram price + highest add-on per gram) x (1 + VAT)

The add-on is the making charge and the shop margin together (one number, never added twice).
The weight is the NET gold weight (without stones).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import settings

MAX_WEIGHT = 10_000.0     # grams; anything above is treated as a typing error
MAX_BUDGET = 100_000_000.0
CATEGORIES = ("bangles", "other", "bar")


# ---------------------------------------------------------------------------
# Basic conversions and checks
# ---------------------------------------------------------------------------
def gram_price_from_ounce(ounce_usd: float, usd_to_sar: float, karat: int) -> float:
    return ounce_usd * usd_to_sar / settings.OUNCE_IN_GRAMS * karat / 24


def validate_weight(w) -> tuple | None:
    if w is None or (isinstance(w, float) and np.isnan(w)):
        return ("Enter the gold weight in grams.", "أدخل وزن الذهب بالجرام.")
    if w <= 0:
        return ("The weight must be greater than zero.", "الوزن يجب أن يكون أكبر من صفر.")
    if w > MAX_WEIGHT:
        return (f"The weight is above {MAX_WEIGHT:,.0f} g. Please check the number.",
                f"الوزن أكبر من {MAX_WEIGHT:,.0f} جرام. تأكد من الرقم.")
    return None


def validate_gram_price(g) -> bool:
    return g is not None and isinstance(g, (int, float)) and math.isfinite(g) and g > 0


def category_for(karat: int, piece: str, investment_bar: bool) -> str:
    """A qualified investment bar is only possible for 24K; otherwise use the chosen piece type."""
    if karat == 24 and investment_bar:
        return "bar"
    return piece if piece in ("bangles", "other") else "other"


def vat_rate(category: str) -> float:
    """15% for jewelry and other pieces; 0% for a qualified investment bar (on the assumption that it
    meets the conditions). 24K alone does not give the zero rate."""
    return settings.VAT_INVESTMENT_GOLD if category == "bar" else settings.VAT_STANDARD


# ---------------------------------------------------------------------------
# Add-ons per gram (making charge + shop margin together)
# ---------------------------------------------------------------------------
def bar_addon_high(weight: float) -> float:
    """Upper add-on per gram for a qualified bar. Smooth (linear on log-weight between the points),
    never increasing with weight, never above the cap."""
    pts = settings.BAR_ADDON_HIGH_POINTS
    if weight <= pts[0][0]:
        return min(pts[0][1], settings.BAR_ADDON_CAP)
    if weight >= pts[-1][0]:
        return min(pts[-1][1], settings.BAR_ADDON_CAP)
    lw = math.log10(weight)
    for (w0, a0), (w1, a1) in zip(pts, pts[1:]):
        if w0 <= weight <= w1:
            t = (lw - math.log10(w0)) / (math.log10(w1) - math.log10(w0))
            return min(a0 + t * (a1 - a0), settings.BAR_ADDON_CAP)
    return settings.BAR_ADDON_CAP


def addon_range(category: str, weight: float) -> tuple[float, float]:
    """(lowest, highest) add-on in SAR per gram."""
    if category == "bar":
        hi = bar_addon_high(weight)
        return hi * settings.BAR_ADDON_LOW_SHARE, hi
    return settings.ADDON_RANGES[category]


# ---------------------------------------------------------------------------
# Price estimate
# ---------------------------------------------------------------------------
def estimate(gram_price: float, weight: float, category: str) -> dict:
    lo_add, hi_add = addon_range(category, weight)
    vat = vat_rate(category)
    pre_lo = weight * (gram_price + lo_add)
    pre_hi = weight * (gram_price + hi_add)
    return {
        "gram_price": gram_price, "weight": weight, "category": category, "vat": vat,
        "addon_low": lo_add, "addon_high": hi_add,
        "gold_value": weight * gram_price,
        "pre_vat_low": pre_lo, "pre_vat_high": pre_hi,
        "low": pre_lo * (1 + vat), "high": pre_hi * (1 + vat),   # VAT applied once
    }


def total_price(gram_price: float, weight: float, category: str, which: str) -> float:
    e = estimate(gram_price, weight, category)
    return e["low"] if which == "low" else e["high"]


# ---------------------------------------------------------------------------
# Budget: how many grams can I get?
# ---------------------------------------------------------------------------
def _max_weight(budget: float, gram_price: float, category: str, which: str) -> float:
    """Largest weight whose price (with the 'low' or 'high' add-on) does not exceed the budget.
    The bar add-on depends on the weight, so we solve numerically (price grows with weight)."""
    if category != "bar":
        lo_add, hi_add = settings.ADDON_RANGES[category]
        add = lo_add if which == "low" else hi_add
        return budget / ((gram_price + add) * (1 + vat_rate(category)))
    lo, hi = 0.0, MAX_WEIGHT
    if total_price(gram_price, hi, category, which) <= budget:
        return hi
    for _ in range(80):
        mid = (lo + hi) / 2
        if total_price(gram_price, mid, category, which) <= budget:
            lo = mid
        else:
            hi = mid
    return lo


def floor_to(x: float, step: float = 0.01) -> float:
    return math.floor(x / step + 1e-9) * step


def budget_weight(budget, gram_price: float, category: str) -> dict:
    if budget is None or not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget <= 0:
        return {"ok": False, "error": ("Enter a budget greater than zero.", "أدخل ميزانية أكبر من صفر.")}
    if budget > MAX_BUDGET:
        return {"ok": False, "error": ("The budget is too large. Please check the number.", "الميزانية كبيرة جدًا. تأكد من الرقم.")}
    # fewest grams = highest add-ons; most grams = lowest add-ons. Rounded DOWN so we never exceed the budget.
    w_min = floor_to(_max_weight(budget, gram_price, category, "high"))
    w_max = floor_to(_max_weight(budget, gram_price, category, "low"))
    return {"ok": True, "low": w_min, "high": w_max, "vat": vat_rate(category)}


# ---------------------------------------------------------------------------
# Shop survey (29 Oct 2026) -- kept as project documentation; the calculator no longer uses it
# ---------------------------------------------------------------------------
SURVEY_COLUMNS = ["shop_ar", "shop_en", "city_ar", "city_en", "category", "karat", "available",
                  "fee_min_per_g", "fee_max_per_g", "profit_included", "fixed_profit_min", "fixed_profit_max",
                  "collected_on", "notes"]


def _yes(v) -> bool:
    return str(v).strip().lower() in {"yes", "true", "1", "نعم", "y"}


def _num(v):
    v = str(v).strip()
    return float(v) if v else None


def load_survey(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """One row per shop and category. Invalid rows are skipped with a message."""
    msgs: list[str] = []
    if not Path(path).exists():
        return pd.DataFrame(columns=SURVEY_COLUMNS), [f"missing file: {Path(path).name}"]
    raw = pd.read_csv(path, dtype=str).fillna("")
    for col in SURVEY_COLUMNS:
        if col not in raw.columns:
            raw[col] = ""
    rows = []
    for i, r in raw.iterrows():
        available = _yes(r["available"])
        try:
            lo, hi = _num(r["fee_min_per_g"]), _num(r["fee_max_per_g"])
            flo, fhi = _num(r["fixed_profit_min"]), _num(r["fixed_profit_max"])
            karat = int(float(r["karat"])) if r["karat"].strip() else None
        except ValueError:
            msgs.append(f"row {i + 2} skipped: numbers are not valid")
            continue
        if available and (lo is None or hi is None):
            msgs.append(f"row {i + 2} skipped: missing fee")
            continue
        if available and (lo < 0 or hi < 0):
            msgs.append(f"row {i + 2} skipped: negative fee")
            continue
        if lo is not None and hi is not None and lo > hi:
            lo, hi = hi, lo
        included = _yes(r["profit_included"])
        flo, fhi = (0.0, 0.0) if included else (flo or 0.0, fhi or 0.0)
        if flo > fhi:
            flo, fhi = fhi, flo
        rows.append({
            "shop_ar": r["shop_ar"].strip(), "shop_en": r["shop_en"].strip() or r["shop_ar"].strip(),
            "city_ar": r["city_ar"].strip(), "city_en": r["city_en"].strip() or r["city_ar"].strip(),
            "category": r["category"].strip(), "karat": karat, "karat_specified": karat is not None,
            "available": available, "fee_min_per_g": lo or 0.0, "fee_max_per_g": hi or 0.0,
            "profit_included": included, "fixed_profit_min": flo, "fixed_profit_max": fhi,
            "collected_on": r["collected_on"].strip(), "notes": r["notes"].strip(),
        })
    return pd.DataFrame(rows), msgs


