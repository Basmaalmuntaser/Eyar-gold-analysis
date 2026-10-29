"""Project-wide settings and assumptions (one place to edit them)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Data files
DATA_FILE = DATA_DIR / "gold_oil_clean.csv"            # the cleaned dataset from the notebook (do not edit)
EVENTS_FILE = DATA_DIR / "events.csv"                  # global events studied in the notebook
SURVEY_FILE = DATA_DIR / "shop_survey.csv"             # making charge + profit from the shop survey (29 Oct 2026)

# Units and conversion
OUNCE_IN_GRAMS = 31.1035       # one troy ounce in grams
DEFAULT_USD_TO_SAR = 3.75      # official peg of the Saudi riyal (editable in the calculator)
KARATS = [18, 21, 22, 24]

# Holding periods: same method as the notebook (252 trading sessions per year)
SESSIONS_PER_YEAR = 252
HOLDING_YEARS = [1, 3, 5]

# Event study windows (in trading sessions)
EVENT_BEFORE = 30
EVENT_AFTER_SHORT = 7
EVENT_AFTER_LONG = 30

# VAT (Saudi Arabia). See the "about" page and README for the sources used.
VAT_STANDARD = 0.15            # jewelry sold by a VAT-registered seller
VAT_INVESTMENT_GOLD = 0.0      # investment gold: purity 99% or more, tradable on the bullion market

# Minimum observations before we show a statistic
MIN_ROWS = 30

# Sources
SOURCES = {
    "gold": ("Yahoo Finance: Gold Futures (GC=F)", "https://finance.yahoo.com/quote/GC%3DF/"),
    "oil": ("FRED: WTI Crude Oil Spot Price (DCOILWTICO)", "https://fred.stlouisfed.org/series/DCOILWTICO"),
    "vat": (
        "Saudi Gazette: ZATCA on VAT for gold below 99% purity (Aug 2022)",
        "https://saudigazette.com.sa/article/623255/SAUDI-ARABIA/ZATCA-VAT-applicable-to-gold-if-its-purity-level-is-below-99",
    ),
    "zatca": ("ZATCA (official website)", "https://zatca.gov.sa/"),
}

# Visual identity
COLORS = {
    "bg": "#F7F4EE",
    "card": "#FFFFFF",
    "text": "#202A26",
    "muted": "#5E6762",
    "gold": "#8A641D",
    "gold_light": "#C9A659",
    "oil": "#3F6273",
    "up": "#176B52",
    "down": "#B74444",
    "border": "#E7E0D3",
}
FONT_FAMILY = "Tajawal, 'IBM Plex Sans Arabic', 'Noto Sans Arabic', Tahoma, sans-serif"
