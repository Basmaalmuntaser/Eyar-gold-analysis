"""Hand-checkable tests for the core calculations.  Run:  python -m unittest discover tests"""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import analysis as A  # noqa: E402
from utils import calc, data, live_price, settings  # noqa: E402


class TestPrices(unittest.TestCase):
    def test_gram_price(self):
        # 3110.35 USD/oz x 3.75 / 31.1035 = 375 SAR per gram of 24K; 18K = 375 x 18/24 = 281.25
        self.assertAlmostEqual(calc.gram_price_from_ounce(3110.35, 3.75, 24), 375.0, places=6)
        self.assertAlmostEqual(calc.gram_price_from_ounce(3110.35, 3.75, 18), 281.25, places=6)
        self.assertAlmostEqual(calc.gram_price_from_ounce(3110.35, 3.75, 21), 328.125, places=6)

    def test_invalid_inputs(self):
        for w in (None, 0, -3, 20_000):
            self.assertIsNotNone(calc.validate_weight(w))
        self.assertIsNone(calc.validate_weight(10))
        for g in (None, 0, -5, float("nan"), float("inf")):
            self.assertFalse(calc.validate_gram_price(g))


class TestCalculator(unittest.TestCase):
    """Examples from the brief: gram price 400 SAR, 10 g, 15% VAT."""

    def test_bangles(self):
        e = calc.estimate(400, 10, "bangles")
        self.assertAlmostEqual(e["low"], 4715); self.assertAlmostEqual(e["high"], 4830)
        self.assertEqual((e["addon_low"], e["addon_high"]), (10, 20))

    def test_other_pieces(self):
        e = calc.estimate(400, 10, "other")
        self.assertAlmostEqual(e["low"], 4830); self.assertAlmostEqual(e["high"], 5117.5)
        self.assertEqual((e["addon_low"], e["addon_high"]), (20, 45))

    def test_vat_once_and_bar_zero_rated(self):
        e = calc.estimate(400, 10, "other")
        self.assertAlmostEqual(e["low"], e["pre_vat_low"] * 1.15)       # once, not 1.15^2
        bar = calc.estimate(400, 10, "bar")
        self.assertEqual(bar["vat"], 0.0)
        self.assertAlmostEqual(bar["high"], 10 * (400 + 16))             # 16 SAR/g at 10 g, no VAT

    def test_bar_only_for_24k(self):
        self.assertEqual(calc.category_for(24, "bangles", True), "bar")
        self.assertEqual(calc.category_for(21, "bangles", True), "bangles")   # hidden switch ignored
        self.assertEqual(calc.category_for(24, "other", False), "other")
        self.assertEqual(calc.vat_rate("other"), 0.15)                        # 24K jewelry is not zero-rated

    def test_bar_policy(self):
        ws = np.geomspace(0.1, 5000, 400)
        hi = [calc.bar_addon_high(w) for w in ws]
        self.assertTrue(all(h <= settings.BAR_ADDON_CAP for h in hi))
        self.assertTrue(all(a >= b - 1e-12 for a, b in zip(hi, hi[1:])))      # never increases with weight
        self.assertLessEqual(calc.bar_addon_high(100), 10)
        totals = [h * w for h, w in zip(hi, ws)]
        self.assertTrue(all(a <= b for a, b in zip(totals, totals[1:])))      # total add-on still grows with weight
        for w in (10, 50, 100):                                               # no jumps at the joints
            self.assertAlmostEqual(calc.bar_addon_high(w - 1e-6), calc.bar_addon_high(w + 1e-6), places=4)
        lo, hi10 = calc.addon_range("bar", 10)
        self.assertAlmostEqual(lo, hi10 * settings.BAR_ADDON_LOW_SHARE)


class TestBudget(unittest.TestCase):
    def test_bangles_budget(self):
        b = calc.budget_weight(4830, 400, "bangles")
        # fewest grams with 20/g: 4830 / (420 x 1.15) = 10; most grams with 10/g: 4830 / (410 x 1.15) = 10.24
        self.assertAlmostEqual(b["low"], 10.0); self.assertAlmostEqual(b["high"], 10.24)

    def test_budget_round_trip_never_exceeds(self):
        for cat in ("bangles", "other", "bar"):
            for budget in (999, 5000, 12345.67, 250000):
                b = calc.budget_weight(budget, 412.3, cat)
                self.assertLessEqual(calc.total_price(412.3, b["high"], cat, "low"), budget + 1e-6)
                self.assertLessEqual(calc.total_price(412.3, b["low"], cat, "high"), budget + 1e-6)
                self.assertGreater(calc.total_price(412.3, b["high"] + 0.02, cat, "low"), budget)
                self.assertLessEqual(b["low"], b["high"])

    def test_budget_invalid(self):
        for v in (None, 0, -10, float("nan")):
            self.assertFalse(calc.budget_weight(v, 400, "other")["ok"])


