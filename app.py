import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="تحصيل شان - بطاقات العملاء", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .customer-card {
        background-color: #f8f9fa;
        border-right: 5px solid #034275;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .aging-box { text-align: center; padding: 10px; border-radius: 5px; background: #fff; border: 1px solid #eee; }
    .aging-val { font-weight: bold; color: #034275; font-size: 16px; }
    .aging-label { font-size: 12px; color: #666; }
</style>
""", unsafe_allow_html=True)

# --- 2. الدوال الأساسية ---
def load_data(file):
    if file is None: return None
    file.seek(0)
    tree = ET.parse(file)
    data = [{child.tag: child.text for child in row} for row in tree.getroot()]
    df = pd.DataFrame(data)
    df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
    df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
    # تحويل التاريخ (تنسيق ملفات البرنامج عادة يكون Excel serial date)
    df['Date'] = pd.to_datetime(pd.to_numeric(df['TransDateValue'], errors='coerce'), unit='D', origin='1899-12-30')
    return df

# --- 3. القائمة الجانبية ---
with st.sidebar:
    st.header("📂 البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'])
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

# --- 4. معالجة وعرض البطاقات ---
if f_ledger:
    df = load_data(f_ledger)
    today = datetime.now()
    
    # تصفية القائمة المطلوبة فقط
    df_filtered = df[df['LedgerName'].str.strip().isin([n.strip() for n in target_names])].copy()
    
    if not df_filtered.empty:
        st.title("📇 بطاقات متابعة تحصيل العملاء")
        
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name].sort_values('Date', ascending=False)
            if c_data.empty: continue
            
            balance = c_data['Dr'].sum() - c_data['Cr'].sum()
            if balance <= 1: continue # تخطي الحسابات المسددة
            
            # --- أ. حساب أعمار الديون (Aging) ---
            # نعتمد على الفواتير غير المسددة (تقريبياً من الرصيد الحالي)
            aging = {"0-30": 0, "31-60": 0, "61-90": 0, "91-120": 0, "+120": 0}
            temp_balance = balance
            for _, row in c_data.iterrows():
                if temp_balance <= 0: break
                if row['Dr'] > 0:
                    days = (today - row['Date']).days
                    amount = min(row['Dr'], temp_balance)
                    if days <= 30: aging["0-30"] += amount
                    elif days <= 60: aging["31-60"] += amount
                    elif days <= 90: aging["61-90"] += amount
                    elif days <= 120: aging["91-120"] += amount
                    else: aging["+120"] += amount
                    temp_balance -= amount

            # --- ب. عرض بطاقة العميل ---
            with st.container():
                st.markdown(f'<div class="customer-card"><h3>👤 {name}</h3>', unsafe_allow_html=True)
                
                # صف تعمير الديون
                st.write("**📊 تعمير المديونية (Aging):**")
                cols = st.columns(5)
                for i, (label, val) in enumerate(aging.items()):
                    cols[i].markdown(f'<div class="aging-box"><div class="aging-label">{label}</div><div class="aging-val">{val:,.0f}</div></div>', unsafe_allow_html=True)
                
                st.write("---")
                
                # صف الإحصائيات (آخر 3 أشهر)
                st.write("**📈 تحليل المسحوبات والسداد (آخر 3 أشهر):**")
                stats_cols = st.columns(3)
                
                for i in range(3):
                    # تحديد الفترة (الشهر الحالي، السابق، قبله)
                    target_month = (today.replace(day=1) - timedelta(days=i*30)).month
                    target_year = (today.replace(day=1) - timedelta(days=i*30)).year
                    m_name = (today.replace(day=1) - timedelta(days=i*30)).strftime("%B %Y")
                    
                    m_data = c_data[(c_data['Date'].dt.month == target_month) & (c_data['Date'].dt.year == target_year)]
                    
                    buy_count = len(m_data[m_data['Dr'] > 0])
                    buy_val = m_data['Dr'].sum()
                    pay_count = len(m_data[m_data['Cr'] > 0])
                    pay_val = m_data['Cr'].sum()
                    
                    with stats_cols[i]:
                        st.markdown(f"**🗓️ {m_name}**")
                        st.caption(f"🛒 شراء: {buy_count} فاتورة ({buy_val:,.0f} ر.س)")
                        st.caption(f"💰 سداد: {pay_count} دفعة ({pay_val:,.0f} ر.س)")
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("لم يتم العثور على بيانات للأسماء المحددة.")
else:
    st.info("💡 ارفع ملف LedgerBook.xml لعرض بطاقات التحليل الذكية.")
