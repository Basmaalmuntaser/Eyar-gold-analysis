"""Page 4: About the data / عن البيانات."""
import pandas as pd
import streamlit as st

from utils import settings, ui
from utils.i18n import L

df = ui.get_data()
survey, _ = ui.get_survey()

st.markdown(
    f"""<div class="ey-hero"><div class="ey-kicker">{L('EYAR | About the data', 'عيار | عن البيانات')}</div>
    <h1>{L('Where do the numbers come from?', 'من أين جاءت الأرقام؟')}</h1>
    <div class="ey-lead">{L("I love gold, and many people in Saudi Arabia buy it for saving and jewelry. I asked my grandmother, who has long experience with gold, why it goes up and down, and she said oil and world events affect it. This project tests that idea with real data.",
                            "أحب الذهب، وكثير من الناس في السعودية يشترونه للادخار وللزينة. سألت جدتي، صاحبة الخبرة الطويلة مع الذهب، لماذا يرتفع وينزل، فقالت إن النفط والأحداث العالمية تؤثر عليه. هذا المشروع يختبر هذه الفكرة ببيانات حقيقية.")}</div></div>""",
    unsafe_allow_html=True,
)

ui.cards([
    {"label": L("Actual period", "الفترة الفعلية"), "value": f"{df['Date'].min().year} – {df['Date'].max().year}",
     "desc": f"{ui.date_ar(df['Date'].min())} – {ui.date_ar(df['Date'].max())}"},
    {"label": L("Rows", "عدد الصفوف"), "value": ui.num(len(df)), "desc": L("each row is a gold trading day", "كل صف يوم تداول للذهب")},
    {"label": L("Updates", "تحديث البيانات"), "value": L("Frozen", "مجمدة"), "desc": L("historical data, does not update automatically", "بيانات تاريخية لا تتحدث تلقائيًا")},
], cols=3)

st.subheader(L("Sources", "المصادر"))
st.markdown(L(
    f"- **Gold:** [{settings.SOURCES['gold'][0]}]({settings.SOURCES['gold'][1]}): gold futures price in USD per ounce.\n"
    f"- **Oil:** [{settings.SOURCES['oil'][0]}]({settings.SOURCES['oil'][1]}): WTI crude oil spot price in USD per barrel.\n"
    "- **Different methods:** gold is a **futures** price and oil is a **spot** price, so they are not identical kinds of price.\n"
    "- **Currency:** everything in the app is shown in SAR using the notebook conversion: 3.75 SAR per USD and 31.1035 grams per ounce. "
    "Gold is in SAR per gram (24K unless another karat is stated) and oil in SAR per barrel. Percentages and correlations do not change.",
    f"- **الذهب:** [{settings.SOURCES['gold'][0]}]({settings.SOURCES['gold'][1]}): سعر عقود الذهب الآجلة بالدولار للأونصة.\n"
    f"- **النفط:** [{settings.SOURCES['oil'][0]}]({settings.SOURCES['oil'][1]}): سعر خام غرب تكساس الفوري بالدولار للبرميل.\n"
    "- **اختلاف المنهجية:** الذهب سعر **عقود آجلة**، والنفط سعر **فوري**.\n"
    "- **العملة:** كل ما في التطبيق معروض بالريال حسب تحويل النوتبوك: 3.75 ريال للدولار، و31.1035 جرام للأونصة. "
    "الذهب بالريال للجرام (عيار 24 ما لم يُذكر غيره)، والنفط بالريال للبرميل. النسب والارتباط لا تتغير."))

st.subheader(L("Columns", "الأعمدة"))
st.dataframe(pd.DataFrame([
    ["Date", L("Trading day", "تاريخ يوم التداول"), L("date", "تاريخ")],
    ["Close / Open / High / Low", L("Gold futures prices", "أسعار عقود الذهب"), L("USD per ounce (shown as SAR per gram)", "دولار للأونصة (يُعرض ريال للجرام)")],
    ["Oil_Price", L("WTI oil price", "سعر النفط WTI"), L("USD per barrel (shown as SAR per barrel)", "دولار للبرميل (يُعرض ريال للبرميل)")],
    ["Gold_Return / Oil_Return", L("Daily % change", "التغير اليومي"), "%"],
    ["Year / Month", L("From the date", "من التاريخ"), L("number", "رقم")],
    [L("Drawdown (computed)", "Drawdown (محسوب)"), L("% below the earlier highest close", "كم السعر تحت أعلى إغلاق سابق"), "%"],
    [L("Gram price in SAR (computed)", "سعر الجرام بالريال (محسوب)"), L("ounce price × 3.75 ÷ 31.1035 × karat ÷ 24", "سعر الأونصة × 3.75 ÷ 31.1035 × العيار ÷ 24"), L("SAR per gram", "ريال للجرام")],
], columns=[L("Column", "العمود"), L("Meaning", "المعنى"), L("Unit", "الوحدة")]), hide_index=True, width="stretch")

