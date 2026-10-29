"""Page 3: Price your piece / احسب قطعتك (estimate using the shop survey of 29 Oct 2026)."""
import pandas as pd
import streamlit as st

from utils import calc, settings, ui
from utils.i18n import L, is_ar

df = ui.get_data()
last = df.iloc[-1]
survey, survey_msgs = ui.get_survey()
SURVEY_DATE = ", ".join(sorted({x for x in survey.get("collected_on", pd.Series(dtype=str)) if x})) or "—"
N_SHOPS = survey["shop_en"].nunique() if not survey.empty else 0

st.markdown(
    f"""<div class="ey-hero"><div class="ey-kicker">{L('EYAR | Price your piece', 'عيار | احسب قطعتك')}</div>
    <h1>{L('How much is your piece, roughly?', 'كم سعر قطعتك تقريبًا؟')}</h1>
    <div class="ey-lead">{L('Choose the karat, enter the weight and the piece type. We estimate a price range with the gold value, making charge and VAT, based on a survey of shops.',
                            'اختاري العيار واكتبي الوزن ونوع القطعة، ونحسب لك نطاقًا تقديريًا يشمل قيمة الذهب والمصنعية والضريبة بناءً على عينة من المحلات.')}</div>
    <div class="ey-meta">{L('Reference price: last close in the project data', 'السعر المرجعي: آخر إغلاق في بيانات المشروع')} ({ui.date_ar(last['Date'])}) · {L('shop survey', 'مسح المحلات')}: {ui.date_ar(SURVEY_DATE) if SURVEY_DATE != '—' else '—'}</div>
    </div>""",
    unsafe_allow_html=True,
)

VAT_LABELS = {
    "jewelry": L("Jewelry and gold pieces (15%)", "مشغولات ومجوهرات (15%)"),
    "investment": L("Investment gold: bar or coin, 99% purity or more (0%)", "ذهب استثماري: سبيكة أو عملة نقاوتها 99% فأكثر (0%)"),
    "unknown": L("Not sure", "غير متأكدة"),
}
CATEGORY_LABELS = {"bangles": L("Bangles", "بناجر"), "other": L("Other pieces", "مشغولات أخرى")}
cities = sorted(set(survey["city_en"])) if not survey.empty else []
city_name = {r.city_en: L(r.city_en, r.city_ar) for r in survey.itertuples()} if not survey.empty else {}
shops = list(dict.fromkeys(survey["shop_en"])) if not survey.empty else []
shop_name = {r.shop_en: L(r.shop_en, r.shop_ar) for r in survey.itertuples()} if not survey.empty else {}

# defaults (kept in session so a language switch keeps the inputs)
for k, v in {"c_weight": None, "c_stones": False, "c_stone_w": None, "c_stone_v": None, "c_ounce": None, "c_gram": None,
             "c_fx": settings.DEFAULT_USD_TO_SAR}.items():
    st.session_state.setdefault(k, v)
CHOICES = {"c_karat": 21, "c_cat": "bangles", "c_city": "all", "c_shop": "sample", "c_incl": "incl", "c_vat": "jewelry"}

