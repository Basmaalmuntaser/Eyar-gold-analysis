"""Gold piece calculator (pure Python/pandas, no Streamlit, so it can be unit-tested).

Formulas
--------
gram price for a karat (SAR) = ounce price (USD) x USD->SAR rate / 31.1035 x karat / 24
gold weight                  = piece weight - stones weight   (only if the entered weight includes stones)
metal value                  = gram price x gold weight
extras (from the shop survey)= making charge (+ shop margin, only if the survey says it is NOT inside the making charge)
subtotal                     = metal value + extras + stones value (if known)
VAT                          = subtotal x VAT rate (applied once)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import settings

MAX_WEIGHT = 10_000.0  # grams; anything above is treated as a typing error



# ---------------------------------------------------------------------------
# Basic conversions
# ---------------------------------------------------------------------------
def gram_price_from_ounce(ounce_usd: float, usd_to_sar: float, karat: int) -> float:
    return ounce_usd * usd_to_sar / settings.OUNCE_IN_GRAMS * karat / 24


def vat_rate(case: str) -> float | None:
    if case == "jewelry":
        return settings.VAT_STANDARD
    if case == "investment":
        return settings.VAT_INVESTMENT_GOLD
    return None  # unknown: we do not show a confirmed taxed total


def validate_weight(w) -> str | None:
    if w is None or (isinstance(w, float) and np.isnan(w)):
        return ("Enter the piece weight in grams.", "أدخلي وزن القطعة بالجرام.")
    if w <= 0:
        return ("The weight must be greater than zero.", "الوزن يجب أن يكون أكبر من صفر.")
    if w > MAX_WEIGHT:
        return (f"The weight is above {MAX_WEIGHT:,.0f} g. Please check the number.", f"الوزن أكبر من {MAX_WEIGHT:,.0f} جرام. تأكدي من الرقم.")
    return None


def gold_weight(total_weight: float, has_stones: bool, includes_stones: bool,
                stone_weight: float | None) -> dict:
    """Returns the gold weight used in the calculation, plus notes or an error."""
    err = validate_weight(total_weight)
    if err:
        return {"ok": False, "error": err}
    if not has_stones or not includes_stones:
        return {"ok": True, "gold_w": float(total_weight), "deducted": 0.0, "note": None, "upper_bound": False}
    if stone_weight is None or stone_weight == 0:
        return {
            "ok": True, "gold_w": float(total_weight), "deducted": 0.0, "upper_bound": True,
            "note": ("The weight includes stones of unknown weight, so we counted all of it as gold. "
                     "The gold value here is therefore higher than the real one.",
                     "الوزن المدخل يشمل أحجارًا وزنها غير معروف، فحسبنا الوزن كله ذهبًا. "
                     "لذلك قيمة الذهب هنا أعلى من الحقيقية."),
        }
    if stone_weight < 0:
        return {"ok": False, "error": ("Stone weight cannot be negative.", "وزن الأحجار لا يمكن أن يكون سالبًا.")}
    if stone_weight >= total_weight:
        return {"ok": False, "error": ("Stone weight must be less than the total piece weight.", "وزن الأحجار يجب أن يكون أقل من وزن القطعة الكلي.")}
    return {"ok": True, "gold_w": float(total_weight - stone_weight), "deducted": float(stone_weight),
            "note": None, "upper_bound": False}


# ---------------------------------------------------------------------------
# Shop survey (collected 29 Oct 2026, prices BEFORE VAT)
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


def survey_rows(survey: pd.DataFrame, karat: int, category: str, city: str | None = None,
                shop: str | None = None) -> tuple[pd.DataFrame, bool]:
    """Eligible shops for the choice. Returns (rows, general) where general=True means the
    ranges are a general estimate whose karat was NOT specified in the survey."""
    if survey.empty:
        return survey, False
    s = survey[(survey["category"] == category) & survey["available"]]
    exact = s[s["karat"] == karat]
    if len(exact):
        s, general = exact, False
    else:
        s, general = s[~s["karat_specified"]], True   # never reuse 21K bangle prices for other karats
    if city:
        s = s[s["city_en"] == city]
    if shop:
        s = s[s["shop_en"] == shop]
    return s, general


def _shop_extras(row, w: float) -> tuple[float, float]:
    lo = row["fee_min_per_g"] * w + row["fixed_profit_min"]   # fixed profit is added once per piece
    hi = row["fee_max_per_g"] * w + row["fixed_profit_max"]
    return lo, hi


def extras_range(rows: pd.DataFrame, gold_w: float) -> dict | None:
    """Range of (making charge + profit) across eligible shops. Each shop is computed on its own
    first, so a minimum from one shop is never mixed with a profit from another."""
    if rows is None or rows.empty:
        return None
    per_shop = [(r["shop_en"], *_shop_extras(r, gold_w)) for _, r in rows.iterrows()]
    return {
        "low": min(p[1] for p in per_shop), "high": max(p[2] for p in per_shop),
        "per_shop": per_shop, "rows": rows, "n_shops": rows["shop_en"].nunique(),
        "any_fixed": bool((rows["fixed_profit_max"] > 0).any()),
    }


# ---------------------------------------------------------------------------
# Estimate
# ---------------------------------------------------------------------------
@dataclass
class Estimate:
    karat: int
    gold_w: float
    gram_price: float
    metal_value: float
    stones_value: float | None
    extras: dict | None
    vat_case: str
    vat: float | None
    notes: list[str] = field(default_factory=list)

    @property
    def has_range(self) -> bool:
        return self.extras is not None

    @property
    def subtotal_low(self) -> float:
        return self.metal_value + (self.extras["low"] if self.extras else 0) + (self.stones_value or 0)

    @property
    def subtotal_high(self) -> float:
        return self.metal_value + (self.extras["high"] if self.extras else 0) + (self.stones_value or 0)

    def vat_amount(self, subtotal: float) -> float | None:
        return None if self.vat is None else subtotal * self.vat

    @property
    def total_low(self) -> float | None:
        return None if self.vat is None else self.subtotal_low * (1 + self.vat)

    @property
    def total_high(self) -> float | None:
        return None if self.vat is None else self.subtotal_high * (1 + self.vat)


def estimate(karat: int, gold_w: float, gram_price: float, rows: pd.DataFrame | None,
             vat_case: str, stones_value: float | None = None) -> Estimate:
    ex = extras_range(rows, gold_w) if rows is not None else None
    notes = []
    return Estimate(
        karat=karat, gold_w=gold_w, gram_price=gram_price, metal_value=gram_price * gold_w,
        stones_value=stones_value, extras=ex, vat_case=vat_case, vat=vat_rate(vat_case), notes=notes,
    )


# ---------------------------------------------------------------------------
# Shop offer comparison (always on the same basis: before VAT)
# ---------------------------------------------------------------------------
def compare_offer(est: Estimate, offer: float, offer_includes_vat: str,
                  has_stones: bool, offer_includes_stones: bool) -> dict:
    if offer is None or offer <= 0:
        return {"status": "invalid", "reason": ("Enter a price greater than zero.", "أدخلي سعرًا أكبر من صفر.")}
    if offer_includes_vat == "unknown":
        return {"status": "insufficient", "reason": ("We do not know if the offer includes VAT, so the comparison may be unfair. Ask the shop and compare again.",
                "لا نعرف هل السعر المعروض يشمل الضريبة، فالمقارنة قد تكون غير عادلة. اسألي المحل ثم أعيدي المقارنة.")}
    if offer_includes_vat == "yes" and est.vat is None:
        return {"status": "insufficient", "reason": ("The offer includes VAT but the VAT case of the piece is not set, so we cannot remove VAT accurately. Set it in the optional details.",
                "العرض يشمل الضريبة، لكن الحالة الضريبية للقطعة غير محددة، فلا نستطيع حذف الضريبة منه بدقة. حددي الحالة في التفاصيل الاختيارية.")}
    if has_stones and offer_includes_stones and est.stones_value is None:
        return {"status": "insufficient", "reason": ("The offer includes stones but the stone value is not in the estimate, so the comparison is not like-for-like. Enter the stone value if known.",
                "العرض يشمل أحجارًا، وقيمة الأحجار غير مدخلة في التقدير، فالمقارنة غير متكافئة. أدخلي قيمة الأحجار إن كانت معروفة.")}

    pre_vat = offer / (1 + est.vat) if offer_includes_vat == "yes" else offer
    stones = est.stones_value if (has_stones and offer_includes_stones and est.stones_value) else 0.0
    implicit = pre_vat - est.metal_value - stones
    out = {
        "pre_vat": pre_vat, "implicit": implicit,
        "implicit_per_gram": implicit / est.gold_w if est.gold_w else np.nan,
    }
    if not est.has_range:
        out.update(status="no_range")
        return out
    lo = est.metal_value + est.extras["low"] + stones
    hi = est.metal_value + est.extras["high"] + stones
    if pre_vat < lo:
        out.update(status="below", diff=pre_vat - lo)
    elif pre_vat > hi:
        out.update(status="above", diff=pre_vat - hi)
    else:
        out.update(status="within", diff=0.0)
    out.update(low=lo, high=hi)
    return out


# ---------------------------------------------------------------------------
# Budget: how many grams can I get?
# ---------------------------------------------------------------------------
def _weight_for_budget(budget_pre_vat: float, gram_price: float, per_gram_extra: float, fixed_extra: float) -> float:
    w = (budget_pre_vat - fixed_extra) / (gram_price + per_gram_extra)
    return max(w, 0.0)


def budget_weight(budget: float, gram_price: float, rows: pd.DataFrame | None, vat: float) -> dict:
    if budget is None or budget <= 0:
        return {"ok": False, "error": "budget"}
    pre = budget / (1 + vat)
    if rows is None or rows.empty:
        return {"ok": True, "metal_only": True, "high": pre / gram_price, "low": None}
    lows, highs = [], []
    for _, r in rows.iterrows():
        highs.append(_weight_for_budget(pre, gram_price, r["fee_min_per_g"], r["fixed_profit_min"]))
        lows.append(_weight_for_budget(pre, gram_price, r["fee_max_per_g"], r["fixed_profit_max"]))
    return {"ok": True, "metal_only": False, "low": min(lows), "high": max(highs)}
