"""Page 1: Discover gold / اكتشف الذهب (the analysis page with filters)."""
import numpy as np
import pandas as pd
import streamlit as st

from utils import analysis as A
from utils import charts, settings, ui
from utils.data import filter_period
from utils.i18n import L

df = ui.get_data()
dmin, dmax = df["Date"].min().date(), df["Date"].max().date()
CFG = {"displayModeBar": False}

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
DEFAULTS = {"f_view": "price", "f_period": (dmin, dmax), "f_assets": ["gold", "oil"]}


def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state["v_" + k] = v
    ui.forget(*DEFAULTS)


VIEW_LABELS = {"price": L("Price (SAR)", "السعر (ريال)"), "index": L("Relative change (start = 100)", "التغير النسبي (بداية الفترة = 100)")}
ASSET_LABELS = {"gold": L("Gold", "الذهب"), "oil": L("Oil", "النفط")}

with st.sidebar:
    st.divider()
    st.markdown(f"#### {L('Filters', 'الفلاتر')}")
    st.selectbox(L("View type", "نوع العرض"), list(VIEW_LABELS), format_func=VIEW_LABELS.get,
                 key=ui.lkey("f_view", DEFAULTS["f_view"]), on_change=ui.sync, args=("f_view",),
                 help=L("Price: each asset on its own axis. Relative change: both start at 100 for easy comparison.",
                        "السعر: كل أصل على محوره الخاص. التغير النسبي: يبدأ كل أصل من 100 لتسهيل المقارنة."))
    st.slider(L("Period", "الفترة الزمنية"), min_value=dmin, max_value=dmax, format="YYYY-MM-DD",
              key=ui.lkey("f_period", DEFAULTS["f_period"]), on_change=ui.sync, args=("f_period",))
    st.multiselect(L("Assets to compare", "الأصول في المقارنة"), list(ASSET_LABELS), format_func=ASSET_LABELS.get,
                   key=ui.lkey("f_assets", DEFAULTS["f_assets"]), on_change=ui.sync, args=("f_assets",),
                   placeholder=L("Choose an asset", "اختاري أصلًا"))
    st.button(L("Reset filters", "إعادة تعيين الفلاتر"), on_click=reset_filters, icon=":material/restart_alt:", width="stretch")
    st.caption(L("Filters affect this page. Global events and holding periods use the full data, as noted next to them.",
                 "الفلاتر تؤثر على هذه الصفحة. الأحداث العالمية ومدد الاحتفاظ تستخدم كامل البيانات، وهذا مكتوب بجانبها."))

view = ui.val("f_view")
start, end = ui.val("f_period")
assets = ui.val("f_assets")
d = filter_period(df, start, end)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    f"""<div class="ey-hero">
    <div class="ey-kicker">{L('EYAR | Discover gold', 'عيار | اكتشف الذهب')}</div>
    <h1>{L('Does gold always go up?', 'هل الذهب دائمًا يرتفع؟')}</h1>
    <div class="ey-lead">{L("The idea started with a question to my grandmother about how gold relates to oil and world events. Here I tested that idea with historical data.",
                            "بدأت الفكرة بسؤال لجدتي عن علاقة الذهب بالنفط والأحداث العالمية. هنا اختبرت هذه الفكرة باستخدام بيانات تاريخية.")}</div>
    <div class="ey-meta">{L('Latest data', 'آخر بيانات متاحة')}: {ui.date_ar(dmax)} · {L('historical data, not live prices', 'بيانات تاريخية وليست أسعارًا مباشرة')}</div>
    </div>""",
    unsafe_allow_html=True,
)
with st.container(horizontal=True, gap="small"):
    st.markdown(f'<a class="ey-btn" href="#results" target="_self">{L("Explore the results", "استكشف النتائج")}</a>',
                unsafe_allow_html=True, width="content")
    if st.button(L("Price your piece", "احسب قطعتك"), type="primary", icon=":material/calculate:"):
        st.switch_page("views/calculator.py")

