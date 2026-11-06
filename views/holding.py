"""Page 2: Try holding / جرّب الاحتفاظ -- what would gold bought years ago be worth?"""
import pandas as pd
import streamlit as st

from utils import analysis as A
from utils import charts, settings, ui
from utils.i18n import L

df = ui.get_data()
dmin, dmax = df["Date"].min().date(), df["Date"].max().date()
CFG = {"displayModeBar": False}
NOW = "now"   # option: until today / latest available price

st.markdown(
    f"""<div class="ey-hero"><div class="ey-kicker">{L('EYAR | Try holding', 'عيار | جرّب الاحتفاظ')}</div>
    <h1>{L('If you had bought gold years ago, what would it be worth?', 'لو اشتريت الذهب قبل سنوات، كم أصبحت قيمته؟')}</h1>
    <div class="ey-lead">{L('Choose the buy date, the amount and the karat to estimate how the value of the gold changed over the holding period.',
                            'اختر تاريخ الشراء والمبلغ والعيار لتقدير كيف تغيرت قيمة الذهب خلال مدة الاحتفاظ.')}</div></div>""",
    unsafe_allow_html=True,
)

with st.container(border=True):
    c1, c2 = st.columns(2)
    buy = c1.date_input(L("Buy date", "تاريخ الشراء"), min_value=dmin, max_value=dmax, format="YYYY-MM-DD",
                        key=ui.lkey("h_buy", pd.Timestamp("2020-01-02").date()), on_change=ui.sync, args=("h_buy",))
    amount = c2.number_input(L("Value of the gold when bought (SAR), without making charge and VAT",
                               "قيمة الذهب وقت الشراء (ريال)، دون المصنعية والضريبة"),
                             min_value=1.0, max_value=100_000_000.0, step=500.0,
                             key=ui.lkey("h_amount", 5000.0), on_change=ui.sync, args=("h_amount",))
    c3, c4 = st.columns(2)
    karat = c3.radio(L("Karat", "العيار"), settings.KARATS, horizontal=True, format_func=lambda k: L(f"{k}K", f"عيار {k}"),
                     key=ui.lkey("h_karat", 21), on_change=ui.sync, args=("h_karat",))

    # Only the periods that are possible from this buy date, plus "until today"
    years_ok = A.available_years(df, buy)
    options = years_ok + [NOW]
    prev = ui.val("h_period")
    if prev not in options:          # first visit, or the buy date changed: move to a valid period
        if prev is None:
            new = years_ok[-1] if years_ok else NOW
        else:
            valid = [y for y in years_ok if isinstance(prev, int) and y <= prev]
            new = valid[-1] if valid else NOW
        st.session_state["v_h_period"] = new
        ui.forget("h_period")

    def period_label(p):
        if p == NOW:
            return L("Until today / latest available price", "حتى اليوم / آخر تسعيرة متاحة")
        return L(f"{p} year" + ("s" if p > 1 else ""), {1: "سنة واحدة", 2: "سنتان"}.get(p, f"{p} سنوات"))

    period = c4.selectbox(L("Holding period", "مدة الاحتفاظ"), options, format_func=period_label,
                          key=ui.lkey("h_period", NOW), on_change=ui.sync, args=("h_period",))
    if not years_ok:
        c4.caption(L("No full year is available after this buy date in the study data, so only “until today” can be chosen.",
                     "لا توجد سنة كاملة متاحة بعد هذا التاريخ في بيانات الدراسة، لذلك يمكن اختيار «حتى اليوم» فقط."))

if amount is None or amount <= 0:
    st.warning(L("Enter an amount greater than zero.", "أدخل مبلغًا أكبر من صفر."))
    st.stop()