class TestLivePrice(unittest.TestCase):
    friday = datetime(2026, 11, 6, 13, 0, tzinfo=timezone.utc)      # Friday 08:00 New York (open)
    saturday = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)    # closed

    def ok_getter(self, t):
        return lambda url, h=None: {"symbol": "XAU", "currency": "USD", "price": 4012.5, "updatedAt": t}

    def test_market_hours(self):
        self.assertTrue(live_price.market_open(self.friday))
        self.assertFalse(live_price.market_open(self.saturday))
        self.assertFalse(live_price.market_open(datetime(2026, 11, 4, 22, 30, tzinfo=timezone.utc)))  # 17:30 NY break
        self.assertTrue(live_price.market_open(datetime(2026, 11, 8, 23, 30, tzinfo=timezone.utc)))   # Sunday 18:30 NY

    def test_live_delayed_closed(self):
        q = live_price.fetch(now_utc=self.friday, getter=self.ok_getter("2026-11-06T12:59:00Z"))
        self.assertTrue(q.ok); self.assertEqual(q.status, "live")
        q = live_price.fetch(now_utc=self.friday, getter=self.ok_getter("2026-11-06T12:30:00Z"))
        self.assertEqual(q.status, "delayed")
        q = live_price.fetch(now_utc=self.saturday, getter=self.ok_getter("2026-11-06T21:58:00Z"))
        self.assertTrue(q.ok); self.assertEqual(q.status, "closed")

    def test_rejects_bad_or_old_prices(self):
        for payload in ({"symbol": "XAU", "currency": "USD", "price": -1, "updatedAt": "2026-11-06T12:59:00Z"},
                        {"symbol": "XAU", "currency": "USD", "price": 129.0, "updatedAt": "2026-11-06T12:59:00Z"},   # per gram, not ounce
                        {"symbol": "XAU", "currency": "EUR", "price": 3500, "updatedAt": "2026-11-06T12:59:00Z"},
                        {"symbol": "XAU", "currency": "USD", "price": 4000, "updatedAt": "2026-11-06T10:00:00Z"},    # stale while open
                        {"symbol": "XAU", "currency": "USD", "price": 4000, "updatedAt": "2026-11-06T14:00:00Z"}):   # future
            q = live_price.fetch(now_utc=self.friday, getter=lambda url, h=None, p=payload: p)
            self.assertFalse(q.ok, payload)
            self.assertIsNone(q.usd_oz)          # no silent fallback to the historical data

    def test_network_failure(self):
        def boom(url, h=None):
            raise OSError("no network")
        q = live_price.fetch(now_utc=self.friday, getter=boom)
        self.assertFalse(q.ok); self.assertIsNotNone(q.error)

    def test_goldapi_io_parsing(self):
        p = {"metal": "XAU", "currency": "USD", "price": 4733.125, "timestamp": 1776907250}
        price, ts = live_price.parse_goldapi_io(p)
        self.assertEqual(price, 4733.125); self.assertEqual(ts.tzinfo, timezone.utc)