if len(d) < 2:
    st.warning(L("The selected period is too short (fewer than two trading days). Widen it in the sidebar.",
                 "الفترة المختارة قصيرة جدًا ولا تحتوي يومي تداول على الأقل. وسّعي الفترة من الشريط الجانبي."))
    st.stop()
small = len(d) < settings.MIN_ROWS
if small:
    st.info(L(f"The selected period has only {len(d)} trading days. Some statistics need at least {settings.MIN_ROWS}, so they are hidden.",
              f"الفترة المختارة فيها {len(d)} يوم تداول فقط. بعض الإحصائيات تحتاج {settings.MIN_ROWS} يومًا على الأقل، فأخفيناها."))

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
S = A.period_summary(d)
g0, g1 = d["Gold_SAR_g"].iloc[0], d["Gold_SAR_g"].iloc[-1]
gpeak = d.loc[d["Close"].idxmax(), "Gold_SAR_g"]
dd = A.max_drawdown(d)
corr = A.correlations(d)
hold = A.holding_table(df, [1]).iloc[0]
SCOPE_P = L("Selected period", "الفترة المختارة")

ui.cards([
    {"label": L("Gold price change in the period", "تغير سعر الذهب خلال الفترة"), "value": ui.pct(S["change_pct"]),
     "tone": "up" if S["change_pct"] >= 0 else "down",
     "desc": L(f"From {ui.sar_g(g0)} ({ui.date_ar(S['start_date'])}) to {ui.sar_g(g1)} ({ui.date_ar(S['end_date'])}).",
               f"من {ui.sar_g(g0)} ({ui.date_ar(S['start_date'])}) إلى {ui.sar_g(g1)} ({ui.date_ar(S['end_date'])})."),
     "scope": SCOPE_P},
    {"label": L("Largest fall from a peak", "أكبر انخفاض من قمة"), "value": ui.pct(dd["value"]), "tone": "down" if dd["value"] < 0 else "",
     "desc": L(f"Deepest fall below a previous high, reached in {ui.month_ar(dd['date'])}.",
               f"أكبر نزول تحت أعلى سعر سابق، وصل إليه في {ui.month_ar(dd['date'])}.") if dd["value"] < 0
     else L("No fall below an earlier peak in this period.", "لم ينزل السعر تحت قمة سابقة داخل هذه الفترة."),
     "scope": L("Peaks inside the selected period", "من قمم الفترة المختارة")},
    {"label": L("Daily return correlation: gold and oil", "ارتباط العوائد اليومية: الذهب والنفط"),
     "value": L("not enough", "غير كافٍ") if small or corr["n_returns"] < settings.MIN_ROWS else ui.corr_text(corr["returns"]),
     "desc": L(f"{A.corr_strength(corr['returns'], 'en')}. A value near zero means no clear linear relationship in this sample; it does not prove there is no effect.",
               f"{A.corr_strength(corr['returns'], 'ar')}. القيمة القريبة من الصفر تعني غياب علاقة خطية واضحة في هذه العينة، ولا تثبت انعدام أي تأثير.")
     if not small else L("Needs more days.", "تحتاج أيامًا أكثر."),
     "scope": SCOPE_P},
    {"label": L("~1-year holds that ended with a positive return", "احتفاظ لسنة تقريبًا انتهى بعائد موجب"),
     "value": ui.pct(hold["positive_pct"], sign=False),
     "desc": L(f"Share of tested cases ({ui.num(hold['tested'])} buy dates), not the size of the profit or a guarantee.",
               f"نسبة الحالات المختبرة ({ui.num(hold['tested'])} تاريخ شراء)، وليست مقدار الربح أو ضمانًا للمستقبل."),
     "scope": L("Full study period", "كامل فترة الدراسة")},
])

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
st.markdown('<div id="results"></div>', unsafe_allow_html=True)
st.subheader(L("Results", "النتائج"))
tabs = st.tabs([L("Price journey", "رحلة السعر"), L("Yearly performance", "أداء السنوات"), L("Gold and oil", "الذهب والنفط"),
                L("World events", "الأحداث العالمية"), L("Risk", "المخاطر"), L("Data and statistics", "البيانات والإحصائيات")])

