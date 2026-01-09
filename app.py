import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# إعدادات الصفحة
st.set_page_config(page_title="تحصيل شان الحديثة", layout="wide")

st.title("💸 مديونية العملاء - مطابقة تامة")
st.info("المستهدف: 218,789.96 ر.س (40 عميل)")

def get_xml_df(file):
    if file is None: return None
    file.seek(0)
    tree = ET.parse(file)
    return pd.DataFrame([{c.tag: child.text for child in row} for row in tree.getroot()])

with st.sidebar:
    st.header("📂 استيراد البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'])

if f_ledger:
    df = get_xml_df(f_ledger)
    if df is not None:
        try:
            df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
            df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
            
            # --- الفلترة الذهبية للمطابقة التامة ---
            # نعتمد على أرقام الحسابات (113 و 221) لاستخراج العملاء بدقة
            mask_customers = df['AcLedger'].astype(str).str.startswith(('113', '221'))
            df_customers = df[mask_customers]
            
            # استبعاد الحسابات غير الصفرية والراجحي
            exclude_list = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة"]
            
            summary = df_customers.groupby('LedgerName').agg({'Dr':'sum', 'Cr':'sum'}).reset_index()
            summary['Balance'] = summary['Dr'] - summary['Cr']
            
            # فلترة الأرصدة المدينة فقط (أكبر من 0.01 ريال)
            final = summary[
                (~summary['LedgerName'].str.contains('|'.join(exclude_list), na=False)) & 
                (summary['Balance'] > 0.01)
            ].sort_values('Balance', ascending=False)
            
            # عرض النتائج
            c1, c2 = st.columns(2)
            current_total = final['Balance'].sum()
            c1.metric("إجمالي المديونية الحالية", f"{current_total:,.2f} ر.س")
            c2.metric("عدد العملاء", f"{len(final)}")
            
            if round(current_total, 2) == 218789.96:
                st.success("✅ تم التطابق التام مع تقرير أعمار الديون (PDF)!")
            else:
                st.warning(f"الفرق الحالي: {218789.96 - current_total:,.2f} ر.س")

            st.divider()
            st.dataframe(final[['LedgerName', 'Balance']], use_container_width=True, height=600)
            
        except Exception as e:
            st.error(f"خطأ: {e}")