def result_sentence(final, gain):
    if gain >= 0:
        return L(f"Gold worth {ui.sar(amount)} became about <b>{ui.sar(final)}</b>, an approximate increase of <b>{ui.sar(gain)}</b>.",
                 f"قيمة ذهب بمبلغ {ui.sar(amount)} أصبحت نحو <b>{ui.sar(final)}</b>، بزيادة تقريبية قدرها <b>{ui.sar(gain)}</b>.")
    return L(f"Gold worth {ui.sar(amount)} became about <b>{ui.sar(final)}</b>, an approximate decrease of <b>{ui.sar(-gain)}</b>.",
             f"قيمة ذهب بمبلغ {ui.sar(amount)} أصبحت نحو <b>{ui.sar(final)}</b>، بانخفاض تقريبي قدره <b>{ui.sar(-gain)}</b>.")


if period == NOW:
    q = ui.get_quote()
    if not q.ok:
        st.error(L("We could not get a current reference price, so we cannot show today's value. Try again later, or choose a number of years.",
                   "تعذر الحصول على سعر مرجعي حالي، لذلك لا نستطيع عرض القيمة اليوم. حاول لاحقًا أو اختر عددًا من السنوات.")
                 + " " + ui.tr(q.error))
        st.stop()
    r = A.hold_value_now(df, buy, amount, karat, q.usd_oz)
    if not r["ok"]:
        st.warning(L("No trading session on or after this date in the data.", "لا توجد جلسة تداول في هذا التاريخ أو بعده داخل البيانات."))
        st.stop()
    end_label = ui.quote_status_line(q)
else:
    r = A.hold_value(df, buy, period, amount, karat)
    if not r["ok"]:
        st.warning(L("This period is not available from the chosen date.", "هذه المدة غير متاحة من التاريخ المختار."))
        st.stop()
    end_label = (ui.date_ar(r["end_date"]) + (L(" (last trading session before the anniversary date)", " (آخر جلسة تداول قبل تاريخ نهاية المدة)")
                                              if r["end_date"] != r["target"] else ""))

if pd.Timestamp(buy) != r["start_date"]:
    st.caption(L(f"The chosen date is not a trading day, so we used the next session: {ui.date_ar(r['start_date'])}.",
                 f"التاريخ المختار ليس يوم تداول، فاستخدمنا أول جلسة بعده: {ui.date_ar(r['start_date'])}."))

ui.cards([
    {"label": L(f"Gram price when bought ({karat}K)", f"سعر الجرام عند الشراء (عيار {karat})"), "value": ui.sar(r["gram_start"], 1),
     "desc": ui.date_ar(r["start_date"])},
    {"label": L(f"Gram price at the end ({karat}K)", f"سعر الجرام عند نهاية الاحتفاظ (عيار {karat})"), "value": ui.sar(r["gram_end"], 1),
     "desc": end_label},
], cols=2)
ui.insight(result_sentence(r["final"], r["gain"]))
ui.note(L("The value is an estimate for the gold only, before any shop deduction. It does not include getting back the making charge or the purchase VAT.",
          "القيمة تقديرية للذهب فقط، قبل خصم المحل، ولا تشمل استرداد المصنعية أو ضريبة الشراء."))
if period == NOW:
    ui.note(L("The buy price comes from the historical study data (gold futures) and the current price from a spot price service. "
              "These are two different references, so treat the result as an approximate comparison, not an exact investment return.",
              "سعر الشراء من بيانات الدراسة التاريخية (عقود آجلة)، والسعر الحالي من خدمة سعر فوري. "
              "هما مرجعان مختلفان، فالنتيجة مقارنة تقديرية وليست عائد استثمار دقيقًا."))
else:
    st.plotly_chart(charts.hold_value(r["path"], amount), theme=None, config=CFG, key="hold_value")

st.markdown(
    f"<div class='ey-note' style='margin-top:6px'>{L('In the study data, losses were less common over longer holding periods, but the result depends on the buy and sell dates, and a longer period does not guarantee a profit.', 'في بيانات الدراسة، كانت الخسائر أقل شيوعًا مع فترات الاحتفاظ الأطول، لكن النتيجة تعتمد على تاريخ الشراء والبيع ولا يضمن طول المدة ربحًا.')}</div>",
    unsafe_allow_html=True,
)
