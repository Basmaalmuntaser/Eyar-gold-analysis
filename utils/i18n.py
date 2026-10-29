"""Very small translation helper. English is the default language.

Usage:  L("English text", "النص العربي")
"""
import streamlit as st


def lang() -> str:
    return st.session_state.get("lang", "en")


def is_ar() -> bool:
    return lang() == "ar"


def L(en: str, ar: str) -> str:
    return ar if is_ar() else en
