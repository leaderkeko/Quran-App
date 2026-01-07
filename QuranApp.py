import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# --- إعدادات وتخصيص الواجهة ---
st.set_page_config(page_title="نظام مسجد التقوى", layout="wide")

# دالة لمعالجة النصوص العربية لتظهر بشكل صحيح في الـ PDF
def ar(text):
    return get_display(reshape(str(text)))

# إنشاء مجلدات الصور
if not os.path.exists("student_images"): os.makedirs("student_images")

# --- الهوية البصرية ---
col1, col2 = st.columns([1, 5])
with col1:
    # استبدل الرابط برابط صورة اللوغو الخاص بمسجدك
    st.image("https://cdn-icons-png.flaticon.com/512/2412/2412959.png", width=100)
with col2:
    st.title("نظام إدارة حلقة مسجد [ضع اسم مسجدك هنا]")
    st.subheader("لوحة التحكم وإصدار التقارير للأهل")

# --- إدارة البيانات ---
FILE_NAME = 'students_data.csv'
def load_data():
    if os.path.exists(FILE_NAME): return pd.read_csv(FILE_NAME)
    return pd.DataFrame(columns=["التاريخ", "اسم الطالب", "عدد الصفحات", "تقييم الحفظ", "تقييم التجويد", "ملاحظات", "مسار الصورة"])

df = load_data()

# --- إدخال البيانات (الجانبي) ---
st.sidebar.header("📥 إدخال بيانات التسميع")
with st.sidebar.form("student_form"):
    name = st.text_input("اسم الطالب")
    date = st.date_input("التاريخ", datetime.now())
    pages = st.number_input("عدد الصفحات", min_value=0.1, step=0.1)
    hifz = st.selectbox("تقييم الحفظ", ["ممتاز", "جيد جداً", "جيد", "مقبول", "إعادة"])
    tajweed = st.slider("تقييم التجويد", 0, 10, 8)
    note = st.text_area("ملاحظات إضافية")
    img = st.file_uploader("ارفع صورة الطالب", type=['jpg', 'png', 'jpeg'])
    
    if st.form_submit_button("حفظ البيانات"):
        img_path = "No Image"
        if img:
            img_path = f"student_images/{name}.jpg"
            with open(img_path, "wb") as f: f.write(img.getbuffer())
        
        new_row = [date, name, pages, hifz, tajweed, note, img_path]
        df.loc[len(df)] = new_row
        df.to_csv(FILE_NAME, index=False)
        st.success("تم الحفظ بنجاح!")
        st.rerun()

# --- عرض التقارير والمخططات ---
tab1, tab2 = st.tabs(["📈 إحصائيات عامة", "👤 تقرير الطالب و PDF"])

with tab1:
    if not df.empty:
        st.write("### ملخص الأداء العام")
        fig = px.bar(df, x="اسم الطالب", y="عدد الصفحات", color="تقييم الحفظ", title="مجموع الصفحات المسمعة لكل طالب")
        st.plotly_chart(fig, use_container_width=True)
	# --- قسم تقرير اليوم لجميع الطلاب (للواتساب) ---
st.markdown("---")
st.subheader("📋 إصدار تقرير اليوم لجميع الطلاب")

# اختيار التاريخ المراد استخراج تقريره
report_date = st.date_input("اختر التاريخ لاستخراج التقرير العام:", datetime.now())

# تصفية البيانات لهذا اليوم فقط
daily_data = df[df["التاريخ"] == str(report_date)]

if not daily_data.empty:
    st.write(f"عدد الطلاب الذين سَمّعوا اليوم: {len(daily_data)}")
    st.table(daily_data[["اسم الطالب", "عدد الصفحات", "تقييم الحفظ", "تقييم التجويد"]])

    if st.button("توليد تقرير اليوم العام (PDF)"):
        pdf = FPDF()
        pdf.add_page()
        
        font_path = "arial.ttf"
        if os.path.exists(font_path):
            pdf.add_font('ArabicFont', '', font_path, uni=True)
            pdf.set_font('ArabicFont', '', 18)
            
            # عنوان التقرير العام
            pdf.cell(200, 10, txt=ar(f"تقرير حلقة التحفيظ ليوم: {report_date}"), ln=True, align='C')
            pdf.ln(10)
            
            # إعداد جدول الطلاب
            pdf.set_font('ArabicFont', '', 11)
            # عرض الأعمدة: ملاحظات، تجويد، حفظ، صفحات، اسم الطالب
            pdf.cell(40, 10, ar("ملاحظات"), 1, 0, 'C')
            pdf.cell(25, 10, ar("التجويد"), 1, 0, 'C')
            pdf.cell(30, 10, ar("الحفظ"), 1, 0, 'C')
            pdf.cell(25, 10, ar("صفحات"), 1, 0, 'C')
            pdf.cell(60, 10, ar("اسم الطالب"), 1, 1, 'C')
            
            # إضافة بيانات كل طالب سَمّع في هذا اليوم
            for index, row in daily_data.iterrows():
                pdf.cell(40, 10, ar(row['ملاحظات'] if pd.notna(row['ملاحظات']) else "-"), 1, 0, 'C')
                pdf.cell(25, 10, ar(row['تقييم التجويد']), 1, 0, 'C')
                pdf.cell(30, 10, ar(row['تقييم الحفظ']), 1, 0, 'C')
                pdf.cell(25, 10, ar(row['عدد الصفحات']), 1, 0, 'C')
                pdf.cell(60, 10, ar(row['اسم الطالب']), 1, 1, 'C')
            
            pdf.ln(10)
            pdf.set_font('ArabicFont', '', 10)
            pdf.cell(200, 10, txt=ar("ما شاء الله، بارك الله في جهود الطلاب جميعاً"), ln=True, align='C')
            
            daily_file = f"Daily_Report_{report_date}.pdf"
            pdf.output(daily_file)
            with open(daily_file, "rb") as f:
                st.download_button("📥 تحميل تقرير اليوم العام لإرساله للأهل", f, file_name=daily_file)
        else:
            st.error("ملف الخط arial.ttf غير موجود.")