st.subheader(L("Cleaning steps", "خطوات التنظيف"))
st.markdown(L(
    "1. Download gold from Yahoo Finance and oil from FRED, with a fixed end date for gold.\n"
    "2. Convert the oil date, keep data from 2015, rename the columns.\n"
    "3. Drop the trading volume column because the analysis focuses on prices.\n"
    "4. Merge both tables by date, keeping every gold trading day.\n"
    "5. **Missing values:** missing oil days were filled with the last known price (forward fill). These days were not flagged in the file, so the app cannot identify them.\n"
    "6. The oil price was negative on 20 April 2020: the price is kept, and the oil return is excluded when today's or the previous price is not positive.\n"
    "7. No duplicate rows. The clean table was saved as gold_oil_clean.csv.",
    "1. تحميل الذهب من Yahoo Finance والنفط من FRED، وتثبيت تاريخ نهاية تحميل الذهب.\n"
    "2. تحويل تاريخ النفط، والاحتفاظ ببيانات 2015 فما بعد، وإعادة تسمية الأعمدة.\n"
    "3. حذف عمود حجم التداول لأن التحليل يركز على الأسعار.\n"
    "4. دمج الجدولين حسب التاريخ مع الاحتفاظ بكل أيام تداول الذهب.\n"
    "5. **القيم الناقصة:** أيام النفط الناقصة عُوّضت بآخر سعر معروف. علامات الأيام المعوّضة لم تُحفظ في الملف، فلا يمكن تحديدها هنا.\n"
    "6. سعر النفط كان سالبًا في 20 أبريل 2020: أبقينا السعر واستبعدنا عائد النفط عندما يكون السعر الحالي أو السابق غير موجب.\n"
    "7. لا توجد صفوف مكررة. حُفظ الجدول النظيف في gold_oil_clean.csv."))

st.subheader(L("Definitions", "تعريفات"))
st.markdown(L(
    "- **Daily return:** % change from the previous trading day, computed on the full data before any filter.\n"
    "- **Drawdown:** how far the price is below the highest close reached before.\n"
    "- **Holding periods:** 1 year ≈ 252 trading sessions, 3 years ≈ 756, 5 years ≈ 1,260.\n"
    "- **Yearly return:** from the first close to the last close inside the year.\n"
    "- **IQR limits:** Q1 − 1.5 × IQR and Q3 + 1.5 × IQR, used to find unusual days.",
    "- **العائد اليومي:** نسبة تغير السعر عن يوم التداول السابق، على كامل البيانات قبل أي فلتر.\n"
    "- **الانخفاض من القمة (Drawdown):** كم السعر تحت أعلى إغلاق وصل له قبل ذلك.\n"
    "- **مدد الاحتفاظ:** سنة = 252 جلسة تداول تقريبًا، و3 سنوات = 756، و5 سنوات = 1,260.\n"
    "- **العائد السنوي:** من أول إغلاق إلى آخر إغلاق داخل السنة.\n"
    "- **حدود IQR:** الربع الأول − 1.5 × IQR والربع الثالث + 1.5 × IQR، لاكتشاف الأيام غير المعتادة."))

st.subheader(L("Limits of the study", "حدود الدراسة"))
st.markdown(L(
    "- 2015 to 2026 was a strong period for gold; results may differ in the future.\n"
    "- Futures prices differ from shop prices.\n"
    "- Only three world events; timing does not prove cause.\n"
    "- Correlation measures the same-day linear relationship only.\n"
    "- The app does not predict prices.",
    "- الفترة 2015 إلى 2026 كانت قوية للذهب، والنتائج قد تختلف مستقبلًا.\n"
    "- أسعار العقود الآجلة تختلف عن أسعار المحلات.\n"
    "- ثلاثة أحداث عالمية فقط، والتزامن لا يثبت السببية.\n"
    "- الارتباط يقيس العلاقة الخطية في نفس اليوم فقط.\n"
    "- التطبيق لا يتنبأ بالأسعار."))

