import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="تحصيل شان الحديثة", layout="wide")

st.title("💸 مديونية العملاء - مطابقة تامة")
st.markdown("### المستهدف: **218,789.96** ر.س (40 عميل)")

# --- 2. دالة القراءة المباشرة ---
def load_data(file):
    if file is None: return None
    file.seek(0)
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        data = []
        for row in root:
            data.append({child.tag: child.text for child in row})
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"فشل القراءة: {e}")
        return None

# --- 3. القائمة الجانبية ---
with st.sidebar:
    st.header("📂 استيراد البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'], key="ledger_final")

# --- 4. المعالجة ---
if f_ledger:
    df_raw = load_data(f_ledger)
    if df_raw is not None:
        # تحويل المبالغ
        df_raw['Dr'] = pd.to_numeric(df_raw['Dr'], errors='coerce').fillna(0)
        df_raw['Cr'] = pd.to_numeric(df_raw['Cr'], errors='coerce').fillna(0)
        
        # --- المنطق الجديد بناءً على طلبك ---
        # 1. نحدد العملاء من خلال "نوع العملية" (نقدي أو آجل)
        # 2. نستبعد البنوك والعهد يدوياً لضمان النظافة
        exclude_list = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة", "مصاريف", "مشتريات"]
        
        # التجميع حسب الاسم
        summary = df_raw.groupby('LedgerName').agg({
            'Dr': 'sum', 
            'Cr': 'sum',
            'AcLedger': 'first' # للحفاظ على التصنيف للفحص
        }).reset_index()
        
        summary['Balance'] = summary['Dr'] - summary['Cr']

        # الفلترة: أي حساب عليه رصيد مدين وليس من قائمة الاستبعاد
        # مع إضافة "خالد المحمادي" وأي عميل يبدأ بـ 113 أو 221
        final_debtors = summary[
            (
                (summary['AcLedger'].astype(str).str.contains('مبيعات|اجله|نقدية', na=False)) | 
                (summary['AcLedger'].astype(str).str.startswith(('113', '221')))
            ) & 
            (~summary['LedgerName'].str.contains('|'.join(exclude_list), na=False)) &
            (summary['Balance'] > 0.01)
        ].sort_values('Balance', ascending=False)

        # --- 5. عرض النتائج ---
        current_total = final_debtors['Balance'].sum()
        count_found = len(final_debtors)
        
        c1, c2 = st.columns(2)
        c1.metric("إجمالي مديونية العملاء", f"{current_total:,.2f} ر.س")
        c2.metric("عدد العملاء", f"{count_found}")
        
        target = 218789.96
        if abs(current_total - target) < 1:
            st.success(f"✅ تم التطابق التام: {target:,.2f} ر.س")
        else:
            st.warning(f"الفرق: {target - current_total:,.2f} ر.س (تأكد من شمول خالد المحمادي)")

        st.subheader("📋 القائمة المطابقة للبرنامج")
        st.dataframe(final_debtors[['LedgerName', 'Balance']], use_container_width=True)
else:
    st.info("💡 ارفع ملف LedgerBook.xml للبدء.")
