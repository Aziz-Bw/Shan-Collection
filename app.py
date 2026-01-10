import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="تحصيل شان - بطاقات العملاء", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .main-card {
        border: 2px solid #034275;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 35px;
        background-color: #ffffff;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
    }
    .customer-header {
        background-color: #034275;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .metric-box {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #ddd;
    }
    .aging-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .aging-table th, .aging-table td { 
        border: 1px solid #ddd; padding: 8px; text-align: center; font-size: 14px;
    }
    .aging-table th { background-color: #f8f9fa; }
    .urgent-payment { color: #d32f2f; font-weight: bold; font-size: 18px; }
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
    df['Date'] = pd.to_datetime(pd.to_numeric(df['TransDateValue'], errors='coerce'), unit='D', origin='1899-12-30')
    return df

# --- 3. القائمة الجانبية والقائمة المعتمدة ---
with st.sidebar:
    st.header("📂 إدارة البيانات")
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

# --- 4. المعالجة والعرض ---
if f_ledger:
    df = load_data(f_ledger)
    today = datetime.now()
    df_filtered = df[df['LedgerName'].str.strip().isin([n.strip() for n in target_names])].copy()

    if not df_filtered.empty:
        st.title("📇 سجل متابعة مديونيات العملاء")
        
        index = 1
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name].sort_values('Date', ascending=False)
            if c_data.empty: continue
            
            balance = c_data['Dr'].sum() - c_data['Cr'].sum()
            if balance <= 1: continue

            # حساب تعمير الديون (Aging)
            aging = {"0-30": 0, "31-60": 0, "61-90": 0, "91-120": 0, "+120": 0}
            temp_bal = balance
            for _, row in c_data[c_data['Dr'] > 0].iterrows():
                if temp_bal <= 0: break
                days = (today - row['Date']).days
                amt = min(row['Dr'], temp_bal)
                if days <= 30: aging["0-30"] += amt
                elif days <= 60: aging["31-60"] += amt
                elif days <= 90: aging["61-90"] += amt
                elif days <= 120: aging["91-120"] += amt
                else: aging["+120"] += amt
                temp_bal -= amt
            
            # المبلغ المستحق (أكثر من 60 يوم)
            overdue_60 = aging["61-90"] + aging["91-120"] + aging["+120"]

            # عرض البطاقة مع الحدود (Border)
            st.markdown(f"""
            <div class="main-card">
                <div class="customer-header">
                    <span style="font-size: 20px; font-weight: bold;">#{index} - {name}</span>
                    <span style="font-size: 16px;">إجمالي المديونية: {balance:,.2f} ر.س</span>
                </div>
            """, unsafe_allow_html=True)
            
            col_m1, col_m2 = st.columns(2)
            col_m1.markdown(f'<div class="metric-box"><b>إجمالي الرصيد</b><br><span style="font-size:20px; color:#034275;">{balance:,.2f}</span></div>', unsafe_allow_html=True)
            col_m2.markdown(f'<div class="metric-box"><b>المستحق سداده (>60 يوم)</b><br><span class="urgent-payment">{overdue_60:,.2f}</span></div>', unsafe_allow_html=True)

            st.write("#### 📊 تعمير الديون (Aging)")
            st.markdown(f"""
            <table class="aging-table">
                <tr><th>0-30 يوم</th><th>31-60 يوم</th><th>61-90 يوم</th><th>91-120 يوم</th><th>+120 يوم</th></tr>
                <tr>
                    <td>{aging['0-30']:,.2f}</td><td>{aging['31-60']:,.2f}</td>
                    <td style="background:#fff3f3;">{aging['61-90']:,.2f}</td>
                    <td style="background:#fff3f3;">{aging['91-120']:,.2f}</td>
                    <td style="background:#fff3f3;">{aging['+120']:,.2f}</td>
                </tr>
            </table>
            """, unsafe_allow_html=True)

            st.write("#### 📈 تحليل النشاط (آخر 3 أشهر)")
            stats_cols = st.columns(3)
            for i in range(3):
                m_date = (today.replace(day=1) - timedelta(days=i*30))
                m_data = c_data[(c_data['Date'].dt.month == m_date.month) & (c_data['Date'].dt.year == m_date.year)]
                buy_val = m_data['Dr'].sum()
                pay_val = m_data['Cr'].sum()
                with stats_cols[i]:
                    st.info(f"**{m_date.strftime('%m-%Y')}**")
                    st.write(f"🛒 فواتير: {len(m_data[m_data['Dr']>0])} | {buy_val:,.0f} ر.س")
                    st.write(f"💰 دفعات: {len(m_data[m_data['Cr']>0])} | {pay_val:,.0f} ر.س")
            
            st.markdown("</div>", unsafe_allow_html=True)
            index += 1
    else:
        st.warning("ارفع الملف لعرض البيانات.")
