import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والتنسيق البصري ---
st.set_page_config(page_title="تحصيل شان - التحليل الموحد", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .main-card {
        border: 2px solid #034275;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
    .val-activity { color: #555; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 2. دالة القراءة المضمونة ---
def load_data(file):
    if file is None: return None
    file.seek(0)
    tree = ET.parse(file)
    data = [{child.tag: child.text for child in row} for row in tree.getroot()]
    df = pd.DataFrame(data)
    df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
    df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
    # تحويل تاريخ البرنامج المعتمد
    df['Date'] = pd.to_datetime(pd.to_numeric(df['TransDateValue'], errors='coerce'), unit='D', origin='1899-12-30')
    return df

# --- 3. قائمة الأسماء المعتمدة من ميزان المراجعة ---
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
        st.title("📇 سجل متابعة التحصيل (تحليل الفترات الموحد)")
        
        index = 1
        for name in target_names:
            c_data = df_filtered[df_filtered['LedgerName'] == name].sort_values('Date', ascending=False)
            if c_data.empty: continue
            
            total_balance = c_data['Dr'].sum() - c_data['Cr'].sum()
            if total_balance <= 1: continue

            # تعريف الفترات الزمنية الموحدة
            periods = [
                {"label": "0-30 يوم", "min": 0, "max": 30},
                {"label": "31-60 يوم", "min": 31, "max": 60},
                {"label": "61-90 يوم", "min": 61, "max": 90},
                {"label": "91-120 يوم", "min": 91, "max": 120},
                {"label": "+120 يوم", "min": 121, "max": 9999}
            ]
            
            aging_results = []
            temp_bal = total_balance
            
            # 1. حساب المديونية المتبقية (Outstanding) بناءً على الفواتير
            out_vals = {p["label"]: 0 for p in periods}
            for _, row in c_data[c_data['Dr'] > 0].iterrows():
                if temp_bal <= 0: break
                days = (today - row['Date']).days
                amt = min(row['Dr'], temp_bal)
                for p in periods:
                    if days >= p["min"] and days <= p["max"]:
                        out_vals[p["label"]] += amt
                        break
                temp_bal -= amt

            # 2. حساب حركة المشتريات والسداد الفعلية داخل كل فترة
            for p in periods:
                mask = ( (today - c_data['Date']).dt.days >= p["min"] ) & ( (today - c_data['Date']).dt.days <= p["max"] )
                p_data = c_data[mask]
                aging_results.append({
                    "period": p["label"],
                    "outstanding": out_vals.get(p["label"], 0),
                    "purchases": p_data['Dr'].sum(),
                    "payments": p_data['Cr'].sum()
                })

            # المبلغ المستحق سداده (أكثر من 60 يوم)
            overdue_60 = out_vals["61-90"] + out_vals["91-120"] + out_vals["+120"]

            # عرض بطاقة العميل الموحدة
            st.markdown(f"""
            <div class="main-card">
                <div class="customer-header">
                    <span style="font-size: 18px; font-weight: bold;">#{index} - {name}</span>
                    <span style="font-size: 15px;">إجمالي المديونية: {total_balance:,.2f} ر.س</span>
                </div>
                <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                    <div style="flex:1; background:#f8f9fa; padding:10px; border-radius:8px; border:1px solid #ddd; text-align:center;">
                        <small>المبلغ المستحق (>60 يوم)</small><br><b style="color:#d32f2f; font-size:18px;">{overdue_60:,.2f}</b>
                    </div>
                </div>
                <table class="aging-table">
                    <tr>
                        <th style="width:200px;">البيان / الفترة</th>
                        {" ".join([f"<th>{r['period']}</th>" for r in aging_results])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa; font-weight:bold;">المديونية المتبقية (Aging)</td>
                        {" ".join([f"<td class='val-outstanding'>{r['outstanding']:,.2f}</td>" for r in aging_results])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">إجمالي المشتريات (خلال الفترة)</td>
                        {" ".join([f"<td class='val-activity'>{r['purchases']:,.0f}</td>" for r in aging_results])}
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;">إجمالي المسدد (خلال الفترة)</td>
                        {" ".join([f"<td class='val-activity'>{r['payments']:,.0f}</td>" for r in aging_results])}
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            index += 1
    else:
        st.warning("يرجى رفع الملف لعرض البيانات.")
else:
    st.info("💡 ارفع ملف LedgerBook.xml لعرض تقرير التحصيل الموحد.")
