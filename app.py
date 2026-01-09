import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="تحصيل شان الحديثة", layout="wide")

st.title("💸 مديونية العملاء - مطابقة تامة")
st.markdown("### المستهدف: **218,789.96** ر.س (40 عميل)")

# --- 2. دالة القراءة المباشرة (بدون تعقيد) ---
def load_data(file):
    if file is None: return None
    file.seek(0)
    try:
        # قراءة أولية للملف بالكامل
        tree = ET.parse(file)
        root = tree.getroot()
        data = []
        for row in root:
            # استخراج كافة الحقول المتاحة في السطر
            row_dict = {child.tag: child.text for child in row}
            data.append(row_dict)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"فشل في قراءة الملف: {e}")
        return None

# --- 3. القائمة الجانبية ---
with st.sidebar:
    st.header("📂 استيراد البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'], key="ledger_v5")

# --- 4. المعالجة والتحليل ---
if f_ledger:
    df_raw = load_data(f_ledger)
    
    if df_raw is not None:
        # تحويل المبالغ فوراً
        df_raw['Dr'] = pd.to_numeric(df_raw['Dr'], errors='coerce').fillna(0)
        df_raw['Cr'] = pd.to_numeric(df_raw['Cr'], errors='coerce').fillna(0)
        
        # خيار الفحص (عرض كل شيء للتأكد أن البرنامج يقرأ)
        show_all = st.checkbox("🔍 عرض كافة الحسابات المكتشفة في الملف (للتأكد من القراءة)")
        
        # التجميع الأساسي لكل الحسابات
        summary_all = df_raw.groupby('LedgerName').agg({
            'Dr': 'sum', 
            'Cr': 'sum',
            'AcLedger': 'first'
        }).reset_index()
        summary_all['Balance'] = summary_all['Dr'] - summary_all['Cr']

        if show_all:
            st.subheader("📋 كافة الحسابات الموجودة في الملف")
            st.dataframe(summary_all[['LedgerName', 'AcLedger', 'Balance']], use_container_width=True)

        st.divider()

        # --- فلترة الـ 40 عميل المستهدفين ---
        # 1. استبعاد الحسابات البنكية والنقدية
        exclude_list = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة"]
        
        # 2. تطبيق فلترة الأكواد 113 و 221
        final_debtors = summary_all[
            (summary_all['AcLedger'].astype(str).str.startswith(('113', '221'))) & 
            (~summary_all['LedgerName'].str.contains('|'.join(exclude_list), na=False)) &
            (summary_all['Balance'] > 0.01)
        ].sort_values('Balance', ascending=False)

        # --- 5. عرض النتائج النهائية للمطابقة ---
        current_total = final_debtors['Balance'].sum()
        count_found = len(final_debtors)
        
        c1, c2 = st.columns(2)
        c1.metric("إجمالي مديونية العملاء", f"{current_total:,.2f} ر.س")
        c2.metric("عدد العملاء", f"{count_found}")
        
        target = 218789.96
        if abs(current_total - target) < 1:
            st.success(f"✅ مبروك! تم التطابق مع البرنامج: {target:,.2f} ر.س")
        else:
            st.warning(f"الفرق الحالي عن البرنامج: {target - current_total:,.2f} ر.س")

        st.subheader("📋 القائمة النهائية (المطابقة للبرنامج)")
        st.dataframe(
            final_debtors[['LedgerName', 'Balance']], 
            column_config={"Balance": st.column_config.NumberColumn("الرصيد", format="%.2f")},
            use_container_width=True, 
            height=600
        )
else:
    st.info("💡 الرجاء رفع ملف LedgerBook.xml للبدء.")
