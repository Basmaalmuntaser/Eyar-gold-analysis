"""Page 3: Price your piece / احسب قطعتك -- simple estimate with the current reference gold price."""
import streamlit as st

from utils import calc, settings, ui
from utils.i18n import L

PIECES = {"bangles": L("Bangles", "بناجر"), "other": L("Other pieces", "مشغولات أخرى")}
BAR_LABEL = L("Qualified investment bar: 99% purity or more and tradable on the international bullion market",
              "سبيكة استثمارية مؤهلة: نقاء 99% فأكثر وقابلة للتداول في سوق السبائك العالمية")

st.markdown(
    f"""<div class="ey-hero"><div class="ey-kicker">{L('EYAR | Price your piece', 'عيار | احسب قطعتك')}</div>
    <h1>{L('How much is your piece, roughly?', 'كم سعر قطعتك تقريبًا؟')}</h1>
    <div class="ey-lead">{L('Choose the karat, the weight and the piece type. We estimate a price range from the current reference gold price.',
                            'اختر العيار والوزن ونوع القطعة، ونقدّر لك نطاق السعر من سعر الذهب المرجعي الحالي.')}</div></div>""",
    unsafe_allow_html=True,
)


def clear_bar(prefix: str):
    """When the karat is no longer 24, a hidden 'investment bar' choice must not stay switched on."""
    def _cb():
        ui.sync(f"{prefix}_karat")
        if ui.val(f"{prefix}_karat") != 24:
            st.session_state[f"v_{prefix}_bar"] = False
            ui.forget(f"{prefix}_bar")
    return _cb


def piece_inputs(prefix: str, container, small: bool = False):
    """Karat, piece type, and (only for 24K) the investment bar question. Returns (karat, category)."""
    karat = container.radio(L("Karat", "العيار"), settings.KARATS, horizontal=True, format_func=lambda k: L(f"{k}K", f"عيار {k}"),
                            key=ui.lkey(f"{prefix}_karat", 21), on_change=clear_bar(prefix))
    bar = False
    if karat == 24:
        bar = container.toggle(BAR_LABEL, key=ui.lkey(f"{prefix}_bar", False), on_change=ui.sync, args=(f"{prefix}_bar",))
    if not bar:
        widget = container.pills if small else container.radio
        kwargs = {"selection_mode": "single"} if small else {"horizontal": True}
        piece = widget(L("Piece type", "نوع القطعة"), list(PIECES), format_func=PIECES.get,
                       key=ui.lkey(f"{prefix}_piece", "bangles"), on_change=ui.sync, args=(f"{prefix}_piece",), **kwargs)
        piece = piece or "bangles"
    else:
        piece = "bar"
    return karat, calc.category_for(karat, piece, bar)


# ---------------------------------------------------------------------------
# Current reference price
# ---------------------------------------------------------------------------
q = ui.get_quote()
with st.container(horizontal=True, vertical_alignment="center"):
    if q.ok:
        st.markdown(f"<div class='ey-meta'>{ui.quote_status_line(q)}</div>", unsafe_allow_html=True, width="content")
    if st.button(L("Refresh price", "تحديث السعر"), icon=":material/refresh:", type="tertiary"):
        ui.refresh_quote()
        st.rerun()

if not q.ok:
    st.error(L("We could not get a current, reliable gold price right now, so we cannot estimate a purchase price. "
               "Please try “Refresh price” in a few minutes.",
               "تعذر الحصول على سعر ذهب حالي وموثوق الآن، لذلك لا نستطيع تقدير سعر الشراء. "
               "جرّب «تحديث السعر» بعد دقائق.") + " " + ui.tr(q.error))
    last = st.session_state.get("last_good_quote")
    if last is not None:
        t = ui.live_price.riyadh(last.quote_time)
        st.caption(L(f"For information only (not valid for a purchase estimate): the last price we received was {ui.usd(last.usd_oz)} per ounce at {ui.date_ar(t)} {t:%H:%M} Riyadh time.",
                     f"للتوضيح فقط (غير صالح لتقدير الشراء): آخر سعر استلمناه كان {ui.usd(last.usd_oz)} للأونصة في {ui.date_ar(t)} {t:%H:%M} بتوقيت السعودية."))
    st.stop()

