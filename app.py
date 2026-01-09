import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="تحصيل شان الحديثة", layout="wide")

st.title("💸 مديونية العملاء - مطابقة تامة")
st.info("المستهدف: 218,789.96 ر.س (40 عميل)")

# --- 2. دالة القراءة المصححة ---
def get_xml_df(file):
    if file is None: return None
    file.seek(0)
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        # تصحيح: استخراج البيانات بشكل مباشر وآمن
        data = []
        for row in root:
            data.append({child.tag: child.text for child in row})
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        return None

# --- 3. القائمة الجانبية ---
with st.sidebar:
    st.header("📂 استيراد البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'], key="ledger_main")

# --- 4. المعالجة والمطابقة ---
if f_ledger:
    df = get_xml_df(f_ledger)
    if df is not None:
        try:
            # تحويل الأرقام
            df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
            df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
            
            # فلترة حسابات العملاء (تبدأ بـ 113 أو 221)
            mask_customers = df['AcLedger'].astype(str).str.startswith(('113', '221'))
            df_customers = df[mask_customers]
            
            # قائمة الاستبعاد لضمان دقة الرقم
            exclude_list = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة"]
            
            # التجميع وحساب الأرصدة
            summary = df_customers.groupby('LedgerName').agg({
                'Dr': 'sum', 
                'Cr': 'sum'
            }).reset_index()
            
            summary['Balance'] = summary['Dr'] - summary['Cr']
            
            # التصفية النهائية (بدون بنوك + رصيد أكبر من صفر)
            final = summary[
                (~summary['LedgerName'].str.contains('|'.join(exclude_list), na=False)) & 
                (summary['Balance'] > 0.01)
            ].sort_values('Balance', ascending=False)
            
            # عرض النتائج
            c1, c2 = st.columns(2)
            current_total = final['Balance'].sum()
            c1.metric("إجمالي المديونية الحالية", f"{current_total:,.2f} ر.س")
            c2.metric("عدد العملاء المكتشفين", f"{len(final)}")
            
            # التحقق من المطابقة التامة
            if round(current_total, 2) == 218789.96:
                st.success("✅ تم التطابق التام مع تقرير البرنامج (218,789.96)!")
            else:
                diff = 218789.96 - current_total
                st.warning(f"الفرق المتبقي للمطابقة: {diff:,.2f} ر.س")

            st.divider()
            st.subheader("📋 كشف الأرصدة التفصيلي")
            st.dataframe(
                final[['LedgerName', 'Balance']], 
                column_config={"Balance": st.column_config.NumberColumn("الرصيد", format="%.2f")},
                use_container_width=True, 
                height=600
            )
            
        except Exception as e:
            st.error(f"حدث خطأ أثناء المعالجة: {e}")
else:
    st.warning("⚠️ الرجاء رفع ملف LedgerBook.xml للبدء.")