st.subheader(L("Shop survey (making charge and margin)", "مسح المحلات (المصنعية والهامش)"))
st.markdown(L(
    "Collected by the project owner on **29 October 2026** from **6 shops** in Makkah and Riyadh. All prices are **before VAT**, per gram, "
    "except the per-piece profit at two shops. Bangle prices are for **21K**; Al-Bukhari does not sell 21K. "
    "The karat for “other pieces” was not specified, so those ranges are a general estimate, not a confirmed price for any karat. "
    "This is a small sample, not a full market survey, and it does not rate the shops.",
    "جمعتها صاحبة المشروع يوم **29 أكتوبر 2026** من **6 محلات** في مكة والرياض. كل الأسعار **قبل الضريبة** ولكل جرام، "
    "عدا الربح لكل قطعة في محلين. تسعيرة البناجر لعيار **21**، والبخاري لا يبيع عيار 21. "
    "عيار «المشغولات الأخرى» غير محدد في المسح، فنطاقاتها تقدير عام وليست تسعيرة مؤكدة لأي عيار. "
    "هذه عينة صغيرة وليست مسحًا شاملًا للسوق، ولا تقيّم المحلات."))
if not survey.empty:
    sv = pd.DataFrame({
        L("Shop", "المحل"): [L(a, b) for a, b in zip(survey["shop_en"], survey["shop_ar"])],
        L("City", "المدينة"): [L(a, b) for a, b in zip(survey["city_en"], survey["city_ar"])],
        L("Piece type", "نوع القطعة"): [L("Bangles", "بناجر") if c == "bangles" else L("Other pieces", "مشغولات أخرى") for c in survey["category"]],
        L("Karat", "العيار"): [str(int(k)) if pd.notna(k) else L("not specified", "غير محدد") for k in survey["karat"]],
        L("Available", "متوفر"): [L("yes", "نعم") if a else L("no", "لا") for a in survey["available"]],
        L("Fee (SAR/g)", "الرسم (ريال/جرام)"): [f"{a:g}–{b:g}" if a != b else f"{a:g}" if av else "—"
                                                for a, b, av in zip(survey["fee_min_per_g"], survey["fee_max_per_g"], survey["available"])],
        L("Profit included", "الربح مشمول"): [L("yes", "نعم") if p else L("no, +{}–{} SAR per piece", "لا، +{}–{} ريال للقطعة").format(f"{a:g}", f"{b:g}")
                                               for p, a, b in zip(survey["profit_included"], survey["fixed_profit_min"], survey["fixed_profit_max"])],
    })
    st.dataframe(sv, hide_index=True, width="stretch")

st.subheader(L("Preview and download", "معاينة وتنزيل"))
st.dataframe(df[["Date", "Close", "High", "Low", "Open", "Oil_Price", "Gold_Return", "Oil_Return"]].tail(200),
             hide_index=True, width="stretch", height=280,
             column_config={"Date": st.column_config.DateColumn(format="YYYY-MM-DD")})
st.caption(L("Original cleaned file (prices in USD, as saved by the notebook).", "الملف المنظف الأصلي (الأسعار بالدولار كما حفظها النوتبوك)."))
c1, c2 = st.columns(2)
c1.download_button(L("Download the original cleaned data (CSV)", "تنزيل البيانات المنظفة الأصلية (CSV)"), settings.DATA_FILE.read_bytes(),
                   file_name="gold_oil_clean.csv", mime="text/csv", icon=":material/download:", width="stretch")
enriched = df.drop(columns=["Running_Max"]).to_csv(index=False).encode("utf-8-sig")
c2.download_button(L("Download with computed SAR columns (CSV)", "تنزيل البيانات مع أعمدة الريال المحسوبة (CSV)"), enriched,
                   file_name="gold_oil_enriched.csv", mime="text/csv", icon=":material/download:", width="stretch")
st.caption(L("Educational project in a data science bootcamp. Not financial advice.", "مشروع تعليمي ضمن معسكر علم البيانات. ليس نصيحة مالية."))
