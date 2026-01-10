import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="تحصيل شان - الإخراج النهائي", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    
    /* تنسيق كروت الـ KPI العلوية */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-title { font-size: 12px; color: #666; margin-bottom: 5px; font-weight: bold; }
    .kpi-value { font-size: 19px; font-weight: bold; color: #034275; }
    .kpi-sub { font-size: 11px; color: #888; margin-top: 5px; }
    
    /* تنسيق الجدول الداخلي */
    .aging-table { width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ddd; }
    .aging-table th, .aging-table td { 
        border: 1px solid #eee; padding: 10px; text-align: center; font-size: 13px;
    }
    .aging-table th { background-color: #f8f9fa; color: #034275; font-weight: bold; }
    .val-outstanding { font-weight: bold; color: #d32f2f; font-size: 14px; }
    
    /* صندوق الحالة (أخضر/أحمر) */
    .status-box {
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 18px;
        border: 1px solid;
    }
    .status-red { background-color: #fdf2f2; color: #c0392b; border-color: #f5c6cb; }
    .status-green { background-color: #f0f9f4; color: #27ae60; border-color: #c3e6cb; }
    
    /* تعديل شكل الاكسباندر */
    .streamlit-expanderHeader {
        font-family: 'Tajawal', sans-serif;
        font-weight: bold;
        font-size: 16px;
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. دالة القراءة الذكية (فلترة صارمة للمرتجعات) ---
def load_data(file):
    if file is None: return None
    file.seek(0)
    tree = ET.parse(file)
    data = [{child.tag: child.text for child in row} for row in tree.getroot()]
    df = pd.DataFrame(data)
    
    df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
    df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
    df['Date'] = pd.to_datetime(pd.to_numeric(df['TransDateValue'], errors='coerce'), unit='D', origin='1899-12-30')
    
    def is_return_transaction(row):
        text_content = (str(row.get('VoucherName', '')) + " " + str(row.get('AcLedger', '')) + " " + str(row.get('Narration', ''))).lower()
        return any(x in text_content for x in ['return', 'مرتجع', 'مردود', 'credit note', 'تسوية', 'تعديل'])

    df['IsReturn'] = df.apply(is_return_transaction, axis=1)
    return df

# --- 3. القائمة المعتمدة ---
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
        # --- (أ) قسم الكروت العلوية (KPIs) - الكاش الصافي ---
        df_cash_collection = df_filtered[(df_filtered['Cr'] > 0) & (df_filtered['IsReturn'] == False)]
        
        global_overdue_amt = 0
        global_overdue_count = 0
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name]
            bal = c_data['Dr'].sum() - c_data['Cr'].sum()
            if bal <= 1: continue
            temp_bal = bal
            c_overdue = 0
            for _, r in c_data.sort_values('Date', ascending=False)[c_data['Dr'] > 0].iterrows():
                if temp_bal <= 0: break
                days = (today - r['Date']).days
                amt = min(r['Dr'], temp_bal)
                if days > 60: c_overdue += amt
                temp_bal -= amt
            if c_overdue > 1:
                global_overdue_amt += c_overdue
                global_overdue_count += 1

        # تحصيل الأسابيع
        offset_to_sat = (today.weekday() + 2) % 7
        last_sat = today - timedelta(days=offset_to_sat)
        weeks_kpi = []
        for i in range(4):
            end_date = last_sat - timedelta(weeks=i)
            start_date = end_date - timedelta(days=6)
            mask = (df_cash_collection['Date'].dt.date >= start_date.date()) & (df_cash_collection['Date'].dt.date <= end_date.date())
            weeks_kpi.append({"val": df_cash_collection[mask]['Cr'].sum(), "range": f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"})
        weeks_kpi.reverse()

        # تحصيل الشهور
        months_kpi = []
        for i in range(3):
            d = today.replace(day=1) - timedelta(days=i*30)
            mask = (df_cash_collection['Date'].dt.month == d.month) & (df_cash_collection['Date'].dt.year == d.year)
            months_kpi.append({"name": d.strftime('%B'), "val": df_cash_collection[mask]['Cr'].sum()})

        # المتوسطات
        days_active = max((today - df_filtered['Date'].min()).days, 1)
        total_cash_only = df_cash_collection['Cr'].sum()
        avg_weekly = (total_cash_only / days_active) * 7
        avg_monthly = (total_cash_only / days_active) * 30

        # --- عرض اللوحة العلوية ---
        st.markdown("### 📊 مركز قيادة التحصيل (صافي النقدية)")
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">المستحق سداده (>60 يوم)</div><div class="kpi-value" style="color:#c0392b;">{global_overdue_amt:,.0f}</div><div class="kpi-sub">{global_overdue_count} عملاء متأخرين</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">متوسط التحصيل الأسبوعي</div><div class="kpi-value">{avg_weekly:,.0f}</div><div class="kpi-sub">صافي بدون مرتجع</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">متوسط التحصيل الشهري</div><div class="kpi-value">{avg_monthly:,.0f}</div><div class="kpi-sub">صافي بدون مرتجع</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.caption("📅 أداء الشهور والأسابيع")
        
        m1, m2, m3, w1, w2, w3, w4 = st.columns(7)
        with m1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{months_kpi[0]["name"]}</div><div class="kpi-value" style="font-size:16px">{months_kpi[0]["val"]:,.0f}</div></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{months_kpi[1]["name"]}</div><div class="kpi-value" style="font-size:16px">{months_kpi[1]["val"]:,.0f}</div></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{months_kpi[2]["name"]}</div><div class="kpi-value" style="font-size:16px">{months_kpi[2]["val"]:,.0f}</div></div>', unsafe_allow_html=True)
        
        for i, wk in enumerate(weeks_kpi):
            with [w1, w2, w3, w4][i]:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">W{i+1}</div><div class="kpi-value" style="font-size:16px">{wk["val"]:,.0f}</div><div class="kpi-sub" style="font-size:9px">{wk["range"]}</div></div>', unsafe_allow_html=True)

        st.divider()

        # --- (ب) بطاقات العملاء (Expandable) ---
        st.title("📇 قائمة العملاء والتحليل")
        
        index = 1
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name].sort_values('Date', ascending=False)
            if c_data.empty: continue
            
            total_balance = c_data['Dr'].sum() - c_data['Cr'].sum()
            if total_balance <= 1: continue

            periods = [
                {"key": "P0", "label": "0-30 يوم", "min": 0, "max": 30},
                {"key": "P30", "label": "31-60 يوم", "min": 31, "max": 60},
                {"key": "P60", "label": "61-90 يوم", "min": 61, "max": 90},
                {"key": "P90", "label": "91-120 يوم", "min": 91, "max": 120},
                {"key": "P120", "label": "+120 يوم", "min": 121, "max": 9999}
            ]
            
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
            
            # تحديد لون وحالة العميل
            if overdue_60_card > 1:
                status_icon = "🔴"
                status_class = "status-red"
                status_msg = f"يوجد مبالغ مستحقة السداد: {overdue_60_card:,.2f}"
            else:
                status_icon = "🟢"
                status_class = "status-green"
                status_msg = "✅ حساب منتظم (لا يوجد متأخرات > 60 يوم)"

            # تعبئة الجدول
            table_rows = []
            for p in periods:
                p_mask = ( (today - c_data['Date']).dt.days >= p["min"] ) & ( (today - c_data['Date']).dt.days <= p["max"] )
                p_data = c_data[p_mask]
                real_pay_data = p_data[(p_data['Cr'] > 0) & (p_data['IsReturn'] == False)]
                
                table_rows.append({
                    "outstanding": out_vals[p["key"]],
                    "purch_val": p_data['Dr'].sum(),
                    "purch_count": len(p_data[p_data['Dr'] > 0]),
                    "pay_val": real_pay_data['Cr'].sum(),
                    "pay_count": len(real_pay_data)
                })

            # --- عرض العميل (Expander) ---
            with st.expander(f"{status_icon} #{index} - {name} | الرصيد: {total_balance:,.2f} ر.س"):
                st.markdown(f"""
                <div class="status-box {status_class}">
                    {status_msg}
                </div>
                <table class="aging-table">
                    <tr>
                        <th style="width:180px;">البيان / الفترة</th>
                        {" ".join([f"<th>{p['label']}</th>" for p in periods])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa; font-weight:bold;">المديونية (Aging)</td>
                        {" ".join([f"<td class='val-outstanding'>{r['outstanding']:,.2f}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">المشتريات (قيمة)</td>
                        {" ".join([f"<td>{r['purch_val']:,.0f}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">الفواتير (عدد)</td>
                        {" ".join([f"<td>{r['purch_count']}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">السداد النقدي (قيمة)</td>
                        {" ".join([f"<td style='color:#27ae60;'>{r['pay_val']:,.0f}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">الدفعات (عدد)</td>
                        {" ".join([f"<td>{r['pay_count']}</td>" for r in table_rows])}
                    </tr>
                </table>
                """, unsafe_allow_html=True)
            index += 1
else:
    st.info("💡 ارفع ملف LedgerBook.xml لعرض لوحة القيادة.")
