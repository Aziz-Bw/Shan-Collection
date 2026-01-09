import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="تحصيل شان الحديثة", layout="wide")

st.title("💸 مديونية العملاء - مطابقة تامة")
st.markdown("### المستهدف: **218,789.96** ر.س (40 عميل)")

# --- 2. دالة القراءة المستقرة والآمنة ---
def get_xml_df(file):
    if file is None: return None
    file.seek(0)
    try:
        # قراءة الملف ومعالجة كل سطر بشكل منفصل لضمان عدم فقدان بيانات
        tree = ET.parse(file)
        root = tree.getroot()
        all_rows = []
        for row in root:
            all_rows.append({child.tag: child.text for child in row})
        return pd.DataFrame(all_rows)
    except Exception as e:
        st.error(f"حدث خطأ في قراءة الملف: {e}")
        return None

# --- 3. القائمة الجانبية للرفع ---
with st.sidebar:
    st.header("📂 استيراد البيانات")
    f_ledger = st.file_uploader("ارفع ملف LedgerBook.xml", type=['xml'], key="ledger_input")

# --- 4. المعالجة والمطابقة التامة ---
if f_ledger:
    df = get_xml_df(f_ledger)
    if df is not None:
        try:
            # تحويل المبالغ لأرقام عشرية دقيقة
            df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
            df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
            
            # الفلترة الذكية بناءً على PDF: حسابات 113 و 221 فقط
            mask_customers = df['AcLedger'].astype(str).str.startswith(('113', '221'))
            df_customers = df[mask_customers].copy()
            
            # قائمة الاستبعاد لضمان التطابق مع البرنامج (البنوك والعهد)
            exclude_list = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة"]
            
            # تجميع الحركات وحساب الرصيد لكل عميل
            summary = df_customers.groupby('LedgerName').agg({
                'Dr': 'sum', 
                'Cr': 'sum'
            }).reset_index()
            
            summary['Balance'] = summary['Dr'] - summary['Cr']
            
            # الفلترة النهائية: رصيد أكبر من صفر + استبعاد البنوك
            final = summary[
                (~summary['LedgerName'].str.contains('|'.join(exclude_list), na=False)) & 
                (summary['Balance'] > 0.01)
            ].sort_values('Balance', ascending=False)
            
            # --- 5. عرض النتائج ---
            current_total = final['Balance'].sum()
            count_found = len(final)
            
            c1, c2 = st.columns(2)
            c1.metric("إجمالي المديونية الحالية", f"{current_total:,.2f} ر.س")
            c2.metric("عدد العملاء المكتشفين", f"{count_found}")
            
            # التحقق من المطابقة (المستهدف 218,789.96)
            target = 218789.96
            if round(current_total, 2) == target:
                st.success(f"✅ مبروك! تم التطابق التام مع تقرير البرنامج: {target:,.2f} ر.س")
            else:
                diff = target - current_total
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
            st.error(f"خطأ أثناء معالجة البيانات: {e}")
else:
    st.warning("⚠️ الرجاء رفع ملف LedgerBook.xml للبدء.")
