import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="تحصيل شان - مركز القيادة المطور", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .kpi-card { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 10px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; height: 110px; display: flex; flex-direction: column; justify-content: center; }
    .kpi-title { font-size: 12px; color: #666; margin-bottom: 3px; font-weight: bold; }
    .kpi-value { font-size: 18px; font-weight: bold; color: #034275; }
    .main-card { border: 2px solid #034275; padding: 20px; border-radius: 12px; margin-bottom: 30px; background-color: #ffffff; }
    .customer-header { background-color: #034275; color: white; padding: 12px 20px; border-radius: 8px; display: flex; justify-content: space-between; }
    .aging-table { width: 100%; border-collapse: collapse; }
    .aging-table th, .aging-table td { border: 1px solid #eee; padding: 8px; text-align: center; font-size: 12px; }
    .urgent-box { background:#fdf2f2; border: 1px solid #f5c6cb; padding:10px; border-radius:8px; text-align:center; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. دالة القراءة مع استبعاد المرتجعات من التحصيل ---
def load_data(file):
    if file is None: return None
    file.seek(0)
    tree = ET.parse(file)
    data = [{child.tag: child.text for child in row} for row in tree.getroot()]
    df = pd.DataFrame(data)
    df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
    df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
    df['Date'] = pd.to_datetime(pd.to_numeric(df['TransDateValue'], errors='coerce'), unit='D', origin='1899-12-30')
    
    # تصنيف الحركات: (المرتجعات عادة يكون لها كود حساب 4111002 أو وصف معين)
    # سنفترض استبعاد الحركات التي تأتي من حسابات المرتجعات لضمان دقة "التحصيل النقدي"
    df['IsReturn'] = df['AcLedger'].astype(str).str.contains('4111002|3111002|3112002') 
    return df

# --- 3. قائمة الأسماء المستهدفة ---
target_names = [
    "شركة الريادة العربية التجارية", "شركة أصل الشرق لقطع غيار السيارات فرع 14", "شركة ركن الأمجاد المتحدة للتجارة",
    "شركة موجود المتحدة للتجارة", "مؤسسة وتين الغربية التجارية", "شركة بن شيهون البركة التجارية فرع 14",
    "مؤسسة علي فريد علي المرهون (عالم ام جي)", "شركة خالد حامد سالم المحمادي التجارية", "مؤسسة جود الجزيرة لقطع غيار السيارات",
    "مؤسسة الابداع الصيني لقطع غيار السيارات", "مؤسسة عواطف سالم باجابر", "شركة ارض الذهب للذهب و المجوهرات",
    "شركة بن شيهون البركة التجارية فرع النزهة", "مؤسسة الراقي العالمي لقطع الغيار", "مؤسسة الاقبال التجارية",
    "مؤسسة الامداد الحصري التجارية", "مؤسسة رواد الجودة لقطع الغيار", "مؤسسة وفاق الفرسان للتجارة",
    "مؤسسة الوفاء الخالدة لتجارة الجملة والتجزئة", "شركة أصل المصدر الرائدة لقطع غيار السيارات",
    "مؤسسة عبود صالح باحشوان لقطع غيار السيارات", "شركة اسطورة الشرق التجارية", "مؤسسة الشامل المتميز لقطع غيار السيارات",
    "شركة أصل الشرق لقطع غيار السيارات فرع بني مالك", "شركة ركن الصناعية للتجارة", "مؤسسة رواد اسيا لقطع غيار السيارات",
    "شركة قلب الصقر للتجارة", "شركة الاتحاد المتطورة للتجارة", "مؤسسة رمز الصفوة لقطع غيار السيارات 3 فرع محايل",
    "شركة تمكين الخليجية للتجارة", "مؤسسة حلول المركبة لقطع غيار السيارات", "مؤسسة رمز الصفوة لقطع غيار السيارات المركز الصيني بني مالك",
    "شركة السلام التجارية", "شركة المحرك الأفضل لتجارة الجملة والتجزئة", "مؤسسة الزعيم واحد لقطع غيار السيارات",
    "مؤسسة المستقبل الحديث لقطع غيار السيارات", "خالي سالم", "مؤسسة درب العطاء المتكامل لقطع غيار السيارات",
    "شركة الإنجازات لتجارة الجملة و التجزئة", "منقذة لقطع غيار السيارات"
]

if 'f_ledger' not in st.session_state:
    with st.sidebar:
        st.header("📂 البيانات")
        f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'])
        if f_ledger: st.session_state.f_ledger = load_data(f_ledger)

if 'f_ledger' in st.session_state:
    df_raw = st.session_state.f_ledger
    today = datetime.now()
    df_filtered = df_raw[df_raw['LedgerName'].str.strip().isin([n.strip() for n in target_names])].copy()

    # فصل السدادات النقدية (التحصيل الحقيقي) عن المرتجعات
    df_collection = df_filtered[(df_filtered['Cr'] > 0) & (df_filtered['IsReturn'] == False)]

    # --- حساب KPIs (مع استبعاد المرتجعات) ---
    global_overdue_amt = 0
    for name in target_names:
        c_data = df_filtered[df_filtered['LedgerName'] == name]
        bal = c_data['Dr'].sum() - c_data['Cr'].sum()
        if bal <= 1: continue
        temp_bal = bal
        for _, r in c_data.sort_values('Date', ascending=False)[c_data['Dr'] > 0].iterrows():
            if temp_bal <= 0: break
            days = (today - r['Date']).days
            amt = min(r['Dr'], temp_bal)
            if days > 60: global_overdue_amt += amt
            temp_bal -= amt

    # تحصيل الأسابيع والشهور (نستخدم df_collection فقط)
    # [نفس منطق الحساب السابق مطبق على df_collection]

    st.markdown("### 📊 لوحة مراقبة التحصيل (بعد استبعاد المرتجعات)")
    # [عرض البطاقات بنفس التنسيق السابق]

    st.divider()

    # --- بطاقات العملاء ---
    index = 1
    for name in target_names:
        c_all = df_filtered[df_filtered['LedgerName'] == name].sort_values('Date', ascending=False)
        total_bal = c_all['Dr'].sum() - c_all['Cr'].sum()
        if total_bal <= 1: continue

        # عند عرض "عدد السدادات" نستخدم فقط الحركات التي ليست IsReturn
        # [منطق عرض الجدول التفصيلي]
        st.markdown(f'<div class="main-card"><div class="customer-header"><span>#{index} - {name}</span><span>الرصيد: {total_bal:,.2f}</span></div>', unsafe_allow_html=True)
        # ... تكملة الجدول ...
        index += 1
