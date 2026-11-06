"""EYAR | عيار: understand gold's history and the price of your piece.

Run:  streamlit run app.py
"""
import streamlit as st

from utils import ui
from utils.i18n import L, init_lang, keep_lang_in_url

st.set_page_config(page_title="EYAR | عيار", page_icon="assets/icon.png", layout="wide",
                   initial_sidebar_state="auto")

init_lang()          # English for a first visit; afterwards the saved choice (also kept in the address as ?lang=)
ui.inject_css()
ui.splash_once()     # once per session: not on language switch, page change or calculations

PAGES = [
    st.Page("views/discover.py", title=L("Discover gold", "اكتشف الذهب"), icon=":material/insights:", url_path="discover", default=True),
    st.Page("views/holding.py", title=L("Try holding", "جرّب الاحتفاظ"), icon=":material/hourglass_top:", url_path="holding"),
    st.Page("views/calculator.py", title=L("Price your piece", "احسب قطعتك"), icon=":material/calculate:", url_path="calculator"),
    st.Page("views/about.py", title=L("About the data", "عن البيانات"), icon=":material/info:", url_path="about"),
]
nav = st.navigation(PAGES, position="top")

ui.lang_toggle()
keep_lang_in_url()
df = ui.get_data()
ui.sidebar_info(df)

nav.run()