# ---------------------------------------------------------------------------
# Inputs and result
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1.2], gap="large")
with left:
    with st.container(border=True):
        karat, category = piece_inputs("c", st)
        weight = st.number_input(L("Gold weight (grams)", "وزن الذهب (جرام)"), min_value=0.0, max_value=calc.MAX_WEIGHT, step=0.5,
                                 placeholder=L("e.g. 10", "مثال: 10"), key=ui.lkey("c_weight", None), on_change=ui.sync, args=("c_weight",))
        st.caption(L("Enter the net gold weight, without stones.", "أدخل وزن الذهب الصافي دون الفصوص أو الأحجار."))

gram = calc.gram_price_from_ounce(q.usd_oz, settings.DEFAULT_USD_TO_SAR, karat)
with right:
    err = calc.validate_weight(weight)
    if not calc.validate_gram_price(gram):
        st.error(L("The reference price is not valid.", "السعر المرجعي غير صالح."))
    elif err:
        st.markdown(f'<div class="ey-invoice"><div class="head">{L("Estimated price", "السعر التقديري")}</div>'
                    f'<div class="sub" style="margin-top:8px">{ui.tr(err)}</div></div>', unsafe_allow_html=True)
    else:
        e = calc.estimate(gram, weight, category)
        vat_line = (L("Includes 15% VAT", "يشمل ضريبة القيمة المضافة 15%") if e["vat"] > 0 else
                    L("Zero rate applied, assuming the bar meets the investment bar conditions",
                      "تطبق نسبة الصفر على افتراض استيفاء شروط السبيكة الاستثمارية"))
        kind = L("Investment bar", "سبيكة استثمارية") if category == "bar" else PIECES[category]
        st.markdown(
            f"""<div class="ey-invoice">
            <div class="head">{L('Estimated price', 'السعر التقديري')}</div>
            <div class="big">{L(f"{ui.num(e['low'])} to {ui.num(e['high'])} SAR", f"من {ui.num(e['low'])} إلى {ui.num(e['high'])} ريال")}</div>
            <div class="sub">{vat_line} · {L(f'{karat}K', f'عيار {karat}')} · {kind} · {ui.num(weight, 2)} {L('g', 'جرام')}</div>
            <table>
              <tr><td>{L(f'Reference gram price ({karat}K)', f'السعر المرجعي للجرام (عيار {karat})')}</td><td class='v'>{ui.sar(gram, 1)}</td></tr>
              <tr><td>{L('Making charge and shop margin (estimate)', 'المصنعية وهامش المحل (تقديري)')}</td>
                  <td class='v'>{L(f"{e['addon_low']:.1f} to {e['addon_high']:.1f} SAR/g", f"{e['addon_low']:.1f} إلى {e['addon_high']:.1f} ريال/جرام")}</td></tr>
            </table>
            <div class="foot">{ui.quote_status_line(q)}
            <br>{L('An estimated range, not a binding price.', 'نطاق تقديري، وليس سعرًا إلزاميًا.')}</div></div>""",
            unsafe_allow_html=True,
        )
        if category == "bar":
            ui.note(L("The add-on for bars is an estimate and goes down per gram for heavier bars. It can differ by refinery, brand and seller.",
                      "إضافة السبائك تقديرية وتقل لكل جرام مع زيادة الوزن، وقد تختلف حسب المصفاة أو العلامة التجارية والبائع."))
        else:
            ui.note(L("The range is an estimate; add-ons can be higher depending on the design, the brand and the shop.",
                      "النطاق تقديري، وقد تزيد الإضافات حسب التصميم والعلامة التجارية والمحل.") + "<br>" +
                    L("For heavier pieces, you may be able to negotiate an add-on closer to the lower end of the range.",
                      "مع زيادة وزن القطعة، قد تتمكن من التفاوض على إضافة أقرب للحد الأدنى من النطاق."))
        with st.expander(L("How did we calculate it?", "كيف حسبناها؟")):
            st.markdown(L("We added the making charge and shop margin to the gram price, multiplied by the weight, then added VAT if it applies.",
                          "أضفنا المصنعية وهامش المحل إلى سعر الجرام، وضربنا الناتج في الوزن، ثم أضفنا الضريبة إن كانت مطبقة."))
        t = ui.live_price.riyadh(q.quote_time)
        summary = "\n".join([
            L("EYAR: price estimate", "عيار | EYAR: تقدير السعر"), "",
            f"{L('Karat', 'العيار')}: {karat}", f"{L('Piece type', 'نوع القطعة')}: {kind}",
            f"{L('Gold weight', 'وزن الذهب')}: {weight:.2f} {L('g', 'جرام')}",
            f"{L('Reference gram price', 'السعر المرجعي للجرام')}: {gram:,.2f} SAR",
            f"{L('Price source', 'مصدر السعر')}: {q.provider} (XAU/USD), {L('price time', 'وقت التسعيرة')} {t:%Y-%m-%d %H:%M} {L('Riyadh time', 'بتوقيت السعودية')}",
            f"{L('Add-on (making charge + margin)', 'الإضافة (المصنعية + الهامش)')}: {e['addon_low']:.1f} – {e['addon_high']:.1f} SAR/g",
            f"{L('VAT', 'الضريبة')}: {e['vat'] * 100:.0f}%",
            f"{L('Estimated price', 'السعر التقديري')}: {e['low']:,.0f} – {e['high']:,.0f} SAR", "",
            L("An estimated range, not a binding price.", "نطاق تقديري، وليس سعرًا إلزاميًا."),
        ])
        st.download_button(L("Download the summary", "تنزيل الملخص"), summary.encode("utf-8-sig"), file_name="eyar_estimate.txt",
                           mime="text/plain", icon=":material/download:")