# a. price journey ------------------------------------------------------------
with tabs[0]:
    ui.question(L("How did the gold price change in the selected period?", "كيف تغير سعر الذهب خلال الفترة المختارة؟"))
    if not assets:
        st.info(L("Choose gold or oil in “Assets to compare” in the sidebar.", "اختاري الذهب أو النفط من «الأصول في المقارنة» في الشريط الجانبي."))
    else:
        st.plotly_chart(charts.journey(d, view, assets), theme=None, config=CFG, key="disc_journey")
        below_peak = A.pct_change(S["peak_price"], S["end_price"])
        if abs(below_peak) < 0.05:
            peak_txt = L("The period ended at its highest close.", "وانتهت الفترة عند أعلى إغلاق فيها.")
        else:
            peak_txt = L(f"The highest close was {ui.sar_g(gpeak)} on {ui.date_ar(S['peak_date'])}, and the end price is {ui.pct(abs(below_peak), sign=False)} below it.",
                         f"أعلى إغلاق كان {ui.sar_g(gpeak)} في {ui.date_ar(S['peak_date'])}، والسعر في نهاية الفترة أقل منه بنسبة {ui.pct(abs(below_peak), sign=False)}.")
        ui.insight(L(f"<b>Insight:</b> gold started the period at {ui.sar_g(g0)} and ended at {ui.sar_g(g1)} ({ui.pct(S['change_pct'])}). {peak_txt} The rise was not a straight line.",
                     f"<b>الاستنتاج:</b> بدأ الذهب الفترة عند {ui.sar_g(g0)} وانتهى عند {ui.sar_g(g1)} (تغير {ui.pct(S['change_pct'])}). {peak_txt} الارتفاع لم يكن بخط مستقيم."))
        if "oil" in assets and (d["Oil_Price"] <= 0).any():
            ui.note(L("Note: the oil price was negative on 20 April 2020 (an unusual event in the futures market), so its line drops sharply.",
                      "ملاحظة: سعر النفط كان سالبًا في 20 أبريل 2020 (حدث استثنائي في سوق العقود)، لذلك يظهر هبوط حاد في خطه."))
    with st.expander(L("More explanation", "شرح إضافي")):
        st.markdown(L(
            "- **Price:** gold futures close converted to SAR per gram of 24K, and oil in SAR per barrel. Each has its own axis because the units differ.\n"
            "- **Relative change:** each price divided by the first price of the period × 100, so both start at 100 and can share one axis.\n"
            "- The dot marks the highest gold close in the period.",
            "- **السعر:** إغلاق عقود الذهب الآجلة محوّلًا إلى ريال لكل جرام عيار 24، والنفط بالريال للبرميل. لكل أصل محور مستقل لأن الوحدتين مختلفتان.\n"
            "- **التغير النسبي:** نقسم كل سعر على سعر أول يوم في الفترة ونضرب في 100، فيبدأ الأصلان من 100 ويمكن مقارنتهما على محور واحد.\n"
            "- النقطة على الخط تحدد أعلى إغلاق للذهب في الفترة."))

