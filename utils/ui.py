"""Streamlit helpers: styling, splash screen, formatting, cached loading, shared sidebar."""
from __future__ import annotations

import html
import json

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from . import calc, data, settings
from .i18n import L, is_ar

C = settings.COLORS
LRI, PDI = "⁦", "⁩"  # keep numbers left-to-right inside Arabic text

AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
EN_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def lkey(name: str, default):
    """Widget key that survives a language switch.

    Choice widgets (radio, selectbox, ...) get a new identity when their translated labels change, which
    would reset them. So each language has its own widget key, started from one stored value 'v_<name>'.
    """
    canon = "v_" + name
    st.session_state.setdefault(canon, default)
    key = f"{name}__{'ar' if is_ar() else 'en'}"
    if key not in st.session_state:
        st.session_state[key] = st.session_state[canon]
    return key


def sync(name: str):
    """Copy the widget value of the current language to the stored value."""
    key = f"{name}__{'ar' if is_ar() else 'en'}"
    if key in st.session_state:
        st.session_state["v_" + name] = st.session_state[key]


def val(name: str):
    return st.session_state.get("v_" + name)


def forget(*names):
    """Drop the per-language widget keys (used by reset buttons)."""
    for n in names:
        for lg in ("en", "ar"):
            st.session_state.pop(f"{n}__{lg}", None)


def tr(msg) -> str:
    """Translate a (en, ar) tuple coming from the calculation module."""
    if isinstance(msg, tuple):
        return L(*msg)
    return str(msg)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def ltr(s: str) -> str:
    return f"{LRI}{s}{PDI}"


def num(x, digits=0) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return L("n/a", "غير متاح")
    return ltr(f"{x:,.{digits}f}")


def pct(x, digits=1, sign=True) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return L("n/a", "غير متاح")
    s = f"{x:+,.{digits}f}%" if sign else f"{x:,.{digits}f}%"
    return ltr(s.replace("-", "−"))


def pct_plain(x, digits=1) -> str:
    """For tables (no direction marks)."""
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "—"
    return f"{x:+.{digits}f}%"


def sar(x, digits=0) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return L("n/a", "غير متاح")
    return f"{num(x, digits)} {L('SAR', 'ريال')}"


def sar_g(x, karat=24, digits=0) -> str:
    """Gold price per gram for a karat, in SAR."""
    return f"{num(x, digits)} {L('SAR/g', 'ريال/جرام')} ({L(f'{karat}K', f'عيار {karat}')})"


def sar_bbl(x, digits=0) -> str:
    return f"{num(x, digits)} {L('SAR/barrel', 'ريال/برميل')}"


def usd(x, digits=0) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "غير متاح"
    return ltr(f"${x:,.{digits}f}")


def date_ar(d) -> str:
    """Date in the current language (kept the old name so all pages use one function)."""
    d = pd.Timestamp(d)
    return f"{d.day} {AR_MONTHS[d.month - 1]} {d.year}" if is_ar() else f"{d.day} {EN_MONTHS[d.month - 1]} {d.year}"


def month_ar(d) -> str:
    d = pd.Timestamp(d)
    return f"{AR_MONTHS[d.month - 1]} {d.year}" if is_ar() else f"{EN_MONTHS[d.month - 1]} {d.year}"


def corr_text(r) -> str:
    return num(r, 2) if not np.isnan(r) else L("n/a", "غير متاح")


def esc(s) -> str:
    return html.escape(str(s))


# ---------------------------------------------------------------------------
# Data (cached)
# ---------------------------------------------------------------------------
def _mtime(path):
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0


@st.cache_data(show_spinner=False)
def _load(mtime):
    return data.load()


@st.cache_data(show_spinner=False)
def _events(mtime):
    return data.load_events()


@st.cache_data(show_spinner=False)
def _survey(mtime):
    return calc.load_survey(settings.SURVEY_FILE)


def get_data() -> pd.DataFrame:
    try:
        return _load(_mtime(settings.DATA_FILE))
    except data.DataError as e:
        st.error(str(e))
        st.stop()


def get_events() -> pd.DataFrame:
    return _events(_mtime(settings.EVENTS_FILE))


