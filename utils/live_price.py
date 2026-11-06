"""Current reference gold price for the calculator (spot XAU, USD per troy ounce).

Providers
---------
1. GoldAPI.io  (only if a key is set in Streamlit Secrets as GOLDAPI_KEY)
   GET https://www.goldapi.io/api/XAU/USD   header: x-access-token
   fields used: price (USD per troy ounce), timestamp (Unix seconds, time of the quote)
2. Gold-API.com (no key)
   GET https://api.gold-api.com/price/XAU
   fields used: price (USD per troy ounce), updatedAt (ISO time in UTC, time of the quote)

The historical study (gold futures, GC=F) is never used here as a silent replacement.
Everything in this module is plain Python so it can be tested without a network.
"""
from __future__ import annotations

import json
import math
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import settings

NY = ZoneInfo("America/New_York")
RIYADH = ZoneInfo(settings.RIYADH_TZ)
TIMEOUT = 8  # seconds


@dataclass
class Quote:
    ok: bool
    usd_oz: float | None = None
    quote_time: datetime | None = None      # time of the price itself (UTC), not the time we fetched it
    fetched_at: datetime | None = None
    provider: str = ""
    provider_url: str = ""
    status: str = ""                        # live | delayed | closed | error
    age_minutes: float | None = None
    error: tuple | None = None              # (en, ar)


# ---------------------------------------------------------------------------
# Market hours for spot gold: Sunday 18:00 to Friday 17:00 New York time, daily break 17:00-18:00.
# ---------------------------------------------------------------------------
def market_open(now_utc: datetime) -> bool:
    t = now_utc.astimezone(NY)
    wd, h = t.weekday(), t.hour            # Monday = 0 ... Sunday = 6
    if wd == 5:                            # Saturday
        return False
    if wd == 6:                            # Sunday: opens 18:00
        return h >= 18
    if wd == 4:                            # Friday: closes 17:00
        return h < 17
    return not (h == 17)                   # Mon-Thu: daily break 17:00-18:00


# ---------------------------------------------------------------------------
# Parsing (one function per provider)
# ---------------------------------------------------------------------------
def parse_goldapi_io(payload: dict) -> tuple[float, datetime]:
    if str(payload.get("metal", "XAU")).upper() != "XAU" or str(payload.get("currency", "USD")).upper() != "USD":
        raise ValueError("unexpected metal or currency")
    price = float(payload["price"])
    ts = datetime.fromtimestamp(float(payload["timestamp"]), tz=timezone.utc)
    return price, ts


def parse_gold_api_com(payload: dict) -> tuple[float, datetime]:
    if str(payload.get("symbol", "XAU")).upper() != "XAU" or str(payload.get("currency", "USD")).upper() != "USD":
        raise ValueError("unexpected metal or currency")
    price = float(payload["price"])
    raw = str(payload["updatedAt"]).replace("Z", "+00:00")
    ts = datetime.fromisoformat(raw)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return price, ts.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check(price: float, quote_time: datetime, now_utc: datetime) -> tuple[str, float, tuple | None]:
    """Returns (status, age in minutes, error). A non-None error means: do not use this price."""
    lo, hi = settings.PRICE_PLAUSIBLE_USD_OZ
    if not (isinstance(price, float) and math.isfinite(price)) or price <= 0:
        return "error", 0.0, ("The price received is not valid.", "السعر المستلم غير صالح.")
    if not (lo <= price <= hi):
        return "error", 0.0, ("The price received is outside a plausible range for gold per ounce, so it was not used.",
                              "السعر المستلم خارج النطاق المعقول لأونصة الذهب، فلم نستخدمه.")
    age = (now_utc - quote_time).total_seconds() / 60
    if age < -5:
        return "error", age, ("The price time is in the future, so it is not reliable.", "توقيت السعر في المستقبل، فهو غير موثوق.")
    if age > settings.PRICE_MAX_AGE_HOURS * 60:
        return "error", age, ("The latest price is too old to use for a purchase estimate.", "آخر سعر قديم جدًا لاستخدامه في تقدير الشراء.")
    if not market_open(now_utc):
        last_open = last_open_time(now_utc)
        if last_open is not None and quote_time < last_open - timedelta(minutes=settings.PRICE_STALE_OPEN_MINUTES):
            return "error", age, ("The latest price is older than the last market session, so it is not reliable.",
                                  "آخر سعر أقدم من آخر جلسة للسوق، فهو غير موثوق.")
        return "closed", age, None
    if age > settings.PRICE_STALE_OPEN_MINUTES:
        return "error", age, ("The market is open but the latest price is too old, so it was not used.",
                              "السوق مفتوح لكن آخر سعر قديم، فلم نستخدمه.")
    if age > settings.PRICE_DELAY_MINUTES:
        return "delayed", age, None
    return "live", age, None


def last_open_time(now_utc: datetime) -> datetime | None:
    """The last moment (10-minute steps) when the market was open, looking back up to 4 days."""
    t = now_utc
    for _ in range(4 * 24 * 6):
        t -= timedelta(minutes=10)
        if market_open(t):
            return t
    return None


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------
def _get_json(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EYAR-student-project/1.0",
                                               **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch(goldapi_key: str | None = None, now_utc: datetime | None = None, getter=_get_json) -> Quote:
    """Try the providers in order. Never falls back to the historical study data."""
    now_utc = now_utc or datetime.now(timezone.utc)
    providers = []
    if goldapi_key:
        providers.append(("GoldAPI.io", settings.SOURCES["goldapi_io"][1],
                          lambda: getter("https://www.goldapi.io/api/XAU/USD", {"x-access-token": goldapi_key}), parse_goldapi_io))
    providers.append(("Gold-API.com", settings.SOURCES["gold_api"][1],
                      lambda: getter("https://api.gold-api.com/price/XAU"), parse_gold_api_com))
    last_error = ("Could not reach the price service.", "تعذر الوصول إلى خدمة السعر.")
    for name, url, get, parse in providers:
        try:
            price, qt = parse(get())
        except Exception:
            last_error = ("Could not get a valid price from the price service right now.", "تعذر الحصول على سعر صالح من خدمة السعر الآن.")
            continue
        status, age, err = check(price, qt, now_utc)
        if err:
            last_error = err
            continue
        return Quote(True, price, qt, now_utc, name, url, status, age)
    return Quote(False, fetched_at=now_utc, status="error", error=last_error)


def riyadh(dt: datetime) -> datetime:
    return dt.astimezone(RIYADH)