# b. yearly returns ------------------------------------------------------------
with tabs[1]:
    ui.question(L("Does gold rise every year?", "هل يرتفع الذهب كل سنة؟"))
    y = A.yearly_returns(d, df)
    st.plotly_chart(charts.yearly_bars(y), theme=None, config=CFG, key="disc_yearly")
    complete = y[~y["partial"]]
    n_up = int((y["return"] > 0).sum())
    txt = L(f"<b>Insight:</b> gold rose in {n_up} of {len(y)} years shown.", f"<b>الاستنتاج:</b> ارتفع الذهب في {n_up} من {len(y)} سنة ظاهرة في الفترة.")
    if len(complete):
        bi, wi = complete["return"].idxmax(), complete["return"].idxmin()
        txt += L(f" Best complete year: {int(complete.loc[bi, 'Year'])} ({ui.pct(complete.loc[bi, 'return'])}); weakest: {int(complete.loc[wi, 'Year'])} ({ui.pct(complete.loc[wi, 'return'])}). Gold does not rise every year, and a large part of the gain can come from a few years.",
                 f" أقوى سنة كاملة: {int(complete.loc[bi, 'Year'])} ({ui.pct(complete.loc[bi, 'return'])})، وأضعف سنة كاملة: {int(complete.loc[wi, 'Year'])} ({ui.pct(complete.loc[wi, 'return'])}). الذهب لا يرتفع كل سنة، وجزء كبير من المكاسب قد يأتي في سنوات قليلة.")
    else:
        txt += L(" No complete year is inside the selected period.", " لا توجد سنة كاملة داخل الفترة المختارة.")
    ui.insight(txt)
    ui.note(L("Yearly return = change from the first close to the last close inside the same year (the notebook method). It differs slightly from comparing with the previous year's last close. * = partial year (cut by the filter, or not finished in the data). Hatched bars and ▼ mean a fall, ▲ means a rise.",
              "العائد السنوي = التغير من أول إغلاق إلى آخر إغلاق داخل السنة نفسها، وهي طريقة النوتبوك. وهي تختلف قليلًا عن مقارنة آخر إغلاق بآخر إغلاق في السنة السابقة. العلامة * تعني سنة جزئية. الأعمدة المخططة والسهم ▼ تعني انخفاضًا، والسهم ▲ يعني ارتفاعًا."))

# c. gold vs oil ---------------------------------------------------------------
with tabs[2]:
    ui.question(L("Do gold and oil move together?", "هل يتحرك الذهب والنفط معًا؟"))
    if set(assets) != {"gold", "oil"}:
        st.info(L("This comparison needs both assets. Choose gold and oil in “Assets to compare”.",
                  "هذه المقارنة تحتاج الأصلين. اختاري الذهب والنفط معًا من «الأصول في المقارنة»."))
    elif small:
        st.info(L("The period is too short for a useful correlation.", "الفترة قصيرة جدًا لحساب الارتباط بشكل مفيد."))
    else:
        ui.cards([
            {"label": L("Price correlation", "ارتباط الأسعار"), "value": ui.corr_text(corr["price"]),
             "desc": L(f"{A.corr_strength(corr['price'], 'en')}. Can be misleading because both prices change over time.",
                       f"{A.corr_strength(corr['price'], 'ar')}. قد يكون مضللًا لأن السعرين يتغيران مع الزمن."), "scope": SCOPE_P},
            {"label": L("Daily return correlation", "ارتباط العوائد اليومية"), "value": ui.corr_text(corr["returns"]),
             "desc": L(f"{A.corr_strength(corr['returns'], 'en')}. Measures whether they move the same way on the same day.",
                       f"{A.corr_strength(corr['returns'], 'ar')}. يقيس هل يتحركان في نفس اليوم بنفس الاتجاه."),
             "scope": f"{SCOPE_P} · {ui.num(corr['n_returns'])} {L('days', 'يومًا')}"},
        ], cols=2)
        if st.toggle(L("Compare both paths starting at 100", "مقارنة مساري الأصلين بدءًا من 100"), value=True, key="disc_cmp100"):
            st.plotly_chart(charts.journey(d, "index", ["gold", "oil"]), theme=None, config=CFG, key="disc_index100")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{L('Daily returns: each dot is a trading day', 'العوائد اليومية: كل نقطة يوم تداول')}**")
            st.plotly_chart(charts.scatter_returns(d), theme=None, config=CFG, key="disc_scatter")
        with c2:
            st.markdown(f"**{L('Correlation heatmap', 'مصفوفة الارتباط (Correlation heatmap)')}**")
            st.plotly_chart(charts.heatmap(d), theme=None, config=CFG, key="disc_heat")
        rr = corr["returns"]
        if abs(rr) < 0.1:
            rel = L("there is no clear linear relationship between their daily moves in this sample", "لا تظهر علاقة خطية واضحة بين حركتهما اليومية في هذه العينة")
        elif abs(rr) < 0.3:
            rel = L("the daily relationship is weak in this sample", "العلاقة اليومية ضعيفة في هذه العينة")
        else:
            rel = L("there is a noticeable daily relationship in this sample", "تظهر علاقة يومية ملحوظة في هذه العينة")
        ui.insight(L(f"<b>Insight:</b> the price correlation is {ui.corr_text(corr['price'])} ({A.corr_strength(corr['price'], 'en')}), but the daily return correlation is {ui.corr_text(rr)}: {rel}. Daily oil moves are not enough to explain daily gold moves here.",
                     f"<b>الاستنتاج:</b> ارتباط الأسعار {ui.corr_text(corr['price'])} ({A.corr_strength(corr['price'], 'ar')})، لكن ارتباط العوائد اليومية {ui.corr_text(rr)}: {rel}. لذلك حركة النفط اليومية لا تكفي لتفسير حركة الذهب اليومية هنا."))
    with st.expander(L("More explanation and limits", "شرح إضافي وحدود المقارنة")):
        st.markdown(L(
            "- **Correlation** is a number from −1 to +1. Near +1: they move together; near −1: opposite; near 0: no clear linear relationship.\n"
            "- A correlation near zero does not prove there is no effect; there may be a non-linear or delayed relationship.\n"
            "- **Different methods:** gold here is a futures price (GC=F); oil is a spot price (WTI).\n"
            "- Missing oil days were filled with the last known price in the notebook. Those days were not flagged in the file, so they cannot be identified here.\n"
            "- Oil returns are excluded when today's or the previous price is not positive (20 and 21 April 2020).\n"
            "- Correlation is not causation. Converting to SAR does not change correlations or percentages.",
            "- **الارتباط** رقم بين −1 و+1. قريب من +1: يتحركان معًا، قريب من −1: عكس بعض، قريب من 0: لا علاقة خطية واضحة.\n"
            "- الارتباط القريب من الصفر لا يثبت انعدام أي تأثير؛ قد توجد علاقة غير خطية أو متأخرة.\n"
            "- **اختلاف المنهجية:** الذهب هنا سعر عقود آجلة (GC=F)، والنفط سعر فوري لخام غرب تكساس (WTI).\n"
            "- أيام النفط الناقصة عُوّضت بآخر سعر معروف في النوتبوك. علامات الأيام المعوّضة لم تُحفظ في الملف، فلا يمكن تحديدها هنا.\n"
            "- استبعدنا عائد النفط في الأيام التي يكون فيها السعر الحالي أو السابق غير موجب (20 و21 أبريل 2020).\n"
            "- الارتباط لا يعني السببية. التحويل إلى الريال لا يغير الارتباط أو النسب."))

# d. events ----------------------------------------------------------------------
with tabs[3]:
    ui.question(L("Does gold rise during major world events?", "هل يرتفع الذهب وقت الأحداث العالمية الكبيرة؟"))
    ui.note(L("This section uses the full data (not the period filter) and counts trading sessions, not calendar days.",
              "هذا القسم يستخدم كامل البيانات (لا يتأثر بفلتر الفترة)، والقياس بجلسات التداول وليس بالأيام التقويمية."))
    events = ui.get_events()
    typ = A.typical_change(df, settings.EVENT_AFTER_LONG)
    rows, studies, names = [], {}, {}
    for ev in events.itertuples():
        name = L(ev.event_en, ev.event_ar)
        r = A.event_study(df, ev.date)
        studies[ev.event_en], names[ev.event_en] = r, name
        if r["ok"]:
            a30 = r["after_long"]
            verdict = (L("Above normal", "أعلى من المعتاد") if a30 > typ["q3"] else
                       (L("Below normal", "أقل من المعتاد") if a30 < typ["q1"] else L("Within normal", "ضمن المعتاد")))
            rows.append({L("Event", "الحدث"): name, L("Date", "التاريخ"): ui.date_ar(ev.date),
                         L("Reference day", "اليوم المرجعي"): ui.date_ar(r["base_date"]),
                         L("30 sessions before", "قبل 30 جلسة"): ui.pct_plain(r["before"]),
                         L("7 sessions after", "بعد 7 جلسات"): ui.pct_plain(r["after_short"]),
                         L("30 sessions after", "بعد 30 جلسة"): ui.pct_plain(r["after_long"]),
                         L("vs normal", "مقارنة بالمعتاد"): verdict})
        else:
            rows.append({L("Event", "الحدث"): name, L("Date", "التاريخ"): ui.date_ar(ev.date), L("Reference day", "اليوم المرجعي"): "—",
                         L("30 sessions before", "قبل 30 جلسة"): "—", L("7 sessions after", "بعد 7 جلسات"): "—",
                         L("30 sessions after", "بعد 30 جلسة"): "—", L("vs normal", "مقارنة بالمعتاد"): ui.tr(r["reason"])})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    ui.note(L("Reference day = last close before the event; all changes are measured from it.",
              "اليوم المرجعي = آخر إغلاق قبل الحدث، ومنه تُقاس كل النسب."))
    ui.note(L(f"Normal 30-session change of gold in the full data: average {ui.pct(typ['mean'])}, and half of all periods fall between {ui.pct(typ['q1'])} and {ui.pct(typ['q3'])} (first and third quartiles).",
              f"التغير المعتاد للذهب خلال 30 جلسة في كامل البيانات: المتوسط {ui.pct(typ['mean'])}، ونصف الفترات تقع بين {ui.pct(typ['q1'])} و{ui.pct(typ['q3'])} (الربعان الأول والثالث)."))
    choice = st.selectbox(L("Choose an event to see the gold path around it", "اختاري حدثًا لعرض مسار الذهب حوله"), list(studies),
                          format_func=names.get, key=ui.lkey("disc_event", list(studies)[0]), on_change=ui.sync, args=("disc_event",))
    r = studies[choice]
    if r["ok"]:
        st.plotly_chart(charts.event_window(r["window"], names[choice], settings.EVENT_AFTER_SHORT, settings.EVENT_AFTER_LONG),
                        theme=None, config=CFG, key="disc_event_chart")
        ui.cards([
            {"label": L("30 sessions before", "قبل الحدث بـ30 جلسة"), "value": ui.pct(r["before"]), "tone": "up" if r["before"] >= 0 else "down",
             "desc": L("Change up to the reference day.", "التغير حتى اليوم المرجعي.")},
            {"label": L("7 sessions after", "بعد 7 جلسات"), "value": ui.pct(r["after_short"]), "tone": "up" if r["after_short"] >= 0 else "down",
             "desc": L("From the reference day.", "من اليوم المرجعي.")},
            {"label": L("30 sessions after", "بعد 30 جلسة"), "value": ui.pct(r["after_long"]), "tone": "up" if r["after_long"] >= 0 else "down",
             "desc": L("From the reference day.", "من اليوم المرجعي.")},
        ], cols=3)
        base_sar = r["base_price"] / settings.OUNCE_IN_GRAMS * settings.DEFAULT_USD_TO_SAR
        ui.note(L(f"Reference day = last close before the event: {ui.date_ar(r['base_date'])} at {ui.sar_g(base_sar)}.",
                  f"اليوم المرجعي = آخر إغلاق قبل الحدث: {ui.date_ar(r['base_date'])} عند {ui.sar_g(base_sar)}."))
    else:
        st.info(ui.tr(r["reason"]) + L(" So we do not show a partial result.", " لذلك لا نعرض نتيجة ناقصة."))
    ui.insight(L("<b>Insight:</b> gold did not react the same way to every event: it fell, stayed within normal, or rose, and sometimes the move came before the event. This shows timing, not that the event caused it.",
                 "<b>الاستنتاج:</b> الذهب لم يتفاعل بنفس الطريقة مع كل حدث: قد ينزل أو يبقى ضمن المعتاد أو يرتفع، وأحيانًا تحدث الحركة قبل الحدث. هذه نتائج تزامن في الوقت، ولا تثبت أن الحدث هو السبب."))
    with st.expander(L("Limits of this section", "حدود هذا القسم")):
        st.markdown(L("- Only three events, so we cannot generalise.\n- Other factors (interest rates, the dollar, central banks) may move gold at the same time.\n- If 30 sessions are not available before or after an event, no result is shown.",
                      "- ثلاثة أحداث فقط، فلا يصح التعميم منها.\n- عوامل أخرى (الفائدة، الدولار، البنوك المركزية) قد تحرك الذهب في نفس الوقت.\n- عند عدم توفر 30 جلسة قبل الحدث أو بعده لا نعرض نتيجة."))