left, right = st.columns([1, 1.25], gap="large")

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
with left:
    with st.form("calc_form", border=True):
        st.radio(L("Karat", "العيار"), settings.KARATS, horizontal=True, key=ui.lkey("c_karat", CHOICES["c_karat"]),
                 format_func=lambda k: L(f"{k}K", f"عيار {k}"))
        st.number_input(L("Piece weight (grams)", "وزن القطعة (جرام)"), min_value=0.0, max_value=calc.MAX_WEIGHT,
                        step=0.5, placeholder=L("e.g. 10", "مثال: 10"), key="c_weight")
        st.radio(L("Piece type", "نوع القطعة"), list(CATEGORY_LABELS), format_func=CATEGORY_LABELS.get, horizontal=True, key=ui.lkey("c_cat", CHOICES["c_cat"]))

        with st.expander(L("Optional details", "تفاصيل اختيارية")):
            st.selectbox(L("City", "المدينة"), ["all"] + cities, key=ui.lkey("c_city", CHOICES["c_city"]),
                         format_func=lambda c: L("All cities", "كل المدن") if c == "all" else city_name.get(c, c))
            st.selectbox(L("Shop", "المحل"), ["sample"] + shops, key=ui.lkey("c_shop", CHOICES["c_shop"]),
                         format_func=lambda s: L("Whole sample (range of shops)", "نطاق العينة (كل المحلات)") if s == "sample" else shop_name.get(s, s))
            st.markdown(f"**{L('Stones', 'الفصوص والأحجار')}**")
            st.checkbox(L("The piece has stones", "القطعة فيها فصوص أو أحجار"), key="c_stones")
            st.radio(L("The weight I entered:", "الوزن الذي كتبته:"), ["incl", "net"], horizontal=True, key=ui.lkey("c_incl", CHOICES["c_incl"]),
                     format_func={"incl": L("includes the stones", "يشمل الأحجار"), "net": L("is net gold only", "وزن الذهب الصافي فقط")}.get)
            st.number_input(L("Stone weight (g), if known", "وزن الأحجار (جرام) إن كان معروفًا"), min_value=0.0, step=0.1, key="c_stone_w")
            st.number_input(L("Stone value (SAR), if known", "قيمة الأحجار (ريال) إن كانت معروفة"), min_value=0.0, step=50.0, key="c_stone_v")
            st.caption(L("A stone carat is a weight unit (1 carat = 0.2 g) and is different from the gold karat (purity). Multiply carats by 0.2 to get grams.",
                         "قيراط الأحجار وحدة وزن (القيراط = 0.2 جرام)، ويختلف عن «عيار» نقاء الذهب. اضربي القيراط في 0.2 لتحويله إلى جرام."))
            st.markdown(f"**{L('Price and VAT', 'السعر والضريبة')}**")
            st.number_input(L("Reference ounce price in USD (empty = last close)", "سعر أونصة مرجعي بالدولار (فارغ = آخر إغلاق)"),
                            min_value=0.0, step=10.0, key="c_ounce")
            st.number_input(L("Or a gram price for the chosen karat, SAR, before VAT", "أو سعر جرام للعيار المختار بالريال قبل الضريبة"),
                            min_value=0.0, step=1.0, key="c_gram",
                            help=L("If entered, it is used as is; the karat factor is not applied again.",
                                   "إذا كتبتِه نستخدمه مباشرة ولا نطبق معامل العيار عليه مرة ثانية."))
            st.number_input(L("USD to SAR rate", "سعر صرف الدولار بالريال"), min_value=0.1, step=0.01, key="c_fx",
                            help=L("The riyal is officially pegged at 3.75 per USD.", "الريال مربوط رسميًا بالدولار عند 3.75."))
            st.radio(L("VAT case", "الحالة الضريبية"), list(VAT_LABELS), format_func=VAT_LABELS.get, key=ui.lkey("c_vat", CHOICES["c_vat"]))

        submitted = st.form_submit_button(L("Calculate the estimated price", "احسب السعر التقديري"), type="primary",
                                          width="stretch", icon=":material/calculate:")
    if submitted:
        for name in CHOICES:
            ui.sync(name)
        st.session_state["calc_done"] = True
        st.session_state["v_bud_karat"] = ui.val("c_karat")   # the budget section follows the chosen karat
        ui.forget("bud_karat")


def inputs():
    s, v = st.session_state, ui.val
    return dict(karat=v("c_karat"), weight=s["c_weight"], cat=v("c_cat"), city=None if v("c_city") == "all" else v("c_city"),
                shop=None if v("c_shop") == "sample" else v("c_shop"), has_stones=s["c_stones"],
                includes_stones=v("c_incl") == "incl", stone_w=s["c_stone_w"], stone_v=s["c_stone_v"],
                ounce_override=s["c_ounce"], gram_override=s["c_gram"], fx=s["c_fx"], vat_case=v("c_vat"))


