"""Loading the cleaned data and building the derived columns.

All derived columns are computed on the FULL history before any period filter,
so a daily return never changes because the user moved the slider.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings

REQUIRED_COLUMNS = ["Date", "Close", "Oil_Price"]


class DataError(Exception):
    """Raised when the data file is missing or does not have the expected columns."""


def safe_return(price: pd.Series) -> pd.Series:
    """Daily % change, only where today's AND yesterday's price are positive.

    The notebook used `Oil_Return < -100 -> NaN`; for this data both rules remove the
    same two days (20 and 21 April 2020), but this rule is safer in general.
    """
    prev = price.shift(1)
    ret = (price / prev - 1) * 100
    ret[(price <= 0) | (prev <= 0) | price.isna() | prev.isna()] = np.nan
    return ret


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataError("الأعمدة التالية غير موجودة في ملف البيانات: " + "، ".join(missing))

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)

    df["Gold_Return"] = safe_return(df["Close"])
    df["Oil_Return"] = safe_return(df["Oil_Price"])
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month

    # Drawdown over the full history (the discover page recomputes it inside the chosen period)
    df["Running_Max"] = df["Close"].cummax()
    df["Drawdown"] = (df["Close"] / df["Running_Max"] - 1) * 100

    # Everything shown to the user is in SAR (notebook conversion: 3.75 SAR/USD, 31.1035 g per ounce)
    df["Gold_SAR_g"] = df["Close"] / settings.OUNCE_IN_GRAMS * settings.DEFAULT_USD_TO_SAR   # 24K, SAR per gram
    df["Oil_SAR_bbl"] = df["Oil_Price"] * settings.DEFAULT_USD_TO_SAR                          # SAR per barrel

    # Price per gram in SAR with the default peg (display only; the calculator lets you change the rate)
    gram_24 = df["Close"] / settings.OUNCE_IN_GRAMS * settings.DEFAULT_USD_TO_SAR
    for k in settings.KARATS:
        df[f"Gold_{k}K_SAR_g"] = gram_24 * k / 24
    return df


def load_raw(path=settings.DATA_FILE) -> pd.DataFrame:
    if not path.exists():
        raise DataError(f"ملف البيانات غير موجود: {path.name}. ضعي ملف gold_oil_clean.csv داخل مجلد data.")
    return pd.read_csv(path)


def load(path=settings.DATA_FILE) -> pd.DataFrame:
    return prepare(load_raw(path))


def filter_period(df: pd.DataFrame, start, end) -> pd.DataFrame:
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    return df[(df["Date"] >= start) & (df["Date"] <= end)].reset_index(drop=True)


def load_events(path=settings.EVENTS_FILE) -> pd.DataFrame:
    ev = pd.read_csv(path)
    ev["date"] = pd.to_datetime(ev["date"])
    return ev
