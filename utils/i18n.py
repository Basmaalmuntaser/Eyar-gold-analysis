"""Language state and a tiny translation helper. English is the default for a first visit only.

The chosen language lives in st.session_state["lang_pref"] (one shared value for every page) and is
mirrored in the page address as ?lang=ar / ?lang=en, so it also survives a page refresh. It is kept
separate from the switch widget, whose own state Streamlit may drop when you move between pages.

Usage:  L("English text", "النص العربي")
"""
import streamlit as st

LANGS = ("en", "ar")


def init_lang():
    """Call once at the top of app.py, before anything is drawn."""
    if "lang_pref" not in st.session_state:
        q = st.query_params.get("lang")
        st.session_state["lang_pref"] = q if q in LANGS else "en"


def lang() -> str:
    return st.session_state.get("lang_pref", "en")


def set_lang(value: str):
    if value in LANGS:
        st.session_state["lang_pref"] = value


def keep_lang_in_url():
    """Write the language into the address on every run (page changes can drop query parameters)."""
    if st.query_params.get("lang") != lang():
        st.query_params["lang"] = lang()


def is_ar() -> bool:
    return lang() == "ar"


def L(en: str, ar: str) -> str:
    return ar if is_ar() else en