def price_source(inp):
    """Gram price (SAR, before VAT) for the chosen karat, and where it came from."""
    k = inp["karat"]
    if inp["gram_override"]:
        return inp["gram_override"], L(f"{k}K gram price you entered (before VAT)", f"سعر جرام عيار {k} أدخلتِه يدويًا (قبل الضريبة)"), None
    if inp["ounce_override"]:
        return (calc.gram_price_from_ounce(inp["ounce_override"], inp["fx"], k),
                L(f"ounce price you entered: {ui.usd(inp['ounce_override'])}", f"سعر أونصة أدخلتِه يدويًا: {ui.usd(inp['ounce_override'])}"), None)
    g = calc.gram_price_from_ounce(float(last["Close"]), inp["fx"], k)
    g24 = calc.gram_price_from_ounce(float(last["Close"]), inp["fx"], 24)
    return g, L(f"estimate based on the gold futures price (GC=F), last close in the project data, {ui.sar_g(g24, 24, 1)}",
                f"تقدير مبني على سعر عقود الذهب الآجلة (GC=F)، آخر إغلاق في بيانات المشروع، {ui.sar_g(g24, 24, 1)}"), last["Date"]


def shop_rows(inp, karat=None):
    rows, general = calc.survey_rows(survey, karat or inp["karat"], inp["cat"], inp["city"], inp["shop"])
    return rows, general


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
est = None
with right:
    if not st.session_state.get("calc_done"):
        st.markdown(f'<div class="ey-invoice"><div class="head">{L("Estimated price of the piece", "السعر التقديري للقطعة")}</div>'
                    f'<div class="sub" style="margin-top:8px">{L("Choose the karat, enter the weight, then press “Calculate the estimated price”.", "اختاري العيار واكتبي الوزن ثم اضغطي «احسب السعر التقديري».")}</div></div>',
                    unsafe_allow_html=True)
    else:
        inp = inputs()
        gw = calc.gold_weight(inp["weight"], inp["has_stones"], inp["includes_stones"], inp["stone_w"])
        err = ui.tr(gw["error"]) if not gw["ok"] else None
        if not err and inp["vat_case"] == "investment" and inp["karat"] != 24:
            err = L("Investment gold (0% VAT) is for bars and coins of 99% purity or more, i.e. 24K. Change the karat or the VAT case.",
                    "الذهب الاستثماري (نسبة صفر) يخص السبائك والعملات بنقاء 99% فأكثر، أي عيار 24. غيّري العيار أو الحالة الضريبية.")
        if err:
            st.error(err)
        else:
            rows, general = shop_rows(inp)
            gram, src, src_date = price_source(inp)
            stones_value = inp["stone_v"] if (inp["has_stones"] and inp["stone_v"]) else None
            est = calc.estimate(inp["karat"], gw["gold_w"], gram, rows if not rows.empty else None, inp["vat_case"], stones_value)
            st.session_state["calc_est"] = est
            ex = est.extras

            if est.has_range and est.vat is not None:
                big = L(f"{ui.num(est.total_low)} to {ui.num(est.total_high)} SAR", f"من {ui.num(est.total_low)} إلى {ui.num(est.total_high)} ريال")
                sub = L(f"including VAT ({ui.pct(est.vat * 100, 0, sign=False)})", f"شامل الضريبة ({ui.pct(est.vat * 100, 0, sign=False)})")
            elif est.has_range:
                big = L(f"{ui.num(est.subtotal_low)} to {ui.num(est.subtotal_high)} SAR", f"من {ui.num(est.subtotal_low)} إلى {ui.num(est.subtotal_high)} ريال")
                sub = L("before VAT, because the VAT case is not set", "قبل الضريبة، لأن الحالة الضريبية غير محددة")
            elif est.vat is not None:
                big = ui.sar(est.metal_value * (1 + est.vat))
                sub = L("gold value only, with VAT (no shop data for this choice)", "قيمة الذهب فقط مع الضريبة (لا توجد بيانات محلات لهذا الاختيار)")
            else:
                big = ui.sar(est.metal_value)
                sub = L("gold value only, before VAT", "قيمة الذهب فقط قبل الضريبة")

            def rng(a, b):
                return ui.sar(a) if abs(a - b) < 0.5 else L(f"{ui.num(a)} to {ui.num(b)} SAR", f"{ui.num(a)} إلى {ui.num(b)} ريال")

            items = [
                (L("Gold weight used", "وزن الذهب المحسوب"), f"{ui.num(est.gold_w, 2)} {L('g', 'جرام')}"
                 + (f"<br><span class='ey-note'>{L('after removing', 'بعد خصم')} {ui.num(gw['deducted'], 2)} {L('g of stones', 'جرام أحجار')}</span>" if gw["deducted"] else "")),
                (L(f"Gram price, {inp['karat']}K", f"سعر جرام عيار {inp['karat']}"), ui.sar(gram, 1)),
                (L("Gold value", "قيمة الذهب"), ui.sar(est.metal_value)),
                (L("Making charge and margin", "المصنعية والهامش"),
                 rng(ex["low"], ex["high"]) if ex else L("no shop data for this choice", "لا توجد بيانات محلات لهذا الاختيار")),
            ]
            if inp["has_stones"]:
                items.append((L("Stones", "الأحجار"), ui.sar(stones_value) if stones_value else L("value not included", "قيمتها غير داخلة في الإجمالي")))
            items.append((L("Subtotal before VAT", "المجموع قبل الضريبة"), rng(est.subtotal_low, est.subtotal_high)))
            if est.vat is None:
                items.append((L("VAT", "الضريبة"), L("not set: choose the VAT case in the optional details", "غير محددة: اختاري الحالة الضريبية من التفاصيل الاختيارية")))
            else:
                items.append((L(f"VAT ({est.vat * 100:.0f}%)", f"الضريبة ({est.vat * 100:.0f}%)"), rng(est.subtotal_low * est.vat, est.subtotal_high * est.vat)))
                items.append((L("Estimated total", "الإجمالي التقديري"), rng(est.total_low, est.total_high)))
            body = "".join(f"<tr class='{'total' if i == len(items) - 1 and est.vat is not None else ''}'><td>{k}</td><td class='v'>{v}</td></tr>"
                           for i, (k, v) in enumerate(items))
            shop_line = ""
            if ex:
                who = shop_name.get(inp["shop"], inp["shop"]) if inp["shop"] else L(f"{ex['n_shops']} shops", f"{ex['n_shops']} محلات")
                shop_line = L(f"<br>Shop survey: {who}, collected {ui.date_ar(SURVEY_DATE)} (prices before VAT).",
                              f"<br>مسح المحلات: {who}، جُمع في {ui.date_ar(SURVEY_DATE)} (الأسعار قبل الضريبة).")
            general_badge = (f'<div class="ey-demo">{L("General estimate for other pieces: the karat was not specified in the survey, so this is not a confirmed price for the chosen karat.", "تقدير عام للمشغولات: العيار غير محدد في المسح، فهذا ليس تسعيرة مؤكدة للعيار المختار.")}</div>'
                             if (ex and general) else "")
            src_line = ui.esc(src) + (f" ({ui.date_ar(src_date)})" if src_date is not None else "")
            st.markdown(
                f"""<div class="ey-invoice">{general_badge}
                <div class="head">{L('Estimated price of the piece', 'السعر التقديري للقطعة')}</div>
                <div class="big">{big}</div>
                <div class="sub">{sub} · {L(f"{inp['karat']}K", f"عيار {inp['karat']}")} · {CATEGORY_LABELS[inp['cat']]}</div>
                <table>{body}</table>
                <div class="foot">{L('An estimated range from a sample of shops, not a binding price.', 'نطاق تقديري مبني على عينة المحلات، وليس سعرًا إلزاميًا.') if ex else L('Gold value only, from the reference price; not a shop selling price.', 'قيمة الذهب فقط محسوبة من السعر المرجعي، وليست سعر بيع في محل.')}
                <br>{L('Price source', 'مصدر السعر')}: {src_line}. {L('Not a live price.', 'ليس سعرًا مباشرًا.')}{shop_line}</div></div>""",
                unsafe_allow_html=True,
            )
            if gw.get("note"):
                st.warning(ui.tr(gw["note"]))
            if inp["has_stones"] and not stones_value:
                st.info(L("The stone value is unknown, so it is not in the total.", "قيمة الأحجار غير معروفة، فهي غير داخلة في الإجمالي."))
            if not ex:
                if inp["cat"] == "bangles" and inp["karat"] != 21:
                    st.info(L("Bangle prices in the survey are for 21K only, so they are not applied to other karats. Showing the gold value only.",
                              "تسعيرة البناجر في المسح لعيار 21 فقط، ولا نطبقها على عيارات أخرى. نعرض قيمة الذهب فقط."))
                elif inp["shop"]:
                    st.info(L("This shop has no data for this choice (for example, Al-Bukhari does not sell 21K bangles) or it is not in the chosen city.",
                              "هذا المحل لا توجد له بيانات لهذا الاختيار (مثلًا البخاري لا يبيع بناجر عيار 21)، أو ليس في المدينة المختارة."))
                else:
                    st.info(L("No shop in the survey matches this choice. Showing the gold value only.",
                              "لا يوجد محل في المسح يطابق هذا الاختيار. نعرض قيمة الذهب فقط."))

            if ex:
                with st.expander(L("Range per shop", "النطاق لكل محل")):
                    per = pd.DataFrame([{
                        L("Shop", "المحل"): shop_name.get(s, s),
                        L("Making + margin (SAR)", "المصنعية والهامش (ريال)"): f"{lo:,.0f} – {hi:,.0f}",
                        L("Total (SAR)", "الإجمالي (ريال)"): (f"{(est.metal_value + lo + (stones_value or 0)) * (1 + (est.vat or 0)):,.0f} – "
                                                            f"{(est.metal_value + hi + (stones_value or 0)) * (1 + (est.vat or 0)):,.0f}"),
                    } for s, lo, hi in ex["per_shop"]])
                    st.dataframe(per, hide_index=True, width="stretch")
                    st.caption(L(f"Each shop is calculated on its own, then the lowest and highest totals are taken. The sample is {N_SHOPS} shops, not a full market survey.",
                                 f"يُحسب كل محل لوحده، ثم يؤخذ أقل وأعلى إجمالي. العينة {N_SHOPS} محلات، وليست مسحًا شاملًا للسوق."))

            with st.expander(L("How did we calculate it?", "كيف حسبناها؟")):
                base_line = (L("The gram price was entered by hand, so the karat factor was not applied.", "سعر الجرام أُدخل يدويًا، فلم نطبق معامل العيار عليه.")
                             if inp["gram_override"] else
                             L(f"{inp['karat']}K gram price = ounce price (USD) × {inp['fx']:.2f} ÷ {settings.OUNCE_IN_GRAMS} × {inp['karat']} ÷ 24 = {ui.sar(gram, 2)}",
                               f"سعر جرام عيار {inp['karat']} = سعر الأونصة (دولار) × {inp['fx']:.2f} ÷ {settings.OUNCE_IN_GRAMS} × {inp['karat']} ÷ 24 = {ui.sar(gram, 2)}"))
                st.markdown(L(
                    f"1. {base_line}\n"
                    f"2. Gold weight = {est.gold_w:.2f} g" + (" (total weight minus stones)." if gw["deducted"] else ".") + "\n"
                    f"3. Gold value = gram price × gold weight = {ui.sar(est.metal_value)}\n"
                    "4. Making charge and margin from the shop survey: SAR per gram × gold weight. For other pieces at Bareeq Eifa and Lamir, a profit of 20 to 30 SAR per piece is added once. "
                    "When the survey says the profit is inside the per-gram fee, nothing is added on top.\n"
                    "5. Each shop is calculated on its own, then the lowest and highest totals are taken.\n"
                    "6. VAT is applied once on the subtotal (gold + making and margin + known stones). The survey prices are before VAT.\n\n"
                    "**VAT assumption:** ZATCA says gold below 99% purity (such as 18K, 21K, 22K) is subject to 15% VAT when sold by a registered seller, and investment gold "
                    "(99% or more, tradable on the bullion market) is zero-rated. 24K jewelry is not automatically investment gold. "
                    f"[Source]({settings.SOURCES['vat'][1]})",
                    f"1. {base_line}\n"
                    f"2. وزن الذهب = {est.gold_w:.2f} جرام" + (" (الوزن الكلي ناقص وزن الأحجار)." if gw["deducted"] else ".") + "\n"
                    f"3. قيمة الذهب = سعر الجرام × وزن الذهب = {ui.sar(est.metal_value)}\n"
                    "4. المصنعية والهامش من مسح المحلات: ريال لكل جرام × وزن الذهب. ولباقي المشغولات في بريق إيفاء ولامير يضاف ربح 20 إلى 30 ريال للقطعة مرة واحدة. "
                    "إذا كان الربح داخل رسم الجرام لا يضاف شيء فوقه.\n"
                    "5. يُحسب كل محل لوحده، ثم يؤخذ أقل وأعلى إجمالي.\n"
                    "6. الضريبة تحسب مرة واحدة على المجموع (الذهب + المصنعية والهامش + الأحجار المعروفة). أسعار المسح قبل الضريبة.\n\n"
                    "**الافتراض الضريبي:** هيئة الزكاة والضريبة والجمارك توضح أن الذهب بنقاء أقل من 99% (مثل عيار 18 و21 و22) خاضع لضريبة 15% عند بيعه من بائع مسجل، "
                    "وأن الذهب الاستثماري بنقاء 99% فأكثر القابل للتداول في سوق السبائك خاضع لنسبة الصفر. مجوهرات عيار 24 ليست تلقائيًا ذهبًا استثماريًا. "
                    f"[المصدر]({settings.SOURCES['vat'][1]})"))

            clean = lambda x: str(x).replace("⁦", "").replace("⁩", "")
            lines = [L("EYAR: gold piece calculation summary", "عيار | EYAR: ملخص حساب قطعة ذهب"), "",
                     L("Inputs:", "المدخلات:"),
                     f"- {L('Karat', 'العيار')}: {inp['karat']}",
                     f"- {L('Piece type', 'نوع القطعة')}: {CATEGORY_LABELS[inp['cat']]}",
                     f"- {L('Piece weight', 'وزن القطعة')}: {inp['weight']} {L('g', 'جرام')}",
                     f"- {L('Has stones', 'فيها أحجار')}: {L('yes', 'نعم') if inp['has_stones'] else L('no', 'لا')}",
                     f"- {L('Gold weight used', 'وزن الذهب المحسوب')}: {est.gold_w:.2f} {L('g', 'جرام')}",
                     f"- {L('City', 'المدينة')}: {city_name.get(inp['city'], L('All cities', 'كل المدن')) if inp['city'] else L('All cities', 'كل المدن')}",
                     f"- {L('Shop', 'المحل')}: {shop_name.get(inp['shop'], inp['shop']) if inp['shop'] else L('Whole sample', 'نطاق العينة')}",
                     f"- {L('VAT case', 'الحالة الضريبية')}: {VAT_LABELS[inp['vat_case']]}",
                     "", L("Assumptions and price source:", "الافتراضات ومصدر السعر:"),
                     f"- {clean(src)}" + (f" ({ui.date_ar(src_date)})" if src_date is not None else ""),
                     f"- {L('USD to SAR', 'سعر الصرف')}: {inp['fx']}",
                     f"- {L('Gram price', 'سعر الجرام')} ({inp['karat']}K): {gram:,.2f} SAR",
                     f"- {L('Shop survey date', 'تاريخ مسح المحلات')}: {SURVEY_DATE} ({L('prices before VAT', 'الأسعار قبل الضريبة')})"
                     + (f" · {L('general estimate, karat not specified in the survey', 'تقدير عام، العيار غير محدد في المسح')}" if (ex and general) else ""),
                     "", L("Result:", "النتيجة:"),
                     f"- {L('Gold value', 'قيمة الذهب')}: {est.metal_value:,.0f} SAR"]
            if ex:
                lines.append(f"- {L('Making charge and margin', 'المصنعية والهامش')}: {ex['low']:,.0f} – {ex['high']:,.0f} SAR")
            if stones_value:
                lines.append(f"- {L('Stones', 'الأحجار')}: {stones_value:,.0f} SAR")
            lines.append(f"- {L('Subtotal before VAT', 'المجموع قبل الضريبة')}: {est.subtotal_low:,.0f} – {est.subtotal_high:,.0f} SAR")
            if est.vat is not None:
                lines.append(f"- {L('Total with VAT', 'الإجمالي مع الضريبة')}: {est.total_low:,.0f} – {est.total_high:,.0f} SAR")
            lines += ["", L("An estimated range from a sample of 6 shops, not a binding price. Not a live price.",
                            "نطاق تقديري مبني على عينة من 6 محلات، وليس سعرًا إلزاميًا. ليس سعرًا مباشرًا.")]
            st.download_button(L("Download the calculation summary", "تنزيل ملخص الحساب"), "\n".join(lines).encode("utf-8-sig"),
                               file_name="eyar_calculation.txt", mime="text/plain", icon=":material/download:", width="stretch")

    # ---- shop offer comparison ----
    if est is not None:
        inp = inputs()
        with st.expander(L("Have an offer from a shop? Compare it here", "عندك عرض من محل؟ قارنه هنا"), icon=":material/compare_arrows:"):
            offer = st.number_input(L("Offered price (SAR)", "السعر المعروض (ريال)"), min_value=0.0, value=None, step=50.0, key="offer")
            inc_vat = st.radio(L("Does the price include VAT?", "هل يشمل السعر الضريبة؟"), ["yes", "no", "unknown"], horizontal=True,
                               key=ui.lkey("offer_vat", "yes"), on_change=ui.sync, args=("offer_vat",),
                               format_func={"yes": L("Yes", "نعم"), "no": L("No", "لا"), "unknown": L("I don't know", "لا أعرف")}.get)
            inc_st = st.checkbox(L("The price includes the stones", "السعر يشمل الأحجار"), value=True, key="offer_stones") if inp["has_stones"] else False
            if offer:
                c = calc.compare_offer(est, offer, inc_vat, inp["has_stones"], inc_st)
                s = c["status"]
                if s in ("invalid", "insufficient"):
                    st.warning(ui.tr(c["reason"]))
                else:
                    st.markdown(f"{L('Offer before VAT', 'العرض قبل الضريبة')}: **{ui.sar(c['pre_vat'])}**", unsafe_allow_html=True)
                    if s == "no_range":
                        st.info(L("No shop range for this choice, so we show only the difference from the gold value.",
                                  "لا يوجد نطاق محلات لهذا الاختيار، لذلك نعرض الفرق عن قيمة الذهب فقط."))
                    else:
                        label = {"below": L("Below the range", "أقل من النطاق"), "within": L("Within the range", "داخل النطاق"),
                                 "above": L("Above the range", "أعلى من النطاق")}[s]
                        diff = "" if s == "within" else L(f" by {ui.sar(abs(c['diff']))} from the {'lower' if s == 'below' else 'upper'} limit",
                                                          f" بفرق {ui.sar(abs(c['diff']))} عن {'الحد الأدنى' if s == 'below' else 'الحد الأعلى'}")
                        st.markdown(f"<span class='ey-badge {s}'>{label}</span>{diff}", unsafe_allow_html=True)
                        st.caption(L(f"Range before VAT: {ui.num(c['low'])} to {ui.num(c['high'])} SAR.", f"النطاق قبل الضريبة: {ui.num(c['low'])} إلى {ui.num(c['high'])} ريال."))
                    st.markdown(L(f"Implicit additions above the gold value{' and stones' if inc_st and est.stones_value else ''}: **{ui.sar(c['implicit'])}** (about {ui.sar(c['implicit_per_gram'], 1)} per gram).",
                                  f"الإضافات الضمنية فوق قيمة الذهب{' والأحجار' if inc_st and est.stones_value else ''}: **{ui.sar(c['implicit'])}** (تقريبًا {ui.sar(c['implicit_per_gram'], 1)} لكل جرام)."),
                                unsafe_allow_html=True)
                    if c["implicit"] < 0:
                        st.info(L("The offer is below the calculated gold value. Check the weight, the karat, and whether the price includes VAT.",
                                  "العرض أقل من قيمة الذهب المحسوبة. تأكدي من الوزن والعيار، وهل السعر يشمل الضريبة."))
                    st.caption(L("Implicit additions may include the making charge, shop margin and other items; they are not necessarily the shop's profit. An offer above the range is not proof of overcharging; the range comes from a small sample.",
                                 "الإضافات الضمنية قد تشمل المصنعية وهامش المحل وعناصر أخرى، وليست بالضرورة ربح المحل. كون العرض أعلى من النطاق لا يعني غشًا؛ النطاق مبني على عينة محدودة."))

# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------
st.divider()
st.subheader(L("How much gold can my budget buy?", "ميزانيتي كم تجيب؟"))
inp = inputs()
bc1, bc2, bc3 = st.columns([1, 1, 1.4])
budget = bc1.number_input(L("Budget (SAR, including VAT)", "الميزانية (ريال، شاملة الضريبة)"), min_value=0.0, value=None, step=500.0,
                          placeholder=L("e.g. 5000", "مثال: 5000"), key="bud_amount")
bkarat = bc2.selectbox(L("Karat", "العيار"), settings.KARATS, format_func=lambda k: L(f"{k}K", f"عيار {k}"),
                       key=ui.lkey("bud_karat", inp["karat"]), on_change=ui.sync, args=("bud_karat",))
with bc3:
    if budget:
        b_inp = dict(inp)
        if b_inp.get("gram_override") and bkarat != inp["karat"]:
            b_inp["gram_override"] = None  # a manual gram price belongs to one karat only
        b_inp["karat"] = bkarat
        gram_b, _, _ = price_source(b_inp)
        case = inp["vat_case"]
        vat_b = calc.vat_rate(case) if not (case == "investment" and bkarat != 24) else settings.VAT_STANDARD
        assumed = vat_b is None
        vat_b = settings.VAT_STANDARD if vat_b is None else vat_b
        rows_b, general_b = shop_rows(b_inp, bkarat)
        res = calc.budget_weight(budget, gram_b, rows_b if not rows_b.empty else None, vat_b)
        unit = L("g", "جرام")
        if not res["ok"]:
            st.warning(L("Enter a budget greater than zero.", "أدخلي ميزانية أكبر من صفر."))
        elif res["metal_only"]:
            st.markdown(f"<div class='ey-card'><div class='lbl'>{L('Approximate weight', 'الوزن التقريبي')}</div>"
                        f"<div class='val'>{L('up to', 'حتى')} {ui.num(res['high'], 1)} {unit}</div>"
                        f"<div class='desc'>{L('Gold value only, with VAT. No shop data for this choice, so the real weight will be lower.', 'للمعدن فقط مع الضريبة. لا توجد بيانات محلات لهذا الاختيار، فالوزن الفعلي سيكون أقل.')}</div></div>",
                        unsafe_allow_html=True)
        else:
            lo_w, hi_w = ui.num(res["low"], 1), ui.num(res["high"], 1)
            weight_txt = L(f"{lo_w} to {hi_w} g", f"من {lo_w} إلى {hi_w} جرام")
            st.markdown(f"<div class='ey-card'><div class='lbl'>{L('Approximate weight', 'الوزن التقريبي')}</div>"
                        f"<div class='val'>{weight_txt}</div>"
                        f"<div class='desc'>{L('Based on the shop survey range, including VAT', 'حسب نطاق مسح المحلات، شامل الضريبة')} · {CATEGORY_LABELS[inp['cat']]}"
                        f"{L(' · general estimate, karat not specified in the survey', ' · تقدير عام، العيار غير محدد في المسح') if general_b else ''}</div></div>",
                        unsafe_allow_html=True)
        if assumed:
            st.caption(L("The VAT case is not set, so we assumed 15% (jewelry).", "الحالة الضريبية غير محددة، فافترضنا 15% (مشغولات)."))
    else:
        st.caption(L("Enter a budget to see an approximate weight range. It uses the piece type, city and shop chosen above.",
                     "اكتبي الميزانية لنعرض نطاقًا تقريبيًا للوزن. يستخدم نوع القطعة والمدينة والمحل المختارة في الأعلى."))

if survey_msgs:
    with st.expander(L("Notes on the shop survey file", "ملاحظات على ملف مسح المحلات")):
        for m in survey_msgs:
            st.caption(m)
