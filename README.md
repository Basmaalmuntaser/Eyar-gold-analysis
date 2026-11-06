# EYAR | عيار

**Understand gold's moves and the price of your piece.**

EYAR is a Streamlit dashboard developed for a Data Science Bootcamp project. It explores historical gold and oil prices from January 2015 to October 2026 and connects the analysis with a simple gold price calculator for Saudi Arabia.

The app opens in English for a first visit and has an **English / العربية** switch at the top. Arabic is shown right-to-left. Prices and amounts are in Saudi riyals (SAR).

## Live App

[Open EYAR](https://eyar-gold-analysis-efednvdrnbhyg3sdwdge5h.streamlit.app/) · [GitHub Repository](https://github.com/Basmaalmuntaser/Eyar-gold-analysis)

## Share Page

A small static page with the EYAR logo and a button to open the app lives in `docs/` (`index.html`, `og-image.png`, `icon.png`). Once GitHub Pages is turned on for the `docs` folder, its address is:

https://basmaalmuntaser.github.io/Eyar-gold-analysis/

Sharing **this** address shows the EYAR preview image (Open Graph and Twitter Card tags). The preview of the original Streamlit address does not change. Messaging apps may keep an older preview for a while.

## App Pages

| Page | What it does |
|---|---|
| **Discover gold** | Key metrics, price journey (with an optional moving average), yearly performance, gold vs oil (scatter, correlation heatmap), world events, risk (drawdown, distribution, boxplot, up/down days), data preview and summary statistics. Filters in the sidebar. |
| **Try holding** | “If you had bought gold years ago, what would it be worth?” Buy date, gold value at purchase, karat, and a holding period of 1–10 calendar years or *until today*. |
| **Price your piece** | Karat, net gold weight and piece type (bangles / other pieces; for 24K also a *qualified investment bar* option). Shows an estimated price range with the current reference gold price, plus “How much gold can my budget buy?”. |
| **About the data** | Background, sources, columns and units, cleaning steps, definitions, limitations, VAT notes, the original shop survey, and downloads. |

Sidebar (Discover gold): dataset description, sources and period; **View type** dropdown; **From date** and **To date** fields; a **moving average** slider; an **assets** multiselect; and **Reset filters**.

## Four different things in this app

1. **Historical study results** (Discover gold and the notebook) use the historical data coverage, 2 January 2015 – 26 October 2026. They do not change when the calculator price changes.
2. **Calculator price**: a current spot reference price (XAU/USD) fetched when the page is used.
3. **Estimated add-ons**: making charge and shop margin together, set by the project owner as app assumptions.
4. **Try holding**: the value of gold bought on a past date, after whole calendar years (historical data) or until today (current reference price).

## Language

- English is the default only for a first visit. After choosing a language, it stays the same on every page, after calculations, filter changes and downloads.
- The choice is stored in one shared session value (`lang_pref`) and in the page address as `?lang=en` or `?lang=ar`, so it is also restored after a page refresh.
- The intro logo appears once per session; it does not replay when the language changes.

## Current Reference Price (calculator and “until today”)

- **Default provider: Gold-API.com** (`GET https://api.gold-api.com/price/XAU`), no key needed. Fields used: `price` (USD per troy ounce) and `updatedAt` (time of the quote, UTC).
- **Optional provider: GoldAPI.io** (`GET https://www.goldapi.io/api/XAU/USD`, header `x-access-token`). Used first only if a key is set in Streamlit Secrets. Fields used: `price` and `timestamp` (Unix time of the quote).
- A fetched quote is kept for **5 minutes**. The **Refresh price** button fetches again.
- The page shows the source and the **price time in Riyadh time** (the quote's own time, not the time we fetched it).
- Market hours for spot gold (Sunday 18:00 to Friday 17:00 New York time, daily break 17:00–18:00): when the market is closed the price is labelled **“Last available price — market closed”**. When the market is open and the quote is 15–60 minutes old it is labelled **delayed**.
- A price is **not used** if it is not positive, is outside 500–20,000 USD per ounce (this catches per-gram or wrong-currency values), is in the future, is more than 60 minutes old while the market is open, or is older than the last market session while it is closed.
- If no reliable price is available, the calculator shows a clear message and **does not estimate a price**. It never falls back to the October study data. The last good price received in the session may be shown for information only.
- Conversion: `SAR per gram for a karat = USD per ounce × 3.75 ÷ 31.1035 × karat ÷ 24`. The 3.75 SAR/USD peg is an assumption of the app.

### Streamlit Secrets (optional)

No secret is required. To use GoldAPI.io as the first provider:

1. Create a key at [goldapi.io](https://www.goldapi.io/).
2. In Streamlit Community Cloud open the app → **Settings** → **Secrets**.
3. Add one line and save:

   ```toml
   GOLDAPI_KEY = "your-key-here"
   ```

Never put the key in GitHub or in the ZIP. The free GoldAPI.io plan has a small monthly request limit; with a 5-minute cache a busy app may use it up, after which the app moves to Gold-API.com.

## Calculator Method

Inputs: karat, **net gold weight** (without stones), and piece type. For 24K only, the user can mark the piece as a qualified investment bar; changing the karat away from 24 switches this off.

```text
lowest price  = weight × (gram price + lowest add-on per gram)  × (1 + VAT)
highest price = weight × (gram price + highest add-on per gram) × (1 + VAT)
```

The add-on is the making charge and shop margin **together**; nothing is added on top of it. VAT is applied once.

### Estimated add-ons (app assumptions)

| Piece type | Add-on (SAR per gram, before VAT) |
|---|---|
| Bangles | 10 – 20 |
| Other pieces | 20 – 45 |
| Qualified investment bar | see below |

These are estimates chosen by the project owner. They are not official limits or maximum prices, and add-ons can be higher depending on the design, brand and shop. For heavier pieces a buyer may be able to negotiate an add-on closer to the lower end.

### Investment bar add-on policy (app assumption)

There is no surveyed price list for bar weights, so the app uses a simple internal policy, set in `utils/settings.py`:

- Upper add-on per gram at these weights, joined smoothly on a log-weight scale:

  | Bar weight | 1 g or less | 10 g | 50 g | 100 g | 1,000 g or more |
  |---|---|---|---|---|---|
  | Upper add-on (SAR/g) | 22 | 16 | 12 | 10 | 8 |

- Lower add-on = 50% of the upper value.
- The upper value never goes above 22 SAR/g and never increases with weight. The joints are continuous (no jumps), and the total add-on for the bar still grows with weight.
- Actual add-ons differ by refinery, brand and seller.

### VAT

- Jewelry and gold below 99% purity: **15%** on the full estimated selling price, once.
- A **qualified investment bar** (99% purity or more and tradable on the international bullion market) is **zero-rated** under its conditions. The result then says the zero rate applies on the assumption that the conditions are met. 24K alone is not enough.
- The estimate is for the sale of the piece as a product only; separate services may be treated differently.
- Source: [ZATCA, Guideline for the Investment Metals Sector under VAT Provisions](https://zatca.gov.sa/en/HelpCenter/guidelines/Documents/Guideline-For-the-Investment-Metals-Sector-under-VAT-Provisions.pdf). Check current rules with [ZATCA](https://zatca.gov.sa/).

### Budget: “How much gold can my budget buy?”

Inputs: budget, karat, piece type (and the bar option for 24K). The fewest grams use the highest add-on; the most grams use the lowest add-on. VAT is included when it applies. Because the bar add-on depends on the weight, the weight is solved numerically. Weights are rounded **down** to 0.01 g, so the price of the returned weight never exceeds the budget.

### Invoice note

The page reminds the buyer not to buy without a clear invoice showing the karat, weight, price and VAT when due, and to check the seller and the karat hallmark.

## Try Holding Method

- Gram price when bought = historical ounce price × 3.75 ÷ 31.1035 × karat ÷ 24.
- Grams = amount entered ÷ gram price when bought. The amount is the **gold value at purchase, without making charge and VAT**.
- Value at the end = grams × gram price of the same karat at the end. Gain or loss = end value − amount.
- Because the same karat is used at both ends, the % change does not depend on the karat; the karat changes the gram price and the grams bought.
- **Calendar years**: the buy price is the first trading session on or after the chosen date. The end price is the last trading session on or before the same date N years later. Only periods whose end is inside the data are offered (1–10 years). This is different from the notebook, which uses 252 trading sessions per year; the notebook results are not changed.
- **Until today / latest available price** uses the same current price service as the calculator. The buy price comes from the historical gold futures data and the current price from a spot service, so this is an approximate comparison between two references, not an exact investment return. If the current price is not available, no “today” value is shown.
- The value is an estimate for the gold only, before any shop deduction, and does not include getting back the making charge or the purchase VAT.

## Shop Survey (project documentation)

The original survey of six shops in Makkah and Riyadh, collected on **29 October 2026** (prices before VAT), is kept unchanged in `data/shop_survey.csv` and shown on the About page. The calculator now uses the estimated add-ons above instead of the survey.

## Historical Data and Methodology

- **Gold:** [Yahoo Finance — Gold Futures (GC=F)](https://finance.yahoo.com/quote/GC%3DF/history/). **Oil:** [FRED — WTI Crude Oil Spot Price (DCOILWTICO)](https://fred.stlouisfed.org/series/DCOILWTICO).
- **Historical data coverage:** 2 January 2015 – 26 October 2026 (2,971 gold trading days). The analysis uses this historical period; the calculator uses the latest price available from the price provider.
- Daily returns are calculated on the full data before any filter. Oil returns are excluded when the current or previous price is not positive (20–21 April 2020).
- Missing oil prices were forward-filled in the notebook; the cleaned CSV does not flag the filled days.
- Yearly return follows the notebook: first close to last close inside each year. The last year is partial.
- Drawdown on Discover gold is measured from peaks inside the selected period.
- The moving-average slider is computed on the full history, so the start of a filtered period is not distorted.
- Event windows use trading sessions; timing does not prove cause. IQR limits find unusual days; they are not guaranteed limits.
- The “~1-year holds” card on Discover gold is a study result (252 sessions, full study period). The share of positive cases is not the size of a profit.

## Limitations

- 2015 to October 2026 was a strong period for gold; results may differ in the future.
- Historical futures changes are not a full futures trading simulation (contract rolls, costs).
- Real purchases also involve design, brand, shop pricing and resale deductions.
- Forward-filled oil prices may affect daily returns and correlation. Only three world events are examined.
- The current price providers are third-party services without a guaranteed service level.

## Run Locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Tests

```bash
python -m unittest discover tests -v
```

The tests use hand-checkable examples, including: bangles 4,715–4,830 SAR and other pieces 4,830–5,117.50 SAR (gram price 400 SAR, 10 g, 15% VAT); VAT applied once; the bar option only for 24K; the bar policy (cap, never increasing, no jumps); budget results that never exceed the budget; holding example (200 → 400 SAR/g, 5,000 SAR → 25 g → 10,000 SAR); available calendar years and end dates; losses; same % for any karat; price checks (negative, per-gram or wrong-currency values, stale or future times, network failure, no fallback); market hours; and the notebook's data rules.

## Project Structure

| Path | Purpose |
|---|---|
| `app.py` | Entry point: page setup, language, intro, navigation, shared sidebar. |
| `views/` | The four pages. |
| `utils/settings.py` | Assumptions in one place: conversion, VAT, add-on ranges, bar policy, price-service settings, colors, sources. |
| `utils/i18n.py` | Shared language state and the `L(english, arabic)` helper. |
| `utils/live_price.py` | Current reference price: providers, parsing, checks, market hours. |
| `utils/calc.py` | Calculator and budget logic, and the shop survey loader. |
| `utils/analysis.py` | Analysis functions, including the calendar-year holding calculation. |
| `utils/data.py`, `utils/charts.py`, `utils/ui.py` | Data loading, Plotly charts, styling and shared interface helpers. |
| `data/` | `gold_oil_clean.csv` (study data), `events.csv`, `shop_survey.csv` (documentation). |
| `tests/` | Calculation tests. |
| `.streamlit/config.toml` | Theme. |

## Author

**Basma Almuntaser**

---

Educational project. Historical results and calculator estimates are not financial advice or guaranteed purchase prices.