else:
    st.info("لا توجد بيانات مسجلة لهذا التاريخ.")
with tab2:
    if not df.empty:
        sel_student = st.selectbox("اختر الطالب لاستعراض تطوره:", df["اسم الطالب"].unique())
        s_data = df[df["اسم الطالب"] == sel_student]
        
        # ميني داشبورد للطالب
        c1, c2 = st.columns([1, 2])
        last_rec = s_data.iloc[-1]
        
        with c1:
            if last_rec['مسار الصورة'] != "No Image":
                st.image(last_rec['مسار الصورة'], caption=f"صورة {sel_student}", width=150)
            st.metric("آخر تقييم تجويد", f"{last_rec['تقييم التجويد']}/10")
        
        with c2:
            st.write(f"**مسار تطور الطالب: {sel_student}**")
            st.line_chart(s_data.set_index("التاريخ")["عدد الصفحات"])
# زر توليد PDF (سجل متابعة شامل)
        if st.button("توليد سجل المتابعة الشامل (PDF)"):
            pdf = FPDF()
            pdf.add_page()
            
            font_path = "arial.ttf"
            if os.path.exists(font_path):
                pdf.add_font('ArabicFont', '', font_path, uni=True)
                pdf.set_font('ArabicFont', '', 16)
                
                # عنوان التقرير
                pdf.cell(200, 10, txt=ar(f"سجل متابعة الطالب: {sel_student}"), ln=True, align='C')
                pdf.ln(10)
                
                # إضافة صورة الطالب في زاوية الصفحة إذا وجدت
                if last_rec['مسار الصورة'] != "No Image":
                    try:
                        pdf.image(last_rec['مسار الصورة'], x=10, y=10, w=30)
                    except: pass

                # إعداد الجدول
                pdf.set_font('ArabicFont', '', 12)
                # رسم رأس الجدول (عناوين الأعمدة)
                # العرض الإجمالي للصفحة تقريباً 190
                pdf.cell(40, 10, ar("ملاحظات"), 1, 0, 'C')
                pdf.cell(30, 10, ar("التجويد"), 1, 0, 'C')
                pdf.cell(30, 10, ar("الحفظ"), 1, 0, 'C')
                pdf.cell(30, 10, ar("الصفحات"), 1, 0, 'C')
                pdf.cell(40, 10, ar("التاريخ"), 1, 1, 'C') # 1 في النهاية تعني الانتقال لسطر جديد
                
                # إضافة بيانات التسميع (كل السجلات)
                for index, row in s_data.iterrows():
                    pdf.cell(40, 10, ar(row['ملاحظات'] if pd.notna(row['ملاحظات']) else "-"), 1, 0, 'C')
                    pdf.cell(30, 10, ar(row['تقييم التجويد']), 1, 0, 'C')
                    pdf.cell(30, 10, ar(row['تقييم الحفظ']), 1, 0, 'C')
                    pdf.cell(30, 10, ar(row['عدد الصفحات']), 1, 0, 'C')
                    pdf.cell(40, 10, ar(row['التاريخ']), 1, 1, 'C')

                pdf.ln(10)
                pdf.set_font('ArabicFont', '', 10)
                pdf.cell(200, 10, txt=ar(f"تم استخراج التقرير في: {datetime.now().strftime('%Y-%m-%d')}"), ln=True, align='L')
                
                p_file = f"Sijill_{sel_student}.pdf"
                pdf.output(p_file)
                with open(p_file, "rb") as f:
                    st.download_button("📥 تحميل سجل المتابعة الشامل", f, file_name=p_file)
            else:
                st.error("خطأ: ملف الخط arial.ttf غير موجود في المجلد.")