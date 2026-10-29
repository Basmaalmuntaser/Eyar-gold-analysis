"""Page 2: Try holding / جرّب الاحتفاظ (historical holding experiment, all in SAR)."""
import pandas as pd
import streamlit as st

from utils import analysis as A
from utils import charts, settings, ui
from utils.i18n import L

df = ui.get_data()
dmin, dmax = df["Date"].min().date(), df["Date"].max().date()
CFG = {"displayModeBar": False}
TO_SAR_G = settings.DEFAULT_USD_TO_SAR / settings.OUNCE_IN_GRAMS   # USD per ounce -> SAR per gram (24K)

st.markdown(
    f"""<div class="ey-hero"><div class="ey-kicker">{L('EYAR | Try holding', 'عيار | جرّب الاحتفاظ')}</div>
    <h1>{L('If you had bought on a certain date and held, what would have happened?', 'لو اشتريت في تاريخ معين واحتفظت، ماذا كان سيحدث؟')}</h1>
    <div class="ey-lead">{L('A historical experiment on the gold price in the data, in SAR, before any costs, making charge or VAT.',
                            'تجربة تاريخية على سعر الذهب في البيانات بالريال، قبل أي تكاليف أو مصنعية أو ضريبة.')}</div></div>""",
    unsafe_allow_html=True,
)


def years_label(y):
    return {1: L("~1 year (252 sessions)", "سنة تقريبًا (252 جلسة)"),
            3: L("~3 years (756 sessions)", "3 سنوات تقريبًا (756 جلسة)"),
            5: L("~5 years (1,260 sessions)", "5 سنوات تقريبًا (1,260 جلسة)")}[y]


st.session_state.setdefault("h_buy", pd.Timestamp("2019-01-02").date())
st.session_state.setdefault("h_amount", 10_000.0)
with st.container(border=True):
    c1, c2, c3 = st.columns([1.2, 1, 1.4])
    buy = c1.date_input(L("Buy date", "تاريخ الشراء"), min_value=dmin, max_value=dmax, format="YYYY-MM-DD", key="h_buy")
    amount = c2.number_input(L("Amount (SAR)", "المبلغ (ريال)"), min_value=100.0, max_value=100_000_000.0, step=1_000.0, key="h_amount")
    years = c3.radio(L("Holding period", "مدة الاحتفاظ"), [1, 3, 5], format_func=years_label, horizontal=True,
                     key=ui.lkey("h_years", 3), on_change=ui.sync, args=("h_years",))

r = A.simulate_hold(df, buy, years, amount)
if not r["ok"]:
    if r["reason"] == "insufficient":
        last_ok = ui.date_ar(r["last_ok"]) if r["last_ok"] is not None else "—"
        st.warning(L(f"Not enough data: buying on {ui.date_ar(r['start_date'])} needs {years_label(years)} after it, and the latest data is {ui.date_ar(dmax)}. Choose an earlier date (up to {last_ok}) or a shorter period. We do not shorten the period or predict the missing part.",
                     f"البيانات لا تكفي: الشراء في {ui.date_ar(r['start_date'])} يحتاج {years_label(years)} بعده، وآخر بيانات متاحة {ui.date_ar(dmax)}. اختاري تاريخًا أقدم (حتى {last_ok}) أو مدة أقصر. لا نختصر المدة تلقائيًا ولا نتوقع الفترة المفقودة."))
    else:
        st.warning(ui.tr(r["reason"]))
else:
    if pd.Timestamp(buy) != r["start_date"]:
        st.caption(L(f"The chosen date is not a trading day, so we used the next session: {ui.date_ar(r['start_date'])}.",
                     f"التاريخ المختار ليس يوم تداول، فاستخدمنا أول جلسة بعده: {ui.date_ar(r['start_date'])}."))
    tone = "up" if r["gain"] >= 0 else "down"
    gain_word = L("Gain", "مكسب") if r["gain"] >= 0 else L("Loss", "خسارة")
    ui.cards([
        {"label": L("Buy", "الشراء"), "value": ui.sar_g(r["start_price"] * TO_SAR_G), "desc": ui.date_ar(r["start_date"])},
        {"label": L("End of holding", "نهاية الاحتفاظ"), "value": ui.sar_g(r["end_price"] * TO_SAR_G),
         "desc": f"{ui.date_ar(r['end_date'])} · {L('after', 'بعد')} {ui.num(r['sessions'])} {L('sessions', 'جلسة')}"},
        {"label": L("Change", "التغير"), "value": ui.pct(r["change_pct"]), "tone": tone,
         "desc": f"{gain_word} {ui.sar(abs(r['gain']))} · {L('final value', 'القيمة النهائية')} {ui.sar(r['final_value'])}"},
        {"label": L("Largest fall during the test", "أكبر انخفاض أثناء التجربة"), "value": ui.pct(r["max_dd"]), "tone": "down" if r["max_dd"] < 0 else "",
         "desc": L(f"From peaks inside the test path, on {ui.date_ar(r['max_dd_date'])}.", f"من القمم داخل مسار التجربة، في {ui.date_ar(r['max_dd_date'])}.")
         if r["max_dd"] < 0 else L("Never below an earlier peak.", "لم ينزل تحت قمة سابقة.")},
    ])
    st.plotly_chart(charts.hold_value(r["path"], amount), theme=None, config=CFG, key="hold_value")
    extra = (L(f" On the way, the value fell as much as {ui.pct(r['max_dd'])} below an earlier high.",
               f" لكن في الطريق نزلت القيمة حتى {ui.pct(r['max_dd'])} تحت أعلى مستوى سابق.") if r["max_dd"] < -0.5 else "")
    ui.insight(L(f"<b>Result:</b> {ui.sar(amount)} on {ui.date_ar(r['start_date'])} became about {ui.sar(r['final_value'])} on {ui.date_ar(r['end_date'])} ({ui.pct(r['change_pct'])}).",
                 f"<b>النتيجة:</b> مبلغ {ui.sar(amount)} في {ui.date_ar(r['start_date'])} أصبح تقريبًا {ui.sar(r['final_value'])} في {ui.date_ar(r['end_date'])} ({ui.pct(r['change_pct'])}).") + extra)
    ui.note(L("Values in SAR use the notebook conversion (3.75 SAR per USD, 31.1035 g per ounce), so the % change is the same as in USD.",
              "القيم بالريال تستخدم تحويل النوتبوك (3.75 ريال للدولار، و31.1035 جرام للأونصة)، فنسبة التغير نفسها كما بالدولار."))

