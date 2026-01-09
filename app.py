import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="تحصيل شان الحديثة", layout="wide")

st.title("💸 مديونية العملاء - مطابقة ميزان المراجعة")
st.markdown(f"### المستهدف: **218,789.96** ر.س")

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
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'], key="ledger_v_final")

# --- 4. المعالجة والمطابقة ---
if f_ledger:
    df_raw = load_data(f_ledger)
    if df_raw is not None:
        try:
            # تحويل المبالغ
            df_raw['Dr'] = pd.to_numeric(df_raw['Dr'], errors='coerce').fillna(0)
            df_raw['Cr'] = pd.to_numeric(df_raw['Cr'], errors='coerce').fillna(0)
            
            # التجميع حسب العميل
            summary = df_raw.groupby('LedgerName').agg({
                'Dr': 'sum', 
                'Cr': 'sum',
                'AcLedger': 'first'
            }).reset_index()
            
            summary['Balance'] = summary['Dr'] - summary['Cr']

            # --- الفلترة بناءً على ميزان المراجعة ---
            # 1. الحسابات التي تبدأ بـ 1131 (العملاء) أو 221 (الموردين ذوي الأرصدة المدينة)
            # 2. استبعاد البنوك والصناديق الرئيسية
            exclude_names = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة"]
            
            final_debtors = summary[
                (summary['AcLedger'].astype(str).str.startswith(('1131', '221'))) & 
                (~summary['LedgerName'].str.contains('|'.join(exclude_names), na=False)) &
                (summary['Balance'] > 0.01)
            ].sort_values('Balance', ascending=False)

            # --- 5. عرض النتائج ---
            total_val = final_debtors['Balance'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("إجمالي المديونية (مطابق للميزان)", f"{total_val:,.2f} ر.س")
            c2.metric("عدد الحسابات المدينة", f"{len(final_debtors)}")
            
            if abs(total_val - 218789.96) < 1:
                st.success("✅ تم التطابق التام مع تقرير البرنامج وميزان المراجعة!")
            else:
                st.warning(f"الفرق الحالي: {218789.96 - total_val:,.2f} ر.س")

            st.subheader("📋 كشف الأرصدة (العملاء والموردين المدينين)")
            st.dataframe(
                final_debtors[['LedgerName', 'Balance']], 
                column_config={"Balance": st.column_config.NumberColumn("الرصيد المتبقي", format="%.2f")},
                use_container_width=True, 
                height=600
            )
            
        except Exception as e:
            st.error(f"خطأ أثناء المعالجة: {e}")
else:
    st.info("💡 ارفع ملف LedgerBook.xml للبدء.")