# e. risk ----------------------------------------------------------------------
with tabs[4]:
    ui.question(L("How far is gold below its earlier high, and how big are its daily moves?", "كم يبعد الذهب عن أعلى سعر سابق؟ وما حجم حركته اليومية؟"))
    st.plotly_chart(charts.drawdown_area(d["Date"], dd["series"]), theme=None, config=CFG, key="disc_dd")
    ui.note(L("Drawdown = how far the price is below the highest close reached before. Here the peaks are inside the selected period only.",
              "الانخفاض من القمة (Drawdown) = كم السعر تحت أعلى إغلاق وصل له قبل ذلك. هنا القمم محسوبة داخل الفترة المختارة فقط."))
    if dd["value"] < 0:
        ui.insight(L(f"<b>Insight:</b> the largest fall from a peak in the period was {ui.pct(dd['value'])} on {ui.date_ar(dd['date'])}. Buying near a peak can mean a wait before the price comes back.",
                     f"<b>الاستنتاج:</b> أكبر انخفاض من قمة داخل الفترة كان {ui.pct(dd['value'])} في {ui.date_ar(dd['date'])}. الشراء قرب القمة قد يعني انتظار فترة حتى يعود السعر."))
    if small:
        st.info(L("The period is too short for daily return statistics.", "الفترة قصيرة جدًا لإحصائيات العوائد اليومية."))
    else:
        rs = A.return_stats(d["Gold_Return"])
        rr_ = d.dropna(subset=["Gold_Return"])
        worst = rr_.loc[rr_["Gold_Return"].idxmin()]
        best = rr_.loc[rr_["Gold_Return"].idxmax()]
        ui.cards([
            {"label": L("Std. deviation of daily return", "الانحراف المعياري للعائد اليومي"), "value": ui.pct(rs["std"], 2, sign=False),
             "desc": L("A measure of typical volatility, not proof that gold moves this much every day.", "مقياس لحجم التذبذب المعتاد، وليس دليلًا أن الذهب يتحرك بهذا المقدار كل يوم.")},
            {"label": L("Where do half of the days fall?", "أين يقع نصف الأيام؟"), "value": f"{ui.pct(rs['q1'], 2)} {L('to', 'إلى')} {ui.pct(rs['q3'], 2)}",
             "desc": L("Between the first and third quartile of daily returns.", "بين الربع الأول والربع الثالث للعوائد اليومية.")},
            {"label": L("Extreme days (IQR rule)", "أيام متطرفة (قاعدة IQR)"), "value": ui.pct(rs["share_out"], sign=False),
             "desc": L(f"{ui.num(rs['n_out'])} of {ui.num(rs['n'])} days outside the IQR outlier detection limits ({ui.pct(rs['lower'], 2)} and {ui.pct(rs['upper'], 2)}). Kept, because they are real moves.",
                       f"{ui.num(rs['n_out'])} من {ui.num(rs['n'])} يوم خارج حدود اكتشاف القيم المتطرفة وفق قاعدة IQR ({ui.pct(rs['lower'], 2)} و{ui.pct(rs['upper'], 2)}). أبقيناها لأنها حركات حقيقية.")},
        ], cols=3)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{L('Distribution of daily returns', 'توزيع العوائد اليومية')}**")
            st.plotly_chart(charts.histogram(d["Gold_Return"], rs["lower"], rs["upper"]), theme=None, config=CFG, key="disc_hist")
        with c2:
            st.markdown(f"**{L('Up days vs down or flat days', 'الأيام الصاعدة مقابل الهابطة أو الثابتة')}**")
            st.plotly_chart(charts.up_down(A.up_down_by_year(d)), theme=None, config=CFG, key="disc_updown")
        with st.expander(L("Boxplot: the dots are the extreme days", "Boxplot: النقاط هي الأيام المتطرفة")):
            st.plotly_chart(charts.boxplot(d["Gold_Return"]), theme=None, config=CFG, key="disc_box")
        ud = A.up_down_by_year(d)
        up_share = ud["up"].sum() / (ud["up"].sum() + ud["down_flat"].sum()) * 100
        ui.insight(L(
            f"<b>Insight:</b> on about half of the days gold moved between {ui.pct(rs['q1'], 2)} and {ui.pct(rs['q3'], 2)}. The worst day was {ui.pct(worst['Gold_Return'])} ({ui.date_ar(worst['Date'])}) and the best {ui.pct(best['Gold_Return'])} ({ui.date_ar(best['Date'])}). Up days were {ui.pct(up_share, sign=False)} of all days. Similar numbers of up and down days mean the direction of a day alone shows no clear pattern, but this does not prove prediction is impossible.",
            f"<b>الاستنتاج:</b> نصف الأيام تقريبًا تحرك فيها الذهب بين {ui.pct(rs['q1'], 2)} و{ui.pct(rs['q3'], 2)}. أسوأ يوم كان {ui.pct(worst['Gold_Return'])} ({ui.date_ar(worst['Date'])})، وأفضل يوم {ui.pct(best['Gold_Return'])} ({ui.date_ar(best['Date'])}). الأيام الصاعدة كانت {ui.pct(up_share, sign=False)} من الأيام. تقارب أيام الصعود والهبوط يعني أن اتجاه اليوم وحده لا يعطي نمطًا واضحًا، لكنه لا يثبت أن التنبؤ مستحيل."))
        ui.note(L("The dotted lines in the distribution are the IQR outlier detection limits: Q1 − 1.5 × IQR and Q3 + 1.5 × IQR. They help find unusual days; they are not a guaranteed range.",
                  "الخطان المنقطان في التوزيع هما حدود اكتشاف القيم المتطرفة وفق قاعدة IQR: الربع الأول − 1.5 × IQR، والربع الثالث + 1.5 × IQR. هي أداة لاكتشاف الأيام غير المعتادة، وليست نطاقًا مضمونًا."))

