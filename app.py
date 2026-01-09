import streamlit as st
import pandas as pd
import plotly.express as px
import xml.etree.ElementTree as ET

# --- 1. إعدادات الصفحة (التصميم الخام النظيف) ---
st.set_page_config(
    page_title="تحصيل شان الحديثة",
    layout="wide",
    page_icon="💸",
    initial_sidebar_state="expanded"
)

# --- CSS لتنسيق الخط والاتجاه ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
    }
    
    h1, h2, h3 { font-family: 'Tajawal', sans-serif; }
    
    /* محاذاة القوائم لليمين */
    .stSelectbox, .stTextInput, .stNumberInput { direction: rtl; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. إدارة الحالة (تخزين الملف في الذاكرة) ---
if 'ledger_file' not in st.session_state: st.session_state['ledger_file'] = None

# --- 3. دوال المعالجة ---
@st.cache_data(ttl=3600)
def load_ledger_data(file_ledger):
    try:
        file_ledger.seek(0)
        tree = ET.parse(file_ledger)
        df = pd.DataFrame([{child.tag: child.text for child in row} for row in tree.getroot()])
        
        # تحويل الأرقام لضمان دقة الحسابات
        df['Dr'] = pd.to_numeric(df['Dr'], errors='coerce').fillna(0)
        df['Cr'] = pd.to_numeric(df['Cr'], errors='coerce').fillna(0)
        return df
    except:
        return None

# --- 4. القائمة الجانبية ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("مديول التحصيل")
    st.info("📂 ارفع ملف LedgerBook.xml فقط")
    
    f3 = st.file_uploader("LedgerBook.xml", type=['xml'], key="f3_unique")
    if f3:
        st.session_state['ledger_file'] = f3

    if st.button("🗑️ مسح الذاكرة"):
        st.session_state['ledger_file'] = None
        st.rerun()

# ========================================================
# مديول التحصيل والديون (مستقل تماماً)
# ========================================================
st.header("💸 مراقبة الديون والعملاء")

if st.session_state['ledger_file']:
    df_ledger = load_ledger_data(st.session_state['ledger_file'])
    
    if df_ledger is not None:
        # --- 1. الكشف الذكي عن العملاء (بناءً على حسابات المبيعات) ---
        if 'AcLedger' in df_ledger.columns:
            # فلترة الحسابات التي تحتوي على "مبيعات" لاستخراج أسماء العملاء
            sales_mask = df_ledger['AcLedger'].astype(str).str.contains("إيرادات المبيعات|مبيعات", na=False)
            valid_customers_list = df_ledger[sales_mask]['LedgerName'].unique().tolist()
            
            # --- 2. قائمة الاستبعاد (البنوك والعهد) ---
            exclude_list = ["مصرف الراجحي", "البنك الأهلي", "صندوق", "نقدية", "شبكة"]
            final_customers = [c for c in valid_customers_list if not any(ex in c for ex in exclude_list)]
            
            if len(final_customers) > 0:
                # --- 3. حساب الأرصدة النهائية ---
                customers_full_data = df_ledger[df_ledger['LedgerName'].isin(final_customers)]
                
                cust_summary = customers_full_data.groupby('LedgerName').agg(
                    Total_Debit=('Dr', 'sum'),
                    Total_Credit=('Cr', 'sum')
                ).reset_index()
                
                cust_summary['Balance'] = cust_summary['Total_Debit'] - cust_summary['Total_Credit']
                
                # تصفية: نأخذ فقط من رصيده أكبر من 0.01 ريال لمطابقة تقرير البرنامج
                debtors = cust_summary[cust_summary['Balance'] > 0.01].sort_values('Balance', ascending=False)
                
                # --- 4. عرض النتائج والمؤشرات ---
                total_debt = debtors['Balance'].sum()
                count_debtors = len(debtors)
                
                st.success(f"✅ تم التعرف على {count_debtors} عميل مدين.")
                
                m1, m2 = st.columns(2)
                m1.metric("إجمالي الديون القائمة", f"{total_debt:,.2f} ر.س", help="يجب أن يطابق 218,789.96")
                m2.metric("عدد العملاء", f"{count_debtors}", help="المستهدف 40 عميل")
                
                st.markdown("---")
                
                # الرسوم البيانية والجداول
                c1, c2 = st.columns([2, 1])
                with c1:
                    top_15 = debtors.head(15)
                    fig = px.bar(top_15, x='LedgerName', y='Balance', text_auto='.2s', 
                                 title="أعلى 15 مديونية", color='Balance', color_continuous_scale='Reds')
                    st.plotly_chart(fig, use_container_width=True)
                
                with c2:
                    st.dataframe(
                        debtors[['LedgerName', 'Balance']],
                        column_config={
                            "LedgerName": "اسم العميل",
                            "Balance": st.column_config.NumberColumn("الرصيد (دين)", format="%.2f"),
                        },
                        use_container_width=True,
                        height=500
                    )
            else:
                st.warning("⚠️ لم يتم العثور على عملاء مطابقين في هذا الملف.")
        else:
            st.error("❌ العمود 'AcLedger' غير موجود في الملف المرفوع.")
else:
    st.info("💡 الرجاء رفع ملف LedgerBook.xml من القائمة الجانبية لعرض تقرير الديون.")