class TestHolding(unittest.TestCase):
    def setUp(self):
        dates = pd.bdate_range("2015-01-01", "2026-10-26")
        close = np.full(len(dates), 200 / 3.75 * 31.1035)          # 200 SAR/g (24K) ...
        close[dates >= "2020-01-01"] = 400 / 3.75 * 31.1035         # ... then 400 SAR/g
        self.df = data.prepare(pd.DataFrame({"Date": dates, "Close": close, "Oil_Price": 50.0}))

    def test_example_from_brief(self):
        r = A.hold_value(self.df, "2016-03-01", 5, 5000, 24)
        self.assertAlmostEqual(r["gram_start"], 200); self.assertAlmostEqual(r["gram_end"], 400)
        self.assertAlmostEqual(r["grams"], 25); self.assertAlmostEqual(r["final"], 10000); self.assertAlmostEqual(r["gain"], 5000)

    def test_same_return_for_any_karat(self):
        a = A.hold_value(self.df, "2016-03-01", 5, 5000, 18)["final"]
        b = A.hold_value(self.df, "2016-03-01", 5, 5000, 24)["final"]
        self.assertAlmostEqual(a, b)

    def test_loss_and_now(self):
        r = A.hold_value_now(self.df, "2021-01-04", 5000, 21, 200 / 3.75 * 31.1035)
        self.assertAlmostEqual(r["final"], 2500); self.assertAlmostEqual(r["gain"], -2500)

    def test_available_years_and_dates(self):
        self.assertEqual(A.available_years(self.df, "2015-01-02"), list(range(1, 11)))
        self.assertEqual(A.available_years(self.df, "2024-01-02"), [1, 2])
        self.assertEqual(A.available_years(self.df, "2026-06-01"), [])
        r = A.hold_value(self.df, "2016-02-27", 1, 1000, 24)          # Saturday -> Monday 29 Feb 2016
        self.assertEqual(r["start_date"], pd.Timestamp("2016-02-29"))
        self.assertLessEqual(r["end_date"], r["target"])               # last session on/before the anniversary
        self.assertFalse(A.hold_value(self.df, "2024-01-02", 5, 1000, 24)["ok"])


class TestSurveyFile(unittest.TestCase):
    def test_survey_kept_as_documentation(self):
        survey, msgs = calc.load_survey(settings.SURVEY_FILE)
        self.assertEqual(survey["shop_en"].nunique(), 6); self.assertEqual(msgs, [])


class TestAnalysis(unittest.TestCase):
    def setUp(self):
        dates = pd.bdate_range("2020-01-01", periods=1400)
        close = np.linspace(100, 240, len(dates))
        close[10] = 90  # a dip
        oil = np.full(len(dates), 50.0); oil[5] = -10
        self.df = data.prepare(pd.DataFrame({"Date": dates, "Close": close, "Oil_Price": oil}))

    def test_oil_return_excludes_non_positive(self):
        self.assertTrue(np.isnan(self.df.loc[5, "Oil_Return"]))
        self.assertTrue(np.isnan(self.df.loc[6, "Oil_Return"]))
        self.assertAlmostEqual(self.df.loc[7, "Oil_Return"], 0.0)

    def test_drawdown(self):
        dd = A.drawdown(pd.Series([100.0, 120, 90, 130]))
        self.assertAlmostEqual(dd.min(), -25.0)

    def test_holding_and_incomplete_dates(self):
        r = A.simulate_hold(self.df, self.df["Date"].iloc[0], 1, 1000)
        self.assertTrue(r["ok"]); self.assertEqual(len(r["path"]), 253)
        late = A.simulate_hold(self.df, self.df["Date"].iloc[-10], 5, 1000)
        self.assertFalse(late["ok"]); self.assertEqual(late["reason"], "insufficient")
        t = A.holding_table(self.df, [1])
        self.assertEqual(t.loc[0, "tested"], len(self.df) - 252)

    def test_yearly_first_to_last_inside_year(self):
        y = A.yearly_returns(self.df, self.df).set_index("Year")
        g = self.df[self.df["Year"] == 2021]["Close"]
        self.assertAlmostEqual(y.loc[2021, "return"], (g.iloc[-1] / g.iloc[0] - 1) * 100)
        self.assertTrue(y.loc[self.df["Year"].max(), "partial"])

    def test_event_window_not_available(self):
        r = A.event_study(self.df, self.df["Date"].iloc[5])
        self.assertFalse(r["ok"])


class TestRealData(unittest.TestCase):
    """Checks against the notebook, if the real data file is present."""

    @unittest.skipUnless(settings.DATA_FILE.exists(), "no data file")
    def test_matches_notebook_rules(self):
        df = data.load()
        raw = pd.read_csv(settings.DATA_FILE)
        self.assertEqual(len(df), len(raw))
        # our oil rule removes the same days as the notebook rule
        self.assertEqual(int(df["Oil_Return"].isna().sum()), int(raw["Oil_Return"].isna().sum()))
        self.assertAlmostEqual(float(df["Gold_Return"].iloc[1]), float(raw["Gold_Return"].iloc[1]), places=6)


if __name__ == "__main__":
    unittest.main()