def get_survey():
    return _survey(_mtime(settings.SURVEY_FILE))


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
  font-family: {settings.FONT_FAMILY};
}}
.stApp h1 {{ font-weight: 800; letter-spacing: 0; }}
.stApp h2, .stApp h3 {{ font-weight: 700; letter-spacing: 0; }}
/* numbers typed in inputs stay left-to-right */
[data-testid="stNumberInput"] input, [data-testid="stDateInput"] input {{ direction: ltr; text-align: right; }}
/* charts keep their own left-to-right layout */
[data-testid="stPlotlyChart"], [data-testid="stPlotlyChart"] * {{ direction: ltr; }}

.ey-hero {{ padding: 8px 0 14px 0; }}
.ey-kicker {{ color: {C['gold']}; font-weight: 700; font-size: .95rem; margin-bottom: 4px; }}
.ey-hero h1 {{ font-size: clamp(1.9rem, 4.2vw, 2.8rem); margin: 0 0 8px 0; color: {C['text']}; }}
.ey-lead {{ font-size: 1.08rem; color: {C['muted']}; max-width: 46rem; line-height: 1.9; }}
.ey-meta {{ display:inline-block; margin-top: 10px; padding: 4px 12px; border-radius: 999px;
  background: #EFE7D6; color: {C['text']}; font-size: .86rem; }}

.ey-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 14px 0 6px 0; }}
.ey-grid.g2 {{ grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}

.ey-card {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 16px;
  padding: 16px 18px; box-shadow: 0 1px 2px rgba(32,42,38,.04), 0 4px 14px rgba(32,42,38,.04); }}
