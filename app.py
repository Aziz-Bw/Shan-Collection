import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتصميم (نفس التصميم الاحترافي السابق) ---
st.set_page_config(page_title="تحصيل شان - مركز القيادة", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    
    /* تنسيق كروت الـ KPI العلوية */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-title { font-size: 13px; color: #666; margin-bottom: 5px; font-weight: bold; }
    .kpi-value { font-size: 20px; font-weight: bold; color: #034275; }
    .kpi-sub { font-size: 11px; color: #888; margin-top: 5px; }
    
    /* تنسيق بطاقة العميل التفصيلية */
    .main-card {
        border: 2px solid #034275;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        background-color: #ffffff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
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
        font-weight: bold;
    }
    .aging-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
    .aging-table th, .aging-table td { 
        border: 1px solid #eee; padding: 10px; text-align: center; font-size: 13px;
    }
    .aging-table th { background-color: #f1f3f5; color: #034275; }
    .val-outstanding { font-weight: bold; color: #d32f2f; font-size: 15px; }
    .val-activity { color: #555; font-size: 12px; }
    .urgent-box { 
        background:#fdf2f2; border: 1px solid #f5c6cb; 
        padding:15px; border-radius:8px; text-align:center; margin-bottom:20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. دالة القراءة الذكية (تستخرج نوع العملية لاستبعاد المرتجعات) ---
def load_data(file):
    if file is None: return None
    file.seek(0)
    tree = ET.parse(file)
    data = [{child.tag: child.text for child in row} for row in tree.getroot()]
    df = pd.DataFrame(data)
    
    # تحويل الأرقام والتوايخ
    df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
    df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
    df['Date'] = pd.to_datetime(pd.to_numeric(df['TransDateValue'], errors='coerce'), unit='D', origin='1899-12-30')
    
    # --- الفلتر الذكي لاستبعاد المرتجعات ---
    # نبحث في 'VoucherName' أو 'AcLedger' عن أي إشارة للمردودات
    # عادة المرتجعات تحتوي على كلمة "Return" أو "مردود" أو "Credit Note"
    # سنقوم بإنشاء عمود 'IsReturn' لتمييز هذه العمليات
    
    def check_return(row):
        v_name = str(row.get('VoucherName', '')).lower()
        ac_name = str(row.get('AcLedger', '')).lower()
        if 'return' in v_name or 'مردود' in v_name or 'مرتجع' in v_name:
            return True
        return False

    df['IsReturn'] = df.apply(check_return, axis=1)
    
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

# --- 4. واجهة المستخدم والمعالجة ---
with st.sidebar:
    st.header("📂 إدارة البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'])

if f_ledger:
    df = load_data(f_ledger)
    today = datetime.now()
    df_filtered = df[df['LedgerName'].str.strip().isin([n.strip() for n in target_names])].copy()

    if not df_filtered.empty:
        # ---------------------------------------------------------
        # القسم الأول: حسابات لوحة القيادة (KPIs) - نستبعد المرتجعات هنا
        # ---------------------------------------------------------
        
        # نستخدم داتا فريم خاصة للتحصيل (تستبعد المرتجعات تماماً)
        # التحصيل الحقيقي = عمليات دائنة (Cr > 0) وليست مرتجعات (IsReturn == False)
        df_collections_only = df_filtered[(df_filtered['Cr'] > 0) & (df_filtered['IsReturn'] == False)]
        
        # 1. المستحق سداده (>60 يوم) - يحسب من الرصيد الصافي (يشمل المرتجعات لأنها تخفض الدين)
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

        # 2. تحصيل آخر 4 أسابيع (نستخدم df_collections_only)
        offset_to_sat = (today.weekday() + 2) % 7
        last_sat = today - timedelta(days=offset_to_sat)
        weeks_kpi = []
        for i in range(4):
            end_date = last_sat - timedelta(weeks=i)
            start_date = end_date - timedelta(days=6)
            mask = (df_collections_only['Date'].dt.date >= start_date.date()) & (df_collections_only['Date'].dt.date <= end_date.date())
            val = df_collections_only[mask]['Cr'].sum()
            weeks_kpi.append({"val": val, "range": f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"})
        weeks_kpi.reverse()

        # 3. تحصيل الشهور (نستخدم df_collections_only)
        months_kpi = []
        for i in range(3):
            d = today.replace(day=1) - timedelta(days=i*30)
            mask = (df_collections_only['Date'].dt.month == d.month) & (df_collections_only['Date'].dt.year == d.year)
            months_kpi.append({"name": d.strftime('%B'), "val": df_collections_only[mask]['Cr'].sum()})

        # 4. المتوسطات (نستخدم df_collections_only)
        days_active = max((today - df_filtered['Date'].min()).days, 1)
        total_real_collection = df_collections_only['Cr'].sum()
        avg_weekly = (total_real_collection / days_active) * 7
        avg_monthly = (total_real_collection / days_active) * 30

        # --- عرض اللوحة (نفس التصميم السابق) ---
        st.markdown("### 📊 مركز قيادة التحصيل (صافي بدون مرتجعات)")
        
        # الصف 1
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">المستحق سداده (>60 يوم)</div><div class="kpi-value" style="color:#c0392b;">{global_overdue_amt:,.0f}</div><div class="kpi-sub">{global_overdue_count} عملاء متأخرين</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">متوسط التحصيل الأسبوعي</div><div class="kpi-value">{avg_weekly:,.0f}</div><div class="kpi-sub">صافي كاش</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">متوسط التحصيل الشهري</div><div class="kpi-value">{avg_monthly:,.0f}</div><div class="kpi-sub">صافي كاش</div></div>', unsafe_allow_html=True)

        # الصف 2 (الشهور)
        st.markdown("---")
        st.caption("📅 أداء الشهور (صافي التحصيل)")
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{months_kpi[0]["name"]} (الحالي)</div><div class="kpi-value">{months_kpi[0]["val"]:,.0f}</div></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{months_kpi[1]["name"]} (السابق)</div><div class="kpi-value">{months_kpi[1]["val"]:,.0f}</div></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{months_kpi[2]["name"]}</div><div class="kpi-value">{months_kpi[2]["val"]:,.0f}</div></div>', unsafe_allow_html=True)

        # الصف 3 (الأسابيع)
        st.markdown("---")
        st.caption("📅 أداء الأسابيع (من الأحد إلى السبت)")
        w1, w2, w3, w4 = st.columns(4)
        for i, wk in enumerate(weeks_kpi):
            with [w1, w2, w3, w4][i]:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">الأسبوع {i+1}</div><div class="kpi-value">{wk["val"]:,.0f}</div><div class="kpi-sub">{wk["range"]}</div></div>', unsafe_allow_html=True)

        st.divider()

        # ---------------------------------------------------------
        # القسم الثاني: بطاقات العملاء التفصيلية
        # ---------------------------------------------------------
        st.title("📇 بطاقات متابعة العملاء التفصيلية")
        
        index = 1
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name].sort_values('Date', ascending=False)
            if c_data.empty: continue
            
            # الرصيد يحسب شامل المرتجعات لأنها تخفض الدين
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
            
            # تجميع بيانات الجدول (مع استبعاد المرتجعات من صفوف السداد)
            table_rows = []
            for p in periods:
                p_mask = ( (today - c_data['Date']).dt.days >= p["min"] ) & ( (today - c_data['Date']).dt.days <= p["max"] )
                p_data = c_data[p_mask]
                
                # هنا نستبعد المرتجعات من حسابات "السداد"
                real_pay_data = p_data[(p_data['Cr'] > 0) & (p_data['IsReturn'] == False)]
                
                table_rows.append({
                    "outstanding": out_vals[p["key"]],
                    "purch_val": p_data['Dr'].sum(),
                    "purch_count": len(p_data[p_data['Dr'] > 0]),
                    "pay_val": real_pay_data['Cr'].sum(), # سداد حقيقي فقط
                    "pay_count": len(real_pay_data)       # عدد دفعات حقيقية
                })

            st.markdown(f"""
            <div class="main-card">
                <div class="customer-header">
                    <span>#{index} - {name}</span>
                    <span>إجمالي المديونية: {total_balance:,.2f} ر.س</span>
                </div>
                <div class="urgent-box">
                    <small style="color:#666;">المستحق سداده (أقدم من 60 يوم)</small><br>
                    <b style="color:#d32f2f; font-size:24px;">{overdue_60_card:,.2f}</b>
                </div>
                <table class="aging-table">
                    <tr>
                        <th style="width:200px;">البيان / الفترة</th>
                        {" ".join([f"<th>{p['label']}</th>" for p in periods])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa; font-weight:bold;">المديونية المتبقية (Aging)</td>
                        {" ".join([f"<td class='val-outstanding'>{r['outstanding']:,.2f}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">إجمالي المشتريات (قيمة)</td>
                        {" ".join([f"<td>{r['purch_val']:,.0f}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">عدد الفواتير (شراء)</td>
                        {" ".join([f"<td>{r['purch_count']}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">صافي السداد (بدون مرتجع)</td>
                        {" ".join([f"<td style='color:#27ae60; font-weight:bold;'>{r['pay_val']:,.0f}</td>" for r in table_rows])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">عدد الدفعات النقدية</td>
                        {" ".join([f"<td>{r['pay_count']}</td>" for r in table_rows])}
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            index += 1
else:
    st.info("💡 ارفع ملف LedgerBook.xml لعرض لوحة القيادة.")