# f. data ----------------------------------------------------------------------
with tabs[5]:
    ui.question(L("What data are the results built on?", "ما البيانات التي بُنيت عليها النتائج؟"))
    show = pd.DataFrame({
        L("Date", "التاريخ"): d["Date"],
        L("Gold 24K (SAR/g)", "الذهب عيار 24 (ريال/جرام)"): d["Gold_SAR_g"],
        L("Oil (SAR/barrel)", "النفط (ريال/برميل)"): d["Oil_SAR_bbl"],
        L("Gold daily return (%)", "عائد الذهب اليومي (%)"): d["Gold_Return"],
        L("Oil daily return (%)", "عائد النفط اليومي (%)"): d["Oil_Return"],
        L("Below peak (%)", "تحت القمة (%)"): A.drawdown(d["Close"]),
    })
    date_col = L("Date", "التاريخ")
    with st.expander(L(f"Data preview: selected period ({ui.num(len(d))} rows)", f"معاينة البيانات: الفترة المختارة ({ui.num(len(d))} صف)"), expanded=True):
        st.dataframe(show.style.format(precision=2, na_rep="—"), hide_index=True, width="stretch", height=320,
                     column_config={date_col: st.column_config.DateColumn(format="YYYY-MM-DD")})
    with st.expander(L("Summary statistics", "الإحصائيات الوصفية (Summary statistics)"), expanded=True):
        desc = show.drop(columns=[date_col]).describe().T
        desc = desc.rename(columns={"count": L("count", "العدد"), "mean": L("mean", "المتوسط"), "std": L("std", "الانحراف المعياري"),
                                    "min": L("min", "الأدنى"), "25%": L("Q1", "الربع الأول"), "50%": L("median", "الوسيط"),
                                    "75%": L("Q3", "الربع الثالث"), "max": L("max", "الأعلى")})
        st.dataframe(desc.style.format(precision=2, na_rep="—"), width="stretch")
    st.download_button(L("Download the selected period (CSV)", "تنزيل بيانات الفترة المختارة (CSV)"),
                       show.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"eyar_{start}_{end}.csv", mime="text/csv", icon=":material/download:")
