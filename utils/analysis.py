"""Analysis functions shared by all pages (pure pandas, no Streamlit)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings


def pct_change(old: float, new: float) -> float:
    return (new / old - 1) * 100


# ---------------------------------------------------------------------------
# Price, drawdown, yearly returns
# ---------------------------------------------------------------------------
def period_summary(d: pd.DataFrame) -> dict:
    first, last = d.iloc[0], d.iloc[-1]
    peak_i = d["Close"].idxmax()
    low_i = d["Close"].idxmin()
    return {
        "start_date": first["Date"], "end_date": last["Date"],
        "start_price": float(first["Close"]), "end_price": float(last["Close"]),
        "change_pct": pct_change(first["Close"], last["Close"]),
        "peak_date": d.loc[peak_i, "Date"], "peak_price": float(d.loc[peak_i, "Close"]),
        "low_date": d.loc[low_i, "Date"], "low_price": float(d.loc[low_i, "Close"]),
        "rows": len(d),
    }


def drawdown(close: pd.Series) -> pd.Series:
    """% below the highest price reached so far INSIDE the given series."""
    return (close / close.cummax() - 1) * 100


def max_drawdown(d: pd.DataFrame) -> dict:
    dd = drawdown(d["Close"])
    i = dd.idxmin()
    return {"value": float(dd.min()), "date": d.loc[i, "Date"], "series": dd}


def yearly_returns(d: pd.DataFrame, full: pd.DataFrame) -> pd.DataFrame:
    """Return from the first close to the last close INSIDE each year (same as the notebook).

    A year is marked partial when the selected data does not cover all trading days
    of that year (cut by the period filter, or the year is not finished in the data).
    """
    full_bounds = full.groupby("Year")["Date"].agg(["min", "max"])
    last_date = full["Date"].max()
    g = d.groupby("Year")
    out = pd.DataFrame({
        "first": g["Close"].first(), "last": g["Close"].last(),
        "start": g["Date"].min(), "end": g["Date"].max(),
    })
    out["return"] = (out["last"] / out["first"] - 1) * 100
    partial = []
    for year, row in out.iterrows():
        cut = row["start"] > full_bounds.loc[year, "min"] or row["end"] < full_bounds.loc[year, "max"]
        unfinished = year == last_date.year and last_date < pd.Timestamp(year=year, month=12, day=24)
        partial.append(bool(cut or unfinished))
    out["partial"] = partial
    return out.reset_index()


# ---------------------------------------------------------------------------
# Daily returns, volatility, outliers
# ---------------------------------------------------------------------------
def return_stats(ret: pd.Series) -> dict:
    r = ret.dropna()
    q1, q3 = r.quantile(0.25), r.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = r[(r < lower) | (r > upper)]
    return {
        "n": len(r), "std": float(r.std()), "mean": float(r.mean()),
        "q1": float(q1), "q3": float(q3), "lower": float(lower), "upper": float(upper),
        "n_out": len(outliers), "share_out": len(outliers) / len(r) * 100 if len(r) else np.nan,
        "min": float(r.min()), "max": float(r.max()),
        "min_date": None, "max_date": None,
    }


def up_down_by_year(d: pd.DataFrame) -> pd.DataFrame:
    r = d.dropna(subset=["Gold_Return"])
    up = (r["Gold_Return"] > 0).groupby(r["Year"]).sum()
    total = r.groupby("Year").size()
    return pd.DataFrame({"Year": total.index, "up": up.values, "down_flat": (total - up).values})


def correlations(d: pd.DataFrame) -> dict:
    both = d.dropna(subset=["Gold_Return", "Oil_Return"])
    return {
        "price": float(d["Close"].corr(d["Oil_Price"])) if len(d) > 2 else np.nan,
        "returns": float(both["Gold_Return"].corr(both["Oil_Return"])) if len(both) > 2 else np.nan,
        "n_returns": len(both),
    }


def corr_strength(r: float, lang: str = "ar") -> str:
    a = abs(r)
    en = lang == "en"
    if np.isnan(a):
        return "not available" if en else "غير متاح"
    if a < 0.1:
        return "Near zero" if en else "قريب من الصفر"
    if a < 0.3:
        return "Weak" if en else "ضعيف"
    if a < 0.5:
        return "Moderate" if en else "متوسط"
    if a < 0.7:
        return "Fairly strong" if en else "قوي نسبيًا"
    return "Strong" if en else "قوي"


# ---------------------------------------------------------------------------
# Event study (trading sessions, reference = last close BEFORE the event)
# ---------------------------------------------------------------------------
def event_study(full: pd.DataFrame, event_date, before=settings.EVENT_BEFORE,
                after_short=settings.EVENT_AFTER_SHORT, after_long=settings.EVENT_AFTER_LONG) -> dict:
    event_date = pd.Timestamp(event_date)
    on_or_after = full.index[full["Date"] >= event_date]
    if len(on_or_after) == 0 or on_or_after[0] == 0:
        return {"ok": False, "reason": ("Not enough data before or after the event.", "لا توجد بيانات كافية قبل الحدث أو بعده.")}
    base = on_or_after[0] - 1
    if base - before < 0:
        return {"ok": False, "reason": (f"{before} trading sessions before the event are not available.", f"لا تتوفر {before} جلسة تداول قبل الحدث في البيانات.")}
    if base + after_long > full.index[-1]:
        return {"ok": False, "reason": (f"{after_long} trading sessions after the event are not available.", f"لا تتوفر {after_long} جلسة تداول بعد الحدث في البيانات.")}
    c = full["Close"]
    return {
        "ok": True,
        "base_pos": int(base),
        "base_date": full.loc[base, "Date"],
        "base_price": float(c[base]),
        "before": pct_change(c[base - before], c[base]),
        "after_short": pct_change(c[base], c[base + after_short]),
        "after_long": pct_change(c[base], c[base + after_long]),
        "window": full.loc[base - before: base + after_long, ["Date", "Close"]].assign(
            session=np.arange(-before, after_long + 1),
            index=lambda w: w["Close"] / c[base] * 100,
        ),
    }


def typical_change(full: pd.DataFrame, sessions: int = 30) -> dict:
    ch = full["Close"].pct_change(sessions).dropna() * 100
    return {"mean": float(ch.mean()), "q1": float(ch.quantile(0.25)), "q3": float(ch.quantile(0.75))}


# ---------------------------------------------------------------------------
# Holding periods (same method as the notebook: shift by 252 sessions per year)
# ---------------------------------------------------------------------------
def holding_returns(full: pd.DataFrame, years: int) -> pd.Series:
    n = years * settings.SESSIONS_PER_YEAR
    return ((full["Close"].shift(-n) / full["Close"]) - 1) * 100


def holding_table(full: pd.DataFrame, years_list=settings.HOLDING_YEARS) -> pd.DataFrame:
    rows = []
    for y in years_list:
        r = holding_returns(full, y).dropna()
        rows.append({
            "years": y, "tested": len(r),
            "positive_pct": (r > 0).mean() * 100 if len(r) else np.nan,
            "doubled_pct": (r >= 100).mean() * 100 if len(r) else np.nan,
            "median": r.median(), "worst": r.min(), "best": r.max(),
            "last_buy": full["Date"].iloc[len(r) - 1] if len(r) else None,
        })
    return pd.DataFrame(rows)


def simulate_hold(full: pd.DataFrame, buy_date, years: int, amount: float) -> dict:
    """Buy on the first trading day on/after buy_date and hold `years * 252` sessions."""
    n = years * settings.SESSIONS_PER_YEAR
    idx = full.index[full["Date"] >= pd.Timestamp(buy_date)]
    if len(idx) == 0:
        return {"ok": False, "reason": ("No trading session on or after this date in the data.", "لا توجد جلسة تداول في هذا التاريخ أو بعده داخل البيانات.")}
    start = int(idx[0])
    end = start + n
    if end > full.index[-1]:
        last_ok = full["Date"].iloc[full.index[-1] - n] if full.index[-1] - n >= 0 else None
        return {"ok": False, "reason": "insufficient", "last_ok": last_ok, "start_date": full.loc[start, "Date"]}
    path = full.loc[start:end, ["Date", "Close"]].copy()
    path["Value"] = amount * path["Close"] / path["Close"].iloc[0]
    dd = drawdown(path["Close"])
    p0, p1 = float(path["Close"].iloc[0]), float(path["Close"].iloc[-1])
    return {
        "ok": True, "path": path,
        "start_date": path["Date"].iloc[0], "end_date": path["Date"].iloc[-1],
        "start_price": p0, "end_price": p1,
        "change_pct": pct_change(p0, p1),
        "final_value": amount * p1 / p0, "gain": amount * p1 / p0 - amount,
        "max_dd": float(dd.min()), "max_dd_date": path.loc[dd.idxmin(), "Date"],
        "sessions": n,
    }
