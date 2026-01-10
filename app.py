import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="تحصيل شان - مركز القيادة", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    
    /* بطاقات KPI العلوية */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 10px;
    }
    .kpi-title { font-size: 12px; color: #666; margin-bottom: 3px; font-weight: bold; }
    .kpi-value { font-size: 17px; font-weight: bold; color: #034275; }
    .kpi-sub { font-size: 10px; color: #888; }
    
    /* بطاقة العميل */
    .main-card {
        border: 2px solid #034275;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        background-color: #ffffff;
    }
    .customer-header {
        background-color: #034275;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .aging-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
    .aging-table th, .aging-table td { 
        border: 1px solid #eee; padding: 10px; text-align: center; font-size: 13px;
    }
    .aging-table th { background-color: #f1f3f5; color: #034275; }
    .val-outstanding { font-weight: bold; color: #d32f2f; font-size: 15px; }
    .urgent-box { background:#fdf2f2; border: 1px solid #f5c6cb; padding:10px; border-radius:8px; text-align:center; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. دالة القراءة ---
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

# --- 4. واجهة المستخدم ---
with st.sidebar:
    st.header("📂 إدارة البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'])

if f_ledger:
    df = load_data(f_ledger)
    today = datetime.now()
    df_filtered = df[df['LedgerName'].str.strip().isin([n.strip() for n in target_names])].copy()

    if not df_filtered.empty:
        # --- حساب التحليلات العلوية ---
        
        # 1. الديون المتأخرة
        global_overdue_amt = 0
        global_overdue_count = 0
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name]
            balance = c_data['Dr'].sum() - c_data['Cr'].sum()
            if balance <= 1: continue
            
            temp_bal = balance
            c_overdue = 0
            for _, row in c_data.sort_values('Date', ascending=False)[c_data['Dr'] > 0].iterrows():
                if temp_bal <= 0: break
                days = (today - row['Date']).days
                amt = min(row['Dr'], temp_bal)
                if days > 60: c_overdue += amt
                temp_bal -= amt
            if c_overdue > 1:
                global_overdue_amt += c_overdue
                global_overdue_count += 1

        # 2. تحصيل آخر 4 أسابيع (أحد - سبت)
        offset_to_sat = (today.weekday() + 2) % 7
        last_sat = today - timedelta(days=offset_to_sat)
        weeks_kpi = []
        for i in range(4):
            end_date = last_sat - timedelta(weeks=i)
            start_date = end_date - timedelta(days=6)
            mask = (df_filtered['Date'].dt.date >= start_date.date()) & (df_filtered['Date'].dt.date <= end_date.date())
            weeks_kpi.append({"val": df_filtered[mask]['Cr'].sum(), "range": f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"})
        weeks_kpi.reverse()

        # 3. تحصيل آخر 3 أشهر (من بداية الشهر لنهايته)
        months_kpi = []
        for i in range(3):
            # تحديد الشهر
            first_day_of_curr_month = today.replace(day=1)
            target_date = first_day_of_curr_month - timedelta(days=i*30) # تقريبي للوصول للشهر
            m_month = target_date.month
            m_year = target_date.year
            m_name = target_date.strftime('%B')
            
            mask = (df_filtered['Date'].dt.month == m_month) & (df_filtered['Date'].dt.year == m_year)
            months_kpi.append({"name": m_name, "val": df_filtered[mask]['Cr'].sum()})

        # 4. المتوسطات
        days_active = max((today - df_filtered['Date'].min()).days, 1)
        avg_weekly = (df_filtered['Cr'].sum() / days_active) * 7
        avg_monthly = (df_filtered['Cr'].sum() / days_active) * 30

        # --- عرض بطاقات KPI (في 3 صفوف) ---
        st.markdown("### 📊 لوحة مراقبة التحصيل")
        
        # الصف الأول: المتأخرات والمتوسطات
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">المستحق (>60 يوم)</div><div class="kpi-value" style="color:red;">{global_overdue_amt:,.0f}</div><div class="kpi-sub">{global_overdue_count} عملاء متأخرين</div></div>', unsafe_allow_html=True)
        with r1c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">متوسط التحصيل الأسبوعي</div><div class="kpi-value">{avg_weekly:,.0f}</div></div>', unsafe_allow_html=True)
        with r1c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">متوسط التحصيل الشهري</div><div class="kpi-value">{avg_monthly:,.0f}</div></div>', unsafe_allow_html=True)

        # الصف الثاني: تحصيل الشهور (لآخر 3 أشهر)
        st.markdown("---")
        st.caption("💰 إجمالي تحصيل الشهور")
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">تحصيل الشهر الحالي ({months_kpi[0]["name"]})</div><div class="kpi-value">{months_kpi[0]["val"]:,.0f}</div></div>', unsafe_allow_html=True)
        with r2c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">تحصيل الشهر السابق ({months_kpi[1]["name"]})</div><div class="kpi-value">{months_kpi[1]["val"]:,.0f}</div></div>', unsafe_allow_html=True)
        with r2c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">تحصيل ما قبل السابق ({months_kpi[2]["name"]})</div><div class="kpi-value">{months_kpi[2]["val"]:,.0f}</div></div>', unsafe_allow_html=True)

        # الصف الثالث: تحصيل الأسابيع (لآخر 4 أسابيع)
        st.markdown("---")
        st.caption("📅 تحصيل الأسابيع (أحد - سبت)")
        r3c1, r3c2, r3c3, r3c4 = st.columns(4)
        for i, week in enumerate(weeks_kpi):
            with [r3c1, r3c2, r3c3, r3c4][i]:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">الأسبوع {i+1}</div><div class="kpi-value">{week["val"]:,.0f}</div><div class="kpi-sub">{week["range"]}</div></div>', unsafe_allow_html=True)

        st.divider()

        # --- عرض بطاقات العملاء التفصيلية ---
        st.title("📇 سجل متابعة العملاء")
        index = 1
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name].sort_values('Date', ascending=False)
            if c_data.empty: continue
            total_balance = c_data['Dr'].sum() - c_data['Cr'].sum()
            if total_balance <= 1: continue

            periods = [{"key": "P0", "label": "0-30 يوم", "min": 0, "max": 30}, {"key": "P30", "label": "31-60 يوم", "min": 31, "max": 60}, {"key": "P60", "label": "61-90 يوم", "min": 61, "max": 90}, {"key": "P90", "label": "91-120 يوم", "min": 91, "max": 120}, {"key": "P120", "label": "+120 يوم", "min": 121, "max": 9999}]
            out_vals = {p["key"]: 0 for p in periods}
            temp_bal = total_balance
            for _, row in c_data[c_data['Dr'] > 0].iterrows():
                if temp_bal <= 0: break
                days = (today - row['Date']).days
                amt = min(row['Dr'], temp_bal)
                for p in periods:
                    if days >= p["min"] and days <= p["max"]:
                        out_vals[p["key"]] += amt
                        break
                temp_bal -= amt

            overdue_60_card = out_vals["P60"] + out_vals["P90"] + out_vals["P120"]

            st.markdown(f"""
            <div class="main-card">
                <div class="customer-header">
                    <span>#{index} - {name}</span>
                    <span>إجمالي المديونية: {total_balance:,.2f} ر.س</span>
                </div>
                <div class="urgent-box">
                    <small>المستحق سداده (>60 يوم)</small><br><b style="color:#d32f2f; font-size:24px;">{overdue_60_card:,.2f}</b>
                </div>
                <table class="aging-table">
                    <tr><th>البيان / الفترة</th>{" ".join([f"<th>{p['label']}</th>" for p in periods])}</tr>
                    <tr><td style="background:#f8f9fa; font-weight:bold;">المديونية (Aging)</td>{" ".join([f"<td class='val-outstanding'>{out_vals[p['key']]:,.2f}</td>" for p in periods])}</tr>
                    <tr><td style="background:#f8f9fa;">المشتريات (قيمة)</td>{" ".join([f"<td>{c_data[((today-c_data['Date']).dt.days>=p['min'])&((today-c_data['Date']).dt.days<=p['max'])]['Dr'].sum():,.0f}</td>" for p in periods])}</tr>
                    <tr><td style="background:#f8f9fa;">الفواتير (عدد)</td>{" ".join([f"<td>{len(c_data[((today-c_data['Date']).dt.days>=p['min'])&((today-c_data['Date']).dt.days<=p['max'])&(c_data['Dr']>0)])}</td>" for p in periods])}</tr>
                    <tr><td style="background:#f8f9fa;">السداد (قيمة)</td>{" ".join([f"<td>{c_data[((today-c_data['Date']).dt.days>=p['min'])&((today-c_data['Date']).dt.days<=p['max'])]['Cr'].sum():,.0f}</td>" for p in periods])}</tr>
                    <tr><td style="background:#f8f9fa;">الدفعات (عدد)</td>{" ".join([f"<td>{len(c_data[((today-c_data['Date']).dt.days>=p['min'])&((today-c_data['Date']).dt.days<=p['max'])&(c_data['Cr']>0)])}</td>" for p in periods])}</tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            index += 1
else:
    st.info("💡 ارفع ملف LedgerBook.xml لعرض لوحة القيادة الكاملة.")
