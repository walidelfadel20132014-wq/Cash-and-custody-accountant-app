import streamlit as st
import pandas as pd
from datetime import datetime
import re

# إعدادات صفحة التطبيق
st.set_page_config(page_title="إدارة العهد والمصاريف الشخصية", page_icon="💰", layout="wide")

# تهيئة قاعدة بيانات مؤقتة في ذاكرة الجلسة
if 'transactions' not in st.session_state:
    st.session_state['transactions'] = pd.DataFrame(columns=[
        'التاريخ', 'النوع', 'القسم', 'البند / المشروع', 'المبلغ (ر.س)', 'الملاحظات'
    ])

st.title("📊 نظام إدارة العهد والمصاريف الشخصية (خاص)")
st.markdown("مرحباً بك يا مهندس وليد. نظامك المالي الخاص والمؤمن لتتبع عهد العمل والمصاريف الشخصية.")

# --- قسم التحليل الذكي لرسائل البنك النصية (SMS Parser) ---
st.sidebar.markdown("---")
st.sidebar.subheader("📥 محلل رسائل البنك الآلي")
sms_input = st.sidebar.text_area("ألصق نص رسالة البنك هنا:", placeholder="مثال: تم خصم مبلغ 250.00 SAR من بطاقة مدى في ...")

detected_amount = 0.0
detected_type = "صرف (عليه)"
detected_notes = ""

if sms_input:
    # استخراج المبلغ باستخدام التعبيرات النمطية (Regex)
    amount_match = re.search(r'(?:مبلغ|SAR|ر\.س\.?)\s*([\d,.]+)', sms_input)
    if amount_match:
        try:
            detected_amount = float(amount_match.group(1).replace(',', ''))
        except:
            detected_amount = 0.0
    detected_notes = sms_input
    st.sidebar.success(f"تم تحليل الرسالة بنجاح! المبلغ المستخرج: {detected_amount} ر.س")

# القوائم الجانبية للإدخال اليدوي أو عبر الرسالة
st.sidebar.header("➕ تسجيل حركة جديدة")

trans_type = st.sidebar.selectbox("نوع الحركة", ["صرف (عليه)", "إيداع / دفعة (له)"], index=0)
section = st.sidebar.selectbox("القسم", ["عهد العمل", "مصروفات شخصية"])
category = st.sidebar.text_input("البند أو اسم المشروع", placeholder="مثال: مشروع مدرسة المبرز / مواد بناء")
amount = st.sidebar.number_input("المبلغ (ريال سعودي)", min_value=0.0, value=detected_amount, step=10.0)
notes = st.sidebar.text_area("ملاحظات / تفاصيل إضافية", value=detected_notes)

if st.sidebar.button("حفظ الحركة في النظام"):
    if amount > 0 and category:
        new_row = pd.DataFrame({
            'التاريخ': [datetime.now().strftime("%Y-%m-%d %H:%M")],
            'النوع': [trans_type],
            'القسم': [section],
            'البند / المشروع': [category],
            'المبلغ (ر.س)': [amount],
            'الملاحظات': [notes]
        })
        st.session_state['transactions'] = pd.concat([st.session_state['transactions'], new_row], ignore_index=True)
        st.sidebar.success("تم تسجيل الحركة بنجاح!")
    else:
        st.sidebar.error("الرجاء إدخال المبلغ وتحديد البند على الأقل.")

# عرض لوحة المؤشرات الرئيسية (Dashboard)
df = st.session_state['transactions']

col1, col2, col3 = st.columns(3)

if not df.empty:
    work_df = df[df['قسم'] == 'عهد العمل']
    personal_df = df[df['قسم'] == 'مصروفات شخصية']
    
    # حساب إجماليات عهد العمل
    work_in = work_df[work_df['النوع'] == 'إيداع / دفعة (له)']['المبلغ (ر.س)'].sum()
    work_out = work_df[work_df['النوع'] == 'صرف (عليه)']['المبلغ (ر.س)'].sum()
    work_balance = work_in - work_out
    
    # حساب إجماليات المصروفات الشخصية
    personal_out = personal_df[personal_df['النوع'] == 'صرف (عليه)']['المبلغ (ر.س)'].sum()
    
    col1.metric("إجمالي صافي عهد العمل", f"{work_balance:,.2f} ر.س", help="العهدة المستلمة ناقص المصروفات")
    col2.metric("إجمالي مصروفات العمل", f"{work_out:,.2f} ر.س")
    col3.metric("إجمالي المصروفات الشخصية", f"{personal_out:,.2f} ر.س")
else:
    col1.metric("إجمالي صافي عهد العمل", "0.00 ر.س")
    col2.metric("إجمالي مصروفات العمل", "0.00 ر.س")
    col3.metric("إجمالي المصروفات الشخصية", "0.00 ر.س")

st.markdown("---")

# عرض جدول الحركات المفصل مع إمكانية الفلترة
st.subheader("📋 سجل الحركات المالية التفصيلي")

if not df.empty:
    filter_section = st.selectbox("تصفية حسب القسم:", ["الكل", "عهد العمل", "مصروفات شخصية"])
    if filter_section != "الكل":
        filtered_df = df[df['قسم'] == filter_section]
    else:
        filtered_df = df
        
    st.dataframe(filtered_df, use_container_width=True)
    
    # زر لتصدير البيانات إلى ملف CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 تحميل الكشف كملف Excel / CSV",
        data=csv,
        file_name='my_financial_report.csv',
        mime='text/csv',
    )
else:
    st.info("لا توجد حركات مسجلة حتى الآن. استخدم القائمة الجانبية لإضافة أو لصق أول حركة بنكية.")
