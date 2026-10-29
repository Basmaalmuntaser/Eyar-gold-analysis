"""Plotly charts with the EYAR look."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import settings
from .i18n import L, is_ar

C = settings.COLORS
AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def base(fig: go.Figure, height: int = 380, title: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        title=dict(text=title, x=0.99 if is_ar() else 0.01, xanchor="right" if is_ar() else "left", font=dict(size=15, color=C["text"])) if title else None,
        font=dict(family=settings.FONT_FAMILY, size=13, color=C["text"]),
        paper_bgcolor=C["card"], plot_bgcolor=C["card"],
        margin=dict(l=96, r=16, t=56 if title else 28, b=56),
        hoverlabel=dict(font=dict(family=settings.FONT_FAMILY), bgcolor="#FFFFFF", bordercolor=C["border"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right" if is_ar() else "left", x=1 if is_ar() else 0, title=None),
        dragmode=False,
    )
    fig.update_xaxes(gridcolor="#EFEAE0", zerolinecolor="#D9D1C1", linecolor=C["border"], automargin=True)
    fig.update_yaxes(gridcolor="#EFEAE0", zerolinecolor="#D9D1C1", linecolor=C["border"], automargin=True,
                     title_standoff=26)
    return fig


EN_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _hover_dates(dates: pd.Series) -> list[str]:
    m = AR_MONTHS if is_ar() else EN_MONTHS
    return [f"{d.day} {m[d.month - 1]} {d.year}" for d in pd.to_datetime(dates)]


# ---------------------------------------------------------------------------
def journey(d: pd.DataFrame, view: str, assets: list[str]) -> go.Figure:
    """Gold (and optionally oil) path in SAR. 'price' -> separate axes; 'index' -> both start at 100."""
    G, O = "Gold_SAR_g", "Oil_SAR_bbl"
    dates = _hover_dates(d["Date"])
    show_gold, show_oil = "gold" in assets, "oil" in assets
    if view == "index":
        fig = go.Figure()
        if show_gold:
            g = d[G] / d[G].iloc[0] * 100
            fig.add_trace(go.Scatter(x=d["Date"], y=g, name=L("Gold", "الذهب"), line=dict(color=C["gold"], width=2.4),
                                     customdata=dates, hovertemplate="%{customdata}<br>" + L("Gold", "الذهب") + ": %{y:.1f}<extra></extra>"))
        if show_oil:
            o = d[O] / d[O].iloc[0] * 100
            fig.add_trace(go.Scatter(x=d["Date"], y=o, name=L("Oil", "النفط"), line=dict(color=C["oil"], width=1.8, dash="dot"),
                                     customdata=dates, hovertemplate="%{customdata}<br>" + L("Oil", "النفط") + ": %{y:.1f}<extra></extra>"))
        fig.add_hline(y=100, line_color="#B9B0A0", line_width=1)
        fig.update_yaxes(title=L("Level (start = 100)", "المستوى (البداية = 100)"))
        if show_gold:
            i = d[G].idxmax()
            fig.add_trace(go.Scatter(x=[d.loc[i, "Date"]], y=[d.loc[i, G] / d[G].iloc[0] * 100],
                                     mode="markers", marker=dict(size=10, color=C["gold"], line=dict(color="#fff", width=2)),
                                     name=L("Peak", "القمة"), hoverinfo="skip", showlegend=False))
        return base(fig, 420)

    rows = int(show_gold) + int(show_oil)
    titles = ([L("Gold, 24K (SAR per gram)", "الذهب عيار 24 (ريال للجرام)")] if show_gold else []) + ([L("Oil (SAR per barrel)", "النفط (ريال للبرميل)")] if show_oil else [])
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.09,
                        subplot_titles=titles, row_heights=[0.65, 0.35] if rows == 2 else None)
    r = 1
    if show_gold:
        fig.add_trace(go.Scatter(x=d["Date"], y=d[G], name=L("Gold", "الذهب"), line=dict(color=C["gold"], width=2.4),
                                 customdata=dates, hovertemplate="%{customdata}<br>%{y:,.1f} " + L("SAR/g", "ريال/جرام") + "<extra></extra>"), row=r, col=1)
        i = d[G].idxmax()
        fig.add_trace(go.Scatter(x=[d.loc[i, "Date"]], y=[d.loc[i, G]], mode="markers+text",
                                 marker=dict(size=10, color=C["gold"], line=dict(color="#fff", width=2)),
                                 text=[L("Peak ", "القمة ") + f"{d.loc[i, G]:,.0f}"], textposition="top left",
                                 textfont=dict(color=C["gold"]), showlegend=False,
                                 hovertemplate=L("Peak: ", "القمة: ") + f"{dates[i]}<br>%{{y:,.1f}}<extra></extra>"), row=r, col=1)
        r += 1
    if show_oil:
        fig.add_trace(go.Scatter(x=d["Date"], y=d[O], name=L("Oil", "النفط"), line=dict(color=C["oil"], width=1.6),
                                 customdata=dates, hovertemplate="%{customdata}<br>%{y:,.1f} " + L("SAR/barrel", "ريال/برميل") + "<extra></extra>"), row=r, col=1)
    fig.update_layout(showlegend=False)
    for a in fig.layout.annotations:
        a.update(x=1, xanchor="right", font=dict(size=13, color=C["muted"]))
    return base(fig, 460 if rows == 2 else 400)


def yearly_bars(y: pd.DataFrame) -> go.Figure:
    labels = [f"{int(r.Year)}*" if r.partial else str(int(r.Year)) for r in y.itertuples()]
    up = y["return"] >= 0
    fig = go.Figure(go.Bar(
        x=labels, y=y["return"],
        marker=dict(color=np.where(up, C["up"], C["down"]),
                    pattern=dict(shape=np.where(up, "", "/"), fgcolor="#FFFFFF", size=6, fillmode="overlay")),
        text=[f"{'▲' if v >= 0 else '▼'} {v:+.1f}%" for v in y["return"]], textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: %{y:+.1f}%<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="#9C9384", line_width=1)
    fig.update_yaxes(title=L("Yearly return (%)", "العائد السنوي (%)"))
    return base(fig, 380)


def scatter_returns(d: pd.DataFrame) -> go.Figure:
    b = d.dropna(subset=["Gold_Return", "Oil_Return"])
    fig = go.Figure(go.Scattergl(
        x=b["Oil_Return"], y=b["Gold_Return"], mode="markers",
        marker=dict(size=5, color=C["gold"], opacity=0.35),
        customdata=_hover_dates(b["Date"]),
        hovertemplate="%{customdata}<br>" + L("Oil", "النفط") + ": %{x:+.2f}%<br>" + L("Gold", "الذهب") + ": %{y:+.2f}%<extra></extra>",
    ))
    fig.update_xaxes(title=L("Oil daily return (%)", "العائد اليومي للنفط (%)"), zeroline=True)
    fig.update_yaxes(title=L("Gold daily return (%)", "العائد اليومي للذهب (%)"), zeroline=True)
    return base(fig, 400)


def heatmap(d: pd.DataFrame) -> go.Figure:
    names = {"Close": L("Gold price", "سعر الذهب"), "Oil_Price": L("Oil price", "سعر النفط"),
             "Gold_Return": L("Gold daily<br>return", "عائد الذهب<br>اليومي"), "Oil_Return": L("Oil daily<br>return", "عائد النفط<br>اليومي")}
    corr = d[list(names)].corr().rename(index=names, columns=names)
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=list(corr.columns), y=list(corr.index), zmin=-1, zmax=1,
        colorscale=[[0, C["oil"]], [0.5, "#FFFFFF"], [1, C["gold"]]],
        text=np.round(corr.values, 2), texttemplate="%{text:.2f}", textfont=dict(size=14),
        hovertemplate="%{y} / %{x}: %{z:.2f}<extra></extra>", colorbar=dict(thickness=10, title=None),
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickangle=0)
    fig = base(fig, 420)
    fig.update_layout(margin=dict(l=110, b=70))
    return fig


def event_window(w: pd.DataFrame, name: str, short: int, long: int) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=w["session"], y=w["index"], mode="lines", line=dict(color=C["gold"], width=2.6),
        customdata=_hover_dates(w["Date"]),
        hovertemplate=L("Session ", "الجلسة ") + "%{x} (%{customdata})<br>%{y:.1f}<extra></extra>",
    ))
    fig.add_hline(y=100, line_color="#B9B0A0", line_width=1)
    fig.add_vline(x=0, line_dash="dash", line_color=C["oil"])
    fig.add_annotation(x=0, y=1.02, yref="paper", text=L("Reference day", "اليوم المرجعي"), showarrow=False, font=dict(color=C["oil"]))
    for s in (short, long):
        fig.add_vline(x=s, line_dash="dot", line_color="#C9BFAE")
    fig.update_xaxes(title=L("Trading sessions from the reference day", "جلسات التداول من اليوم المرجعي"))
    fig.update_yaxes(title=L("Gold (reference = 100)", "الذهب (المرجع = 100)"))
    return base(fig, 380, name)


def drawdown_area(dates: pd.Series, dd: pd.Series) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=dates, y=dd, fill="tozeroy", line=dict(color=C["down"], width=1.4), fillcolor="rgba(183,68,68,.14)",
        customdata=_hover_dates(dates), hovertemplate="%{customdata}<br>%{y:.1f}% " + L("below the previous peak", "تحت القمة السابقة") + "<extra></extra>",
    ))
    fig.update_yaxes(title=L("Below peak (%)", "تحت القمة (%)"))
    return base(fig, 330)


def histogram(r: pd.Series, lower: float, upper: float) -> go.Figure:
    fig = go.Figure(go.Histogram(x=r.dropna(), nbinsx=70, marker=dict(color=C["gold"], line=dict(color="#fff", width=0.5)),
                                 hovertemplate="%{x}%<br>" + L("Days", "عدد الأيام") + ": %{y}<extra></extra>"))
    for v in (lower, upper):
        fig.add_vline(x=v, line_dash="dot", line_color=C["oil"])
    fig.update_xaxes(title=L("Gold daily return (%)", "العائد اليومي للذهب (%)"))
    fig.update_yaxes(title=L("Number of days", "عدد الأيام"))
    return base(fig, 330)


def boxplot(r: pd.Series) -> go.Figure:
    fig = go.Figure(go.Box(x=r.dropna(), name="", marker=dict(color=C["gold"], size=4, opacity=.6),
                           line=dict(color=C["gold"]), fillcolor="rgba(138,100,29,.12)", boxpoints="outliers",
                           hoverinfo="x"))
    fig.update_xaxes(title=L("Gold daily return (%)", "العائد اليومي للذهب (%)"))
    fig.update_yaxes(showticklabels=False)
    return base(fig, 230)


def up_down(t: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=t["Year"].astype(str), y=t["up"], name=L("Up days", "أيام صاعدة"), marker_color=C["up"],
                         hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Bar(x=t["Year"].astype(str), y=t["down_flat"], name=L("Down or flat days", "أيام هابطة أو ثابتة"),
                         marker=dict(color=C["down"], pattern=dict(shape="/", fgcolor="#FFFFFF", size=6, fillmode="overlay")),
                         hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title=L("Number of days", "عدد الأيام"))
    return base(fig, 360)


def hold_value(path: pd.DataFrame, amount: float) -> go.Figure:
    up = path["Value"].iloc[-1] >= amount
    fig = go.Figure(go.Scatter(
        x=path["Date"], y=path["Value"], mode="lines", line=dict(color=C["up"] if up else C["down"], width=2.4),
        customdata=_hover_dates(path["Date"]),
        hovertemplate="%{customdata}<br>%{y:,.0f} " + L("SAR", "ريال") + "<extra></extra>",
    ))
    fig.add_hline(y=amount, line_dash="dash", line_color="#9C9384",
                  annotation_text=L("Amount invested", "المبلغ الأصلي"), annotation_position="bottom right")
    fig.update_yaxes(title=L("Value (SAR)", "القيمة (ريال)"))
    return base(fig, 380)


def hold_by_buy_date(full: pd.DataFrame, years: int) -> go.Figure:
    n = years * settings.SESSIONS_PER_YEAR
    r = (full["Close"].shift(-n) / full["Close"] - 1) * 100
    fig = go.Figure(go.Scatter(x=full["Date"], y=r, mode="lines", line=dict(color=C["gold"], width=1.8),
                               customdata=_hover_dates(full["Date"]),
                               hovertemplate=L("Bought ", "شراء في ") + "%{customdata}<br>%{y:+.1f}%<extra></extra>"))
    fig.add_hline(y=0, line_color="#9C9384", line_width=1)
    fig.update_yaxes(title=L("Change after holding (%)", "التغير بعد المدة (%)"))
    fig.update_xaxes(title=L("Buy date", "تاريخ الشراء"))
    return base(fig, 340)