.ey-card .lbl {{ color: {C['muted']}; font-size: .92rem; font-weight: 500; }}
.ey-card .val {{ color: {C['text']}; font-size: clamp(1.35rem, 2.2vw, 1.75rem); white-space: nowrap; font-weight: 800; margin: 4px 0 2px 0; line-height: 1.3; }}
.ey-card .val.up {{ color: {C['up']}; }} .ey-card .val.down {{ color: {C['down']}; }}
.ey-card .desc {{ color: {C['muted']}; font-size: .84rem; line-height: 1.7; }}
.ey-card .scope {{ display:inline-block; margin-top: 8px; font-size: .76rem; color: {C['gold']};
  border: 1px solid #E6D6B3; border-radius: 999px; padding: 1px 9px; background: #FBF7EE; }}

.ey-q {{ font-weight: 700; color: {C['text']}; font-size: 1.05rem; margin: 6px 0 2px 0; }}
.ey-insight {{ background: #FBF7EE; border: 1px solid #EADBB9;
  border-radius: 12px; padding: 12px 16px; margin: 6px 0 12px 0; line-height: 1.9; color: {C['text']}; }}
.ey-insight b {{ color: {C['gold']}; }}
.ey-note {{ color: {C['muted']}; font-size: .88rem; line-height: 1.8; }}

.ey-btn {{ display:inline-block; padding: 9px 20px; border-radius: 12px; font-weight: 700; text-decoration: none !important;
  border: 1px solid {C['gold']}; color: {C['gold']} !important; background: #FFFFFF; }}
.ey-btn:hover {{ background: #FBF7EE; }}

.ey-invoice {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 18px; padding: 22px 22px 14px 22px;
  box-shadow: 0 6px 24px rgba(32,42,38,.06); }}
.ey-invoice .head {{ color: {C['muted']}; font-weight: 700; font-size: .95rem; }}
.ey-invoice .big {{ font-size: clamp(1.6rem, 4vw, 2.3rem); font-weight: 800; color: {C['text']}; margin: 4px 0 2px 0; }}
.ey-invoice .sub {{ color: {C['muted']}; font-size: .9rem; margin-bottom: 12px; }}
.ey-invoice table {{ width: 100%; border-collapse: collapse; font-size: .95rem; }}
.ey-invoice table, .ey-invoice tr {{ border: none !important; background: transparent !important; }}
.ey-invoice td {{ padding: 9px 2px; border: none !important; border-top: 1px dashed {C['border']} !important; vertical-align: top; background: transparent !important; }}
.ey-invoice td.v {{ white-space: nowrap; font-weight: 700; }}
@media (max-width: 520px) {{ .ey-invoice td.v {{ white-space: normal; }} .ey-invoice td:first-child {{ width: 50%; }} }}
.ey-invoice tr.total td {{ border-top: 2px solid {C['text']} !important; font-size: 1.05rem; }}
.ey-invoice .foot {{ color: {C['muted']}; font-size: .84rem; margin-top: 10px; line-height: 1.8; }}

.ey-badge {{ display:inline-block; padding: 3px 12px; border-radius: 999px; font-weight: 700; font-size: .9rem; }}
.ey-badge.below {{ background:#E7F2EE; color:{C['up']}; }}
.ey-badge.within {{ background:#F3EEE2; color:{C['gold']}; }}
.ey-badge.above {{ background:#F7E9E9; color:{C['down']}; }}
.ey-demo {{ background:#FFF4D6; border:1px dashed #C9A659; border-radius:10px; padding:8px 12px; font-weight:700; }}
</style>
"""


RTL_CSS = """
<style>
[data-testid="stMain"], [data-testid="stSidebarContent"], [data-baseweb="popover"] { direction: rtl; }
.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], .ey-hero, .ey-card, .ey-insight,
.ey-note, .ey-invoice, .ey-q { direction: rtl; text-align: right; }
.ey-insight { border-right: 4px solid #8A641D; border-left: 1px solid #EADBB9; }
.ey-invoice td.v { text-align: left; }
</style>
"""
LTR_CSS = """
<style>
.ey-insight { border-left: 4px solid #8A641D; border-right: 1px solid #EADBB9; }
.ey-invoice td.v { text-align: right; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(RTL_CSS if is_ar() else LTR_CSS, unsafe_allow_html=True)


def lang_toggle():
    """English / العربية switch at the top of every page (keeps the page and inputs)."""
    st.session_state.setdefault("lang", "en")
    with st.container(horizontal=True, horizontal_alignment="left" if is_ar() else "right"):
        st.radio("Language / اللغة", ["en", "ar"], key="lang", horizontal=True, label_visibility="collapsed",
                 format_func={"en": "English", "ar": "العربية"}.get, width="content")


SPLASH = f"""
<style>
#ey-splash {{ position: fixed; inset: 0; z-index: 2147483000; background: {C['bg']};
  display: flex; align-items: center; justify-content: center; flex-direction: column;
  transition: opacity .45s ease, visibility .45s ease;
  animation: eyOut .4s ease 3.2s forwards; /* safety net if the timer below does not run */ }}
#ey-splash.ey-out {{ opacity: 0; visibility: hidden; pointer-events: none; }}
#ey-splash .logo {{ font-family: {settings.FONT_FAMILY}; font-size: clamp(3.4rem, 12vw, 6rem); font-weight: 800;
  background: linear-gradient(100deg, {C['gold']} 0%, {C['gold']} 40%, #E9CF8C 50%, {C['gold']} 60%, {C['gold']} 100%);
  background-size: 250% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: eyIn .5s ease both, eyShine 1.1s ease .2s both; line-height: 1.2; }}
#ey-splash .tag {{ font-family: {settings.FONT_FAMILY}; color: {C['muted']}; letter-spacing: .3em; font-size: .9rem;
  animation: eyIn .6s ease .15s both; }}
#ey-skip {{ position: absolute; top: 18px; left: 18px; }}
#ey-skip label {{ cursor: pointer; color: {C['muted']}; border: 1px solid {C['border']}; background: #fff;
  border-radius: 999px; padding: 4px 14px; font-family: {settings.FONT_FAMILY}; font-size: .85rem; }}
#ey-skip-box {{ display: none; }}
#ey-skip-box:checked + #ey-splash {{ display: none; }}
@keyframes eyIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes eyShine {{ from {{ background-position: 100% 0; }} to {{ background-position: 0 0; }} }}
@keyframes eyOut {{ to {{ opacity: 0; visibility: hidden; pointer-events: none; }} }}
@media (prefers-reduced-motion: reduce) {{ #ey-splash {{ display: none !important; }} }}
</style>
<input type="checkbox" id="ey-skip-box">
<div id="ey-splash" aria-label="EYAR">
  <div id="ey-skip"><label for="ey-skip-box" role="button" tabindex="0"
    onclick="var r=document.getElementById('ey-splash-root'); if (r) r.remove();">Skip · تخطي</label></div>
  <div class="logo">عيار</div>
  <div class="tag">EYAR</div>
</div>
"""


def splash_once():
    """Show the logo intro only on the first run of the session.

    A tiny script inserts the overlay into the page itself, so the CSS animation starts at that
    moment. The overlay hides itself with CSS (no timer), becomes click-through when it ends,
    and is never inserted again in the same session.
    """
    if st.session_state.get("_splash_shown"):
        return
    st.session_state["_splash_shown"] = True
    script = (
        "<script>(function(){try{"
        "var d=window.parent.document;"
        "if(d.getElementById('ey-splash-root')) return;"
        "var root=d.createElement('div'); root.id='ey-splash-root';"
        "root.innerHTML=" + json.dumps(SPLASH) + ";"
        "d.body.appendChild(root);"
        # the timer runs in the page itself, so it keeps working after this small frame is removed
        "var sc=d.createElement('script');"
        "sc.textContent=" + json.dumps(
            "setTimeout(function(){var s=document.getElementById('ey-splash'); if(s) s.classList.add('ey-out');}, 1250);"
            "setTimeout(function(){var r=document.getElementById('ey-splash-root'); if(r) r.remove();}, 1800);"
        ) + ";"
        "d.body.appendChild(sc);"
        "}catch(e){}})();</script>"
    )
    components.html(script, height=0)


# ---------------------------------------------------------------------------
# Small HTML components
# ---------------------------------------------------------------------------
def cards(items: list[dict], cols: int = 4):
    cls = {4: "", 3: "g3", 2: "g2"}.get(cols, "")
    parts = []
    for it in items:
        tone = it.get("tone", "")
        scope = f'<div class="scope">{esc(it["scope"])}</div>' if it.get("scope") else ""
        parts.append(
            f'<div class="ey-card"><div class="lbl">{esc(it["label"])}</div>'
            f'<div class="val {tone}">{it["value"]}</div>'
            f'<div class="desc">{it.get("desc", "")}</div>{scope}</div>'
        )
    st.markdown(f'<div class="ey-grid {cls}">{"".join(parts)}</div>', unsafe_allow_html=True)


def question(text: str):
    st.markdown(f'<div class="ey-q">{esc(text)}</div>', unsafe_allow_html=True)


def insight(text_html: str):
    st.markdown(f'<div class="ey-insight">{text_html}</div>', unsafe_allow_html=True)


def note(text_html: str):
    st.markdown(f'<div class="ey-note">{text_html}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar (shared part)
# ---------------------------------------------------------------------------
def sidebar_info(df: pd.DataFrame):
    with st.sidebar:
        st.markdown(f"### {L('EYAR', 'عيار')} <span style='color:{C['gold']}'>{L('عيار', 'EYAR')}</span>", unsafe_allow_html=True)
        st.caption(L("Understand gold's moves, and the price of your piece.", "افهم حركة الذهب، وافهم سعر قطعتك."))
        st.markdown(L(
            "**About the data:** daily gold futures prices and WTI crude oil spot prices, merged by gold trading day. "
            "Shown in SAR (3.75 SAR per USD, 31.1035 g per ounce).",
            "**عن البيانات:** أسعار يومية لعقود الذهب الآجلة وسعر نفط خام غرب تكساس الفوري، مدموجة حسب أيام تداول الذهب. "
            "معروضة بالريال (3.75 ريال للدولار، و31.1035 جرام للأونصة).",
        ))
        st.markdown(
            f"**{L('Sources', 'المصادر')}:** [{settings.SOURCES['gold'][0]}]({settings.SOURCES['gold'][1]}), "
            f"[{settings.SOURCES['oil'][0]}]({settings.SOURCES['oil'][1]})"
        )
        st.markdown(L(
            f"**Period:** {date_ar(df['Date'].min())} to {date_ar(df['Date'].max())} ({num(len(df))} trading days). "
            "Historical data, frozen; it does not update automatically.",
            f"**الفترة:** من {date_ar(df['Date'].min())} إلى {date_ar(df['Date'].max())} "
            f"({num(len(df))} يوم تداول). بيانات تاريخية مجمدة، لا تتحدث تلقائيًا.",
        ))