st.divider()
st.subheader(L("General comparison of holding periods", "مقارنة عامة لمدد الاحتفاظ"))
ui.note(L("For each period we tried every possible buy date in the full data, then sold after the period (252 sessions per year, as in the notebook).",
          "لكل مدة جربنا كل تاريخ شراء ممكن في كامل البيانات، ثم البيع بعد المدة (252 جلسة لكل سنة تقريبًا، مثل النوتبوك)."))
t = A.holding_table(df)
tbl = pd.DataFrame({
    L("Period", "المدة"): [years_label(y) for y in t["years"]],
    L("Buy dates tested", "عدد تواريخ الشراء"): t["tested"],
    L("Positive cases (%)", "حالات بعائد موجب (%)"): t["positive_pct"].round(1),
    L("Median (%)", "العائد الوسيط (%)"): t["median"].round(1),
    L("Worst (%)", "أسوأ نتيجة (%)"): t["worst"].round(1),
    L("Best (%)", "أفضل نتيجة (%)"): t["best"].round(1),
    L("Last buy tested", "آخر شراء مختبر"): [ui.date_ar(x) for x in t["last_buy"]],
})
st.dataframe(tbl, hide_index=True, width="stretch")

h = st.segmented_control(L("Show the result by buy date for", "عرض النتيجة حسب تاريخ الشراء لمدة"), [1, 3, 5],
                         key=ui.lkey("h_chart", 3), on_change=ui.sync, args=("h_chart",),
                         format_func=lambda y: years_label(y).split(" (")[0])
if h:
    st.plotly_chart(charts.hold_by_buy_date(df, h), theme=None, config=CFG, key="hold_bydate")

b = t.set_index("years")
ui.insight(L(
    f"<b>Insight:</b> in this data, the longer the holding period, the fewer cases ended with a loss: {ui.pct(b.loc[1, 'positive_pct'], sign=False)} of cases were positive for 1 year, {ui.pct(b.loc[3, 'positive_pct'], sign=False)} for 3 years and {ui.pct(b.loc[5, 'positive_pct'], sign=False)} for 5 years. Time does not guarantee a profit; 2015 to 2026 was a strong period for gold.",
    f"<b>الاستنتاج:</b> في هذه البيانات، كلما طالت مدة الاحتفاظ قلت الحالات التي انتهت بخسارة: {ui.pct(b.loc[1, 'positive_pct'], sign=False)} من الحالات بعائد موجب لسنة، و{ui.pct(b.loc[3, 'positive_pct'], sign=False)} لثلاث سنوات، و{ui.pct(b.loc[5, 'positive_pct'], sign=False)} لخمس سنوات. هذا لا يعني أن الوقت يضمن الربح؛ فترة 2015 إلى 2026 كانت قوية للذهب."))
with st.expander(L("How to read these numbers", "كيف نقرأ هذه الأرقام؟")):
    st.markdown(L(
        "- These are **historical price changes before costs** (making charge, shop margin, VAT, buy/sell spread).\n"
        "- **Cases overlap in time**: buying on two days in a row shares most of the period, so they are not independent tests.\n"
        "- **The share of profitable cases is not the size of the profit**, nor a guaranteed probability for the future.\n"
        "- The price is a futures price; this is **not a full simulation** of futures trading or of buying and selling jewelry.\n"
        "- Periods are approximate: 252 trading sessions per year.",
        "- هذه **تغيرات تاريخية في السعر قبل التكاليف** (المصنعية، هامش المحل، الضريبة، فرق البيع والشراء).\n"
        "- **الحالات متداخلة زمنيًا**: الشراء في يومين متتاليين يشترك في معظم الفترة، فهي ليست تجارب مستقلة.\n"
        "- **نسبة الحالات المربحة ليست مقدار الربح** ولا احتمالًا مضمونًا للمستقبل.\n"
        "- السعر سعر عقود آجلة؛ هذه **ليست محاكاة كاملة** لتداول العقود أو لشراء المجوهرات وبيعها.\n"
        "- المدد تقريبية: 252 جلسة تداول لكل سنة."))
