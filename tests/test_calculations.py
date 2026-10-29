"""Hand-checkable tests for the core calculations.  Run:  python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import analysis as A  # noqa: E402
from utils import calc, data, settings  # noqa: E402

SURVEY = calc.load_survey(settings.SURVEY_FILE)[0]


class TestPrices(unittest.TestCase):
    def test_gram_price(self):
        # 3110.35 USD/oz x 3.75 / 31.1035 = 375 SAR per gram of 24K; 18K = 375 x 18/24 = 281.25
        self.assertAlmostEqual(calc.gram_price_from_ounce(3110.35, 3.75, 24), 375.0, places=6)
        self.assertAlmostEqual(calc.gram_price_from_ounce(3110.35, 3.75, 18), 281.25, places=6)
        self.assertAlmostEqual(calc.gram_price_from_ounce(3110.35, 3.75, 21), 328.125, places=6)

    def test_manual_gram_price_not_scaled_again(self):
        est = calc.estimate(18, 10, 300.0, None, "jewelry")
        self.assertAlmostEqual(est.metal_value, 3000.0)


class TestStones(unittest.TestCase):
    def test_deduct_when_weight_includes_stones(self):
        g = calc.gold_weight(10, True, True, 2)
        self.assertTrue(g["ok"]); self.assertAlmostEqual(g["gold_w"], 8.0)

    def test_no_deduction_for_net_weight(self):
        g = calc.gold_weight(10, True, False, 2)
        self.assertAlmostEqual(g["gold_w"], 10.0); self.assertEqual(g["deducted"], 0.0)

    def test_stones_heavier_than_piece(self):
        self.assertFalse(calc.gold_weight(5, True, True, 5)["ok"])
        self.assertFalse(calc.gold_weight(5, True, True, 7)["ok"])

    def test_unknown_stone_weight_is_flagged(self):
        g = calc.gold_weight(10, True, True, None)
        self.assertTrue(g["upper_bound"]); self.assertAlmostEqual(g["gold_w"], 10.0)

    def test_invalid_weights(self):
        for w in (None, 0, -3, 20_000):
            self.assertFalse(calc.gold_weight(w, False, False, None)["ok"])


class TestSurvey(unittest.TestCase):
    """Examples from the project brief: gram 400 SAR, 10 g gold, 15% VAT, no stones."""

    def total(self, karat, cat, shop):
        rows, general = calc.survey_rows(SURVEY, karat, cat, shop=shop)
        return calc.estimate(karat, 10, 400.0, rows, "jewelry"), general

    def test_remas_bangles(self):
        est, general = self.total(21, "bangles", "Remas")
        self.assertFalse(general)
        self.assertAlmostEqual(est.total_low, 4669); self.assertAlmostEqual(est.total_high, 4669)

    def test_lavin_bangles(self):
        est, _ = self.total(21, "bangles", "Lavin")
        self.assertAlmostEqual(est.total_low, 4830)

    def test_lamir_other_pieces_fixed_profit_once(self):
        est, general = self.total(21, "other", "Lamir")
        self.assertTrue(general)  # karat not specified in the survey
        self.assertAlmostEqual(est.total_low, 4853); self.assertAlmostEqual(est.total_high, 5209.5)

    def test_bukhari_not_offered_for_21k_bangles(self):
        rows, _ = calc.survey_rows(SURVEY, 21, "bangles", shop="Al-Bukhari")
        self.assertTrue(rows.empty)

    def test_bangle_prices_not_reused_for_other_karats(self):
        for k in (18, 22, 24):
            rows, _ = calc.survey_rows(SURVEY, k, "bangles")
            self.assertTrue(rows.empty)

    def test_sample_range_uses_each_shop_separately(self):
        rows, _ = calc.survey_rows(SURVEY, 21, "bangles")
        self.assertEqual(rows["shop_en"].nunique(), 5)
        ex = calc.extras_range(rows, 10)
        self.assertAlmostEqual(ex["low"], 60); self.assertAlmostEqual(ex["high"], 200)
        rows, _ = calc.survey_rows(SURVEY, 21, "other")
        ex = calc.extras_range(rows, 10)
        # lowest single shop: 20*10 + 20 = 220 (Bareeq Eifa/Lamir); highest: 160*10 = 1600 (Al-Bukhari)
        self.assertAlmostEqual(ex["low"], 220); self.assertAlmostEqual(ex["high"], 1600)

    def test_city_filter(self):
        rows, _ = calc.survey_rows(SURVEY, 21, "bangles", city="Riyadh")
        self.assertEqual(set(rows["shop_en"]), {"Lavin", "Bareeq Eifa"})

    def test_vat_once_and_24k_not_zero(self):
        self.assertEqual(calc.estimate(24, 10, 400.0, None, "jewelry").vat, 0.15)
        self.assertEqual(calc.estimate(24, 10, 400.0, None, "investment").vat, 0.0)
        self.assertIsNone(calc.estimate(24, 10, 400.0, None, "unknown").total_low)

    def test_stones_value_inside_taxable_total(self):
        est = calc.estimate(21, 10, 300.0, None, "jewelry", stones_value=500)
        self.assertAlmostEqual(est.subtotal_low, 3500); self.assertAlmostEqual(est.total_low, 4025)


class TestOfferAndBudget(unittest.TestCase):
    def setUp(self):
        self.rows, _ = calc.survey_rows(SURVEY, 21, "bangles")         # extras 60..200 for 10 g
        self.est = calc.estimate(21, 10, 400.0, self.rows, "jewelry")  # subtotal 4060..4200

    def test_offer_with_vat_removed_once(self):
        c = calc.compare_offer(self.est, 4715, "yes", False, False)    # 4715 / 1.15 = 4100
        self.assertAlmostEqual(c["pre_vat"], 4100); self.assertEqual(c["status"], "within")
        self.assertAlmostEqual(c["implicit"], 100); self.assertAlmostEqual(c["implicit_per_gram"], 10)

    def test_offer_above_and_below(self):
        self.assertEqual(calc.compare_offer(self.est, 4300, "no", False, False)["status"], "above")
        self.assertEqual(calc.compare_offer(self.est, 4050, "no", False, False)["status"], "below")

    def test_offer_unknown_vat_is_insufficient(self):
        self.assertEqual(calc.compare_offer(self.est, 4300, "unknown", False, False)["status"], "insufficient")

    def test_budget_range(self):
        b = calc.budget_weight(4669, 400.0, self.rows, 0.15)
        # pre-VAT 4060 -> cheapest shop (6/g): 4060/406 = 10 g; dearest (20/g): 4060/420
        self.assertAlmostEqual(b["high"], 10.0); self.assertAlmostEqual(b["low"], 4060 / 420)

    def test_budget_fixed_profit(self):
        rows, _ = calc.survey_rows(SURVEY, 21, "other", shop="Lamir")
        b = calc.budget_weight(4853, 400.0, rows, 0.15)
        self.assertAlmostEqual(b["high"], 10.0)   # (4220 - 20) / 420

    def test_budget_metal_only(self):
        b = calc.budget_weight(3450, 300.0, None, 0.15)
        self.assertTrue(b["metal_only"]); self.assertAlmostEqual(b["high"], 10.0)


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