st.warning(L("Do not buy without a clear invoice showing the karat, the weight, the price and VAT if it is due, even if the offer is lower. "
             "The invoice matters to prove the purchase and to claim your rights. Check the seller and the karat hallmark.",
             "لا تشترِ دون فاتورة واضحة تبين العيار والوزن والسعر والضريبة إن كانت مستحقة، حتى لو كان العرض أقل. "
             "الفاتورة مهمة لإثبات عملية الشراء والمطالبة بحقك. تحقق من البائع ودمغة العيار."), icon=":material/receipt_long:")

# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------
st.divider()
st.subheader(L("How much gold can my budget buy?", "ميزانيتي كم تجيب؟"))
with st.container(border=True):
    b1, b2 = st.columns([1, 2])
    budget = b1.number_input(L("Budget (SAR)", "الميزانية (ريال)"), min_value=0.0, step=500.0, placeholder=L("e.g. 5000", "مثال: 5000"),
                             key=ui.lkey("b_amount", None), on_change=ui.sync, args=("b_amount",))
    with b2:
        bkarat, bcat = piece_inputs("b", st, small=True)
    if budget:
        bgram = calc.gram_price_from_ounce(q.usd_oz, settings.DEFAULT_USD_TO_SAR, bkarat)
        res = calc.budget_weight(budget, bgram, bcat)
        if not res["ok"]:
            st.warning(ui.tr(res["error"]))
        else:
            lo_w, hi_w = ui.num(res["low"], 2), ui.num(res["high"], 2)
            st.markdown(
                f"<div class='ey-invoice'><div class='big'>{L(f'Your budget buys about {lo_w} to {hi_w} g', f'ميزانيتك تكفي تقريبًا من {lo_w} إلى {hi_w} جرام')}</div>"
                f"<div class='sub'>{L(f'{bkarat}K', f'عيار {bkarat}')} · "
                f"{L('Investment bar', 'سبيكة استثمارية') if bcat == 'bar' else PIECES[bcat]}</div>"
                f"<div class='foot'>{L('The weight estimate already includes the add-ons and VAT (when it applies), and is rounded down so it stays within your budget.', 'تقدير الوزن يشمل الإضافات والضريبة (إن كانت مطبقة)، ومقرّب للأسفل حتى لا يتجاوز ميزانيتك.')}</div></div>",
                unsafe_allow_html=True)
    else:
        st.caption(L("Enter a budget to see an approximate weight range.", "اكتب الميزانية لنعرض نطاقًا تقريبيًا للوزن."))
