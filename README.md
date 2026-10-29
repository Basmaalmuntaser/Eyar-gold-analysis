# EYAR | عيار

**Understand gold's moves and the price of your piece.**

EYAR is a Streamlit dashboard developed for a Data Science Bootcamp project. It explores historical gold and oil prices from January 2015 to October 2026 and connects the analysis with a practical gold jewelry price calculator for Saudi Arabia.

The interface defaults to English and includes an Arabic language option. Monetary results are displayed in Saudi riyals (SAR), with units shown where relevant.

## Live App

[Open EYAR](https://eyar-gold-analysis-efednvdrnbhyg3sdwdge5h.streamlit.app/)

[GitHub Repository](https://github.com/Basmaalmuntaser/Eyar-gold-analysis)

## App Pages

| Page | Features |
|---|---|
| **Discover gold** | Key metrics, historical prices, annual performance, gold and oil comparisons, scatter plots, correlation heatmaps, global events, drawdowns, daily return distributions, boxplots, up/down day counts, data previews, and summary statistics. |
| **Try holding** | Simulate a historical purchase and compare approximately 1-, 3-, and 5-year holding periods using 252 trading sessions per year. |
| **Price your piece** | Estimate a gold piece's value using karat, weight, and available shop survey ranges. Includes optional stone details, tax assumptions, shop quote comparisons, budget estimates, and calculation downloads. |
| **About the data** | Project background, sources, columns and units, cleaning methods, definitions, limitations, and data access. |

The sidebar provides a dataset description, sources, study period, display options, date filters, asset selection, and a reset option.

## Run Locally

Open a terminal in the project directory containing `app.py` and `requirements.txt`, then run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL displayed in the terminal. Keep the terminal running while using the app.

## Deploy on Streamlit Community Cloud

1. Upload the project files to a GitHub repository, preserving the folder structure.
2. Include `app.py`, `requirements.txt`, `data/`, `utils/`, `views/`, `assets/`, and `.streamlit/config.toml`.
3. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
4. Select **Create app**, then choose the repository and branch.
5. Set the main file path to `app.py`.
6. Select a Python version compatible with the dependencies. The original project instructions recommend Python 3.12.
7. Select **Deploy**.

The historical analysis does not require a market-data API key. Google Fonts requires an internet connection; a fallback font is used if it cannot load.

## Project Structure

| Path | Purpose |
|---|---|
| `app.py` | Entry point, page configuration, navigation, and shared sidebar. |
| `views/` | The four app pages. |
| `utils/settings.py` | Shared assumptions and settings, including exchange rate, tax settings, trading sessions, colors, and sources. |
| `utils/data.py` | Data loading and derived columns, including returns, drawdown, and SAR prices. |
| `utils/analysis.py` | Analysis calculations shared across pages. |
| `utils/calc.py` | Calculator logic. |
| `utils/charts.py` | Plotly visualizations. |
| `utils/ui.py` | Styling, opening animation, number formatting, and shared interface helpers. |
| `data/gold_oil_clean.csv` | Cleaned historical dataset exported from the notebook. |
| `data/events.csv` | Selected global events and dates. |
| `data/shop_survey.csv` | Shop survey data for making charges and margins in the updated project. |
| `tests/` | Calculation tests. |
| `.streamlit/config.toml` | Theme configuration. |

## Data Sources

- **Gold:** [Yahoo Finance — Gold Futures (GC=F)](https://finance.yahoo.com/quote/GC%3DF/history/).
- **Oil:** [FRED — WTI Crude Oil Spot Prices (DCOILWTICO)](https://fred.stlouisfed.org/series/DCOILWTICO).
- **Local pricing:** A field survey of six gold shops in Makkah and Riyadh, collected on October 29, 2026.

The historical dataset contains 2,971 gold trading-day observations from January 2, 2015 to October 26, 2026. It is a fixed historical snapshot and does not update automatically.

Gold is quoted using a futures price series, while oil uses a spot price series. Their units differ and are labeled in the dashboard.

## Gold Price Conversion

The default conversion assumptions are:

- Exchange rate: **3.75 SAR per USD**.
- Troy ounce: **31.1035 grams**.

```text
24K gold price in SAR per gram = gold price in USD per ounce × 3.75 / 31.1035
Price for selected karat = 24K price per gram × karat / 24
```

A directly entered gram price for the selected karat must not be adjusted for karat a second time. Converted historical futures prices are reference estimates, not live jewelry shop quotes.

The reference price and exchange rate can be adjusted through the calculator's advanced options where available. The original default exchange-rate setting is `DEFAULT_USD_TO_SAR` in `utils/settings.py`.

## Shop Survey

All amounts below were collected on **October 29, 2026**, exclude VAT, and are in SAR. Per-piece margins are explicitly distinguished from per-gram charges.

| Shop | City | 21K bangles: making charge and margin per gram | Other jewelry |
|---|---|---:|---|
| ريماس | Makkah | 6 | Making charge and margin combined: 25–60 per gram. |
| لاڤين | Riyadh | 20 | Making charge and margin combined: 25–60 per gram. |
| بريق إيفاء | Riyadh | 20 | Making charge: 20–50 per gram, plus a margin of 20–30 per piece. |
| لامير | Makkah | 20 | Making charge: 20–50 per gram, plus a margin of 20–30 per piece. |
| البخاري | Makkah | Not available | Making charge and margin combined: 80–160 per gram. The shop does not offer 21K gold, according to the survey. |
| الريس | Makkah | 20 | Making charge and margin combined: 50–150 per gram. |

The specific karats covered by the other-jewelry ranges were not recorded. These ranges must not be presented as verified quotes for every karat. The 21K bangle charges must not be automatically applied to other karats.

The sample represents the shops surveyed, not the entire Saudi market. Its observed maximum is not a legal price ceiling. Update the survey data file when new observations are collected, preserving the existing schema and distinguishing per-gram charges from per-piece margins.

## Calculator Method

1. Calculate the net gold weight, subtracting stone weight only if it is included in the entered total weight.
2. Multiply net gold weight by the reference gram price for the selected karat.
3. Add the applicable making charge and shop margin without double-counting amounts already included.
4. Include a known stone value if supplied.
5. Apply the appropriate VAT treatment once.

For a selected shop, calculate its minimum and maximum totals using that shop's own fee structure. For a survey-wide range, compare the completed totals for eligible shops rather than combining fees from different shops.

If stone value is unknown, the estimate excludes that value. An implied addition calculated from a shop quote is not necessarily the shop's profit: it may include manufacturing and other costs.

### VAT Assumptions

The project uses the Saudi standard VAT rate of 15% where applicable. Qualifying investment gold is subject to separate zero-rating conditions; selecting 24K alone does not establish eligibility. Tax treatment depends on the transaction and the relevant conditions.

Check the current rules through the [Zakat, Tax and Customs Authority](https://zatca.gov.sa/). Survey fees exclude VAT, and an entered VAT-inclusive amount must not be taxed again.

## Methodology

- Daily returns are calculated on the full chronological dataset before display filters are applied.
- Oil returns are excluded when the current or previous price is non-positive. This addresses April 20 and 21, 2020 in the dataset.
- Missing oil prices were forward-filled in the notebook. The cleaned CSV does not retain flags identifying the filled observations.
- Annual performance follows the notebook's method: change from the first to the last closing price within each year. This differs from a previous-year-end calculation.
- The final year is incomplete and must be labeled accordingly.
- Drawdown measures the percentage decline from a running peak. Its reference period must be clear when filters are used.
- Approximately 1, 3, and 5 years are represented by 252, 756, and 1,260 trading sessions.
- Holding-period results include only purchase dates with a complete future window. These windows overlap and are not independent trials.
- The percentage of profitable cases is the share of historical cases with positive price returns, not the return earned or a guaranteed future probability.
- Event windows use trading sessions. Price movements around an event do not establish causation.
- IQR boundaries identify statistical outliers; they are not guaranteed limits for future daily moves.

## Limitations

- The study covers 2015–October 2026, including a strong period for gold. Future outcomes may differ.
- Historical futures price changes do not reproduce the full return from trading futures, including contract rolls and transaction costs.
- Jewelry purchases also involve making charges, margins, taxes, stones, and potential resale deductions.
- Forward-filled oil prices may affect daily returns and correlation.
- Only three global events are examined, without isolating other simultaneous influences.
- The shop survey is a small, dated sample with incomplete karat coverage for other jewelry.

## Tests

Run the available tests from the project directory:

```bash
python -m unittest discover tests -v
```

The original README describes tests for price conversion, karat handling, stone deductions, tax calculations, making charges, margins, quote comparisons, budget calculations, oil returns, drawdown, holding periods, annual performance, and incomplete event windows. Run the tests on the current code to confirm their status.

## Author

**Basma Almuntaser** 

---

Educational project. Historical results and calculator estimates are not financial advice or guaranteed purchase prices.
