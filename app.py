import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="تحصيل شان الحديثة", layout="wide")

st.title("💸 مديونية العملاء - مطابقة ميزان المراجعة")
st.markdown("### المستهدف النهائي: **218,789.96** ر.س")

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
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'], key="ledger_v_final_verified")

# --- 4. المعالجة والمطابقة المحاسبية ---
if f_ledger:
    df_raw = load_data(f_ledger)
    if df_raw is not None:
        try:
            # تحويل المبالغ
            df_raw['Dr'] = pd.to_numeric(df_raw['Dr'], errors='coerce').fillna(0)
            df_raw['Cr'] = pd.to_numeric(df_raw['Cr'], errors='coerce').fillna(0)
            
            # التجميع حسب الحساب
            summary = df_raw.groupby('LedgerName').agg({
                'Dr': 'sum', 
                'Cr': 'sum',
                'AcLedger': 'first'
            }).reset_index()
            
            summary['Balance'] = summary['Dr'] - summary['Cr']

            # --- الفلترة الرقمية بناءً على ميزان المراجعة المرفوع ---
            # 113: حسابات العملاء (الميزان ص1)
            # 115: أرصدة مدينة أخرى (الميزان ص3)
            # 118: ذمم مدينة غير تجارية (الميزان ص3)
            # 221: موردين بأرصدة مدينة (الميزان ص4)
            
            include_codes = ('113', '115', '118', '221')
            exclude_names = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة", "مصاريف", "مشتريات"]
            
            final_debtors = summary[
                (summary['AcLedger'].astype(str).str.startswith(include_codes)) & 
                (~summary['LedgerName'].str.contains('|'.join(exclude_names), na=False)) &
                (summary['Balance'] > 0.01)
            ].sort_values('Balance', ascending=False)

            # --- 5. عرض النتائج ---
            total_val = final_debtors['Balance'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("إجمالي المديونية المكتشفة", f"{total_val:,.2f} ر.س")
            c2.metric("عدد الحسابات المدينة", f"{len(final_debtors)}")
            
            target = 218789.96
            if abs(total_val - target) < 1:
                st.success(f"✅ تم التطابق التام مع ميزان المراجعة: {target:,.2f} ر.س")
            else:
                st.warning(f"الفرق الحالي عن المستهدف: {target - total_val:,.2f} ر.س")

            st.subheader("📋 كشف الأرصدة (العملاء والذمم المدينة والموردين)")
            st.dataframe(
                final_debtors[['LedgerName', 'AcLedger', 'Balance']], 
                column_config={
                    "Balance": st.column_config.NumberColumn("الرصيد", format="%.2f"),
                    "AcLedger": "رقم الحساب"
                },
                use_container_width=True, 
                height=600
            )
            
        except Exception as e:
            st.error(f"خطأ في المعالجة: {e}")
else:
    st.info("💡 ارفع ملف LedgerBook.xml للبدء.")
