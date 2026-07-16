import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json
import io
import time

# التحقق من وجود مكتبة pypdf لقراءة السير الذاتية بصيغة PDF
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# تهيئة إعدادات الصفحة
st.set_page_config(
    page_title="منصة فرز السير الذاتية الذكية | AI Resume Screener",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص واجهة المستخدم والتنسيق العربي (RTL)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        text-align: right;
        direction: RTL;
    }
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #2563EB 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.2);
    }
    .card-container {
        background-color: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    .metric-box {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        border-right: 5px solid #2563EB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        direction: RTL;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif;
        font-weight: 600;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
    }
    </style>
""", unsafe_allow_html=True)

# دالة لقراءة ملفات PDF واستخراج النص منها
def extract_text_from_pdf(pdf_file):
    if PdfReader is None:
        return "⚠️ مكتبة pypdf غير مثبتة على بيئة العمل البرمجية الحالية لتشغيل ملفات الـ PDF."
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        return f"❌ فشل قراءة ملف الـ PDF: {str(e)}"

# دالة للتواصل مع Gemini 3.5-Flash للحصول على تقييم منظم بصيغة JSON
def screen_resume_with_ai(api_key, job_description, resume_text, candidate_name="مرشح غير معروف"):
    if not api_key:
        return {"error": "يرجى إدخال مفتاح الـ API للتفعيل."}
    
    prompt = f"""
    You are an elite corporate HR Recruiter. Analyze the candidate's Resume against the provided Job Description.
    Evaluate how well the candidate fits the role.

    [Job Description]
    {job_description}

    [Candidate Resume]
    {resume_text}

    Provide your response in Arabic and strictly in the following JSON format. Do not write any preamble, markdown blocks, or extra text. ONLY return the raw JSON object.
    
    Expected JSON Structure:
    {{
        "candidate_name": "{candidate_name}",
        "match_percentage": <integer between 0 and 100>,
        "strengths": ["strengths 1 in Arabic", "strength 2 in Arabic"],
        "weaknesses": ["weakness 1 in Arabic", "weakness 2 in Arabic"],
        "experience_summary": "brief summary of relevant experience in Arabic",
        "interview_questions": ["question 1 in Arabic based on weakness/experience", "question 2 in Arabic"]
    }}
    """
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        response = requests.post(f"{url}?key={api_key}", headers=headers, json=payload, timeout=40)
        if response.status_code == 200:
            result = response.json()
            raw_response = result['candidates'][0]['content']['parts'][0]['text']
            # محاولة تحويل النص القادم من API إلى قاموس JSON في بايثون
            return json.loads(raw_response.strip())
        else:
            return {"error": f"خطأ في خادم التحليل الذكي (كود {response.status_code})"}
    except Exception as e:
        return {"error": f"فشل في إتمام عملية الفرز الذكي: {str(e)}"}

# تصميم الشريط الجانبي
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ إعدادات المنصة</h2>", unsafe_allow_html=True)
    
    # مفتاح API
    gemini_key = st.text_input(
        "مفتاح Gemini API", 
        type="password",
        help="احصل على مفتاحك المجاني من Google AI Studio لتشغيل محرك الفرز الذكي."
    )
    
    st.markdown("---")
    st.markdown("### 📋 نوع إدخال السير الذاتية")
    input_method = st.radio(
        "اختر طريقة رفع السير الذاتية للمتقدمين:",
        ["📁 ملفات فردية (PDF / TXT)", "📊 ملف Excel / CSV مجمع"]
    )
    
    if PdfReader is None:
        st.warning("⚠️ ملاحظة: لقراءة ملفات الـ PDF يرجى تثبيت مكتبة pypdf.")
        
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; font-size: 0.85rem; color: gray;'>"
        "منصة فرز السير الذاتية الذكية v1.0 © 2026"
        "</div>", 
        unsafe_allow_html=True
    )

# الهيدر الرئيسي
st.markdown("""
    <div class="main-header">
        <h1>👥 منصة فرز ومطابقة السير الذاتية بالذكاء الاصطناعي</h1>
        <p>قم بمطابقة السير الذاتية لمرشحيك مع الوصف الوظيفي المستهدف واكتشف أفضل الكفاءات خلال ثوانٍ معدودة</p>
    </div>
""", unsafe_allow_html=True)

# واجهة المدخلات الأساسية
col_jd, col_candidates = st.columns([4, 5])

with col_jd:
    st.markdown("<div class='card-container'>", unsafe_allow_html=True)
    st.markdown("### 📝 1. أدخل الوصف الوظيفي (Job Description)")
    
    # وصف وظيفي افتراضي للبدء السريع والتجربة
    default_jd = """مطلوب مهندس برمجيات بايثون (Python Backend Developer) ذو خبرة لا تقل عن سنتين.
المتطلبات الأساسية:
- خبرة قوية في لغة بايثون وإطار عمل Django أو FastAPI.
- فهم ممتاز للتعامل مع قواعد البيانات SQL (PostgreSQL/MySQL).
- معرفة جيدة بالتعامل مع الـ RESTful APIs وربط الخدمات الخارجية.
- القدرة على العمل الجماعي وامتلاك مهارات تواصل قوية باللغة العربية والانجليزية."""
    
    job_desc = st.text_area(
        "اكتب أو الصق متطلبات الوظيفة الشاغرة ومؤهلاتها:", 
        value=default_jd,
        height=250,
        placeholder="اكتب متطلبات الوظيفة، المهارات التقنية، الخبرة، والشهادات المطلوبة هنا..."
    )
    st.markdown("</div>", unsafe_allow_html=True)

# معالجة رفع السير الذاتية بناءً على الطريقة المختارة
candidates_list = []

with col_candidates:
    st.markdown("<div class='card-container'>", unsafe_allow_html=True)
    st.markdown("### 📂 2. ارفع مستندات المتقدمين للوظيفة")
    
    if input_method == "📁 ملفات فردية (PDF / TXT)":
        uploaded_files = st.file_uploader(
            "اختر ملفات السير الذاتية (يمكن اختيار ملفات متعددة):",
            type=["pdf", "txt"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for file in uploaded_files:
                file_name_clean = file.name.rsplit('.', 1)[0]
                if file.name.endswith('.pdf'):
                    text = extract_text_from_pdf(file)
                else:
                    text = file.read().decode('utf-8', errors='ignore')
                
                candidates_list.append({
                    "name": file_name_clean,
                    "resume_text": text
                })
            st.success(f"✅ تم تحميل وتجهيز {len(candidates_list)} سيرة ذاتية للفرز.")
            
    else:
        uploaded_excel = st.file_uploader(
            "ارفع ملف Excel أو CSV يحتوي على أسئلة وسير ذاتية:",
            type=["xlsx", "csv"]
        )
        if uploaded_excel:
            try:
                if uploaded_excel.name.endswith('.csv'):
                    df_excel = pd.read_csv(uploaded_excel)
                else:
                    df_excel = pd.read_excel(uploaded_excel)
                
                # التحقق من وجود الأعمدة اللازمة
                cols = df_excel.columns.tolist()
                st.write("أعمدة الملف المكتشفة:", cols)
                
                col_name = st.selectbox("اختر العمود المحتوي على (اسم المرشح):", cols)
                col_resume = st.selectbox("اختر العمود المحتوي على (محتوى السيرة الذاتية/المهارات):", cols)
                
                if st.button("تجهيز بيانات الملف المرفوع"):
                    for idx, row in df_excel.iterrows():
                        candidates_list.append({
                            "name": str(row[col_name]),
                            "resume_text": str(row[col_resume])
                        })
                    st.success(f"✅ تم سحب وتجهيز {len(candidates_list)} مرشح من جدول البيانات بنجاح.")
                    st.session_state["excel_candidates"] = candidates_list
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة ملف الإكسل: {str(e)}")
                
        if "excel_candidates" in st.session_state and len(candidates_list) == 0:
            candidates_list = st.session_state["excel_candidates"]
            
    st.markdown("</div>", unsafe_allow_html=True)

# تفعيل زر الفرز الذكي
if len(candidates_list) > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 ابدأ المطابقة والفرز الذكي الآن", use_container_width=True, type="primary"):
        if not gemini_key:
            st.error("🔑 يرجى كتابة مفتاح Gemini API في الشريط الجانبي لتفعيل الفرز.")
        elif not job_desc.strip():
            st.warning("⚠️ يرجى كتابة الوصف الوظيفي المستهدف.")
        else:
            results_data = []
            progress_text = "جاري فرز ومطابقة السير الذاتية..."
            progress_bar = st.progress(0, text=progress_text)
            
            for index, candidate in enumerate(candidates_list):
                # حساب النسبة لتحديث شريط التقدم
                percent_complete = int(((index + 1) / len(candidates_list)) * 100)
                progress_bar.progress(percent_complete, text=f"تحليل مرشح ({index+1}/{len(candidates_list)}): {candidate['name']}")
                
                # إرسال السيرة الذاتية إلى الذكاء الاصطناعي
                analysis_result = screen_resume_with_ai(
                    api_key=gemini_key,
                    job_description=job_desc,
                    resume_text=candidate['resume_text'],
                    candidate_name=candidate['name']
                )
                
                if "error" not in analysis_result:
                    results_data.append(analysis_result)
                else:
                    # إضافة المرشح مع إشارة بحدوث خطأ بالتقييم
                    results_data.append({
                        "candidate_name": candidate['name'],
                        "match_percentage": 0,
                        "strengths": ["تعذر التحليل: " + analysis_result["error"]],
                        "weaknesses": ["-"],
                        "experience_summary": "فشل الاتصال بالذكاء الاصطناعي",
                        "interview_questions": ["-"]
                    })
                
                # تأخير بسيط لتجنب تخطي حدود الاستخدام المجانية لـ API
                time.sleep(1)
                
            progress_bar.empty()
            st.session_state["screening_results"] = results_data
            st.success("🎉 اكتملت عملية الفرز والمطابقة الذكية لجميع السير الذاتية بنجاح!")

# عرض التقرير والنتائج عند توفرها
if "screening_results" in st.session_state:
    results = st.session_state["screening_results"]
    df_results = pd.DataFrame(results)
    
    # تحويل نسبة المطابقة إلى أرقام لضمان عمل الرسوم البيانية
    df_results['match_percentage'] = pd.to_numeric(df_results['match_percentage'], errors='coerce').fillna(0).astype(int)
    
    # ----------------- قسم الإحصائيات العامة -----------------
    st.markdown("## 📊 لوحة تحليل نتائج الفرز والمطابقة")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""
            <div class="metric-box">
                <span style="font-size: 0.9rem; color: gray;">إجمالي السير المفرومة</span>
                <h2 style="margin: 0; color: #0F172A;">{len(df_results)} مرشحين</h2>
            </div>
        """, unsafe_allow_html=True)
    with m_col2:
        top_candidate = df_results.sort_values(by="match_percentage", ascending=False).iloc[0]
        st.markdown(f"""
            <div class="metric-box" style="border-right-color: #10B981;">
                <span style="font-size: 0.9rem; color: gray;">أعلى نسبة مطابقة مكتشفة</span>
                <h2 style="margin: 0; color: #10B981;">{top_candidate['match_percentage']}% ({top_candidate['candidate_name']})</h2>
            </div>
        """, unsafe_allow_html=True)
    with m_col3:
        avg_score = int(df_results['match_percentage'].mean())
        st.markdown(f"""
            <div class="metric-box" style="border-right-color: #F59E0B;">
                <span style="font-size: 0.9rem; color: gray;">متوسط نسبة المطابقة الإجمالية</span>
                <h2 style="margin: 0; color: #F59E0B;">{avg_score}%</h2>
            </div>
        """, unsafe_allow_html=True)

    tab_table, tab_charts, tab_details = st.tabs([
        "📋 جدول الفرز العام وتصدير التقرير",
        "📈 مخططات المقارنة والتحليلات البصرية",
        "🔍 تقرير المطابقة التفصيلي لكل مرشح"
    ])
    
    # Tab 1: Table and Export
    with tab_table:
        st.markdown("### 👥 ترتيب المتقدمين للوظيفة حسب درجة المطابقة")
        
        # تنسيق وعرض جدول مرتب من الأعلى مطابقة إلى الأقل
        df_display = df_results[['candidate_name', 'match_percentage', 'experience_summary']].sort_values(by="match_percentage", ascending=False)
        df_display.columns = ["اسم المتقدم للوظيفة", "نسبة المطابقة (%)", "نبذة عن الخبرة والمؤهلات"]
        
        st.dataframe(df_display, use_container_width=True)
        
        # أداة تصدير تقرير إكسل
        st.markdown("---")
        st.markdown("### 📥 تنزيل تقرير التوظيف النهائي")
        st.write("يمكنك حفظ وتنزيل تقرير الفرز النهائي كملف Excel لتتمكن من مشاركته مع فريق إدارة الموارد البشرية أو متخذي القرار في شركتك:")
        
        # توليد ملف الإكسل مؤقتاً في الذاكرة لتنزيله
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # تنظيف قائمة السلاسل وحفظها بشكل مرئي مريح في إكسل
            df_export = df_results.copy()
            df_export['strengths'] = df_export['strengths'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            df_export['weaknesses'] = df_export['weaknesses'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            df_export['interview_questions'] = df_export['interview_questions'].apply(lambda x: "\n".join(x) if isinstance(x, list) else x)
            
            df_export.columns = ["اسم المرشح", "نسبة المطابقة (%)", "نقاط القوة", "نقاط الضعف والتحديات", "ملخص الخبرات والمهارات", "أسئلة المقابلة المقترحة"]
            df_export.to_excel(writer, index=False, sheet_name="تقرير مطابقة المرشحين")
            
        st.download_button(
            label="💾 تحميل تقرير الفرز النهائي كملف Excel",
            data=buffer.getvalue(),
            file_name="AI_Resume_Screening_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # Tab 2: Visual Charts
    with tab_charts:
        st.markdown("### 📈 مقارنة بصرية لمستوى المرشحين")
        
        # مخطط شريطي أفقي للمرشحين ونسبهم
        df_chart_sorted = df_results.sort_values(by="match_percentage", ascending=True)
        fig_bar = px.bar(
            df_chart_sorted, 
            y="candidate_name", 
            x="match_percentage",
            orientation='h',
            title="تقييم ومطابقة المتقدمين مع معايير الوظيفة الشاغرة",
            labels={"candidate_name": "اسم المرشح", "match_percentage": "نسبة المطابقة الجذابة (%)"},
            color="match_percentage",
            color_continuous_scale="Purples",
            template="plotly_white"
        )
        fig_bar.update_layout(font_family="Cairo", title_font_size=18, title_x=0.5)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tab 3: Detailed AI Reports
    with tab_details:
        st.markdown("### 🔍 تقرير المطابقة والأسئلة المقترحة لكل مرشح")
        
        selected_candidate = st.selectbox("اختر اسم المرشح لاستعراض ملف تحليله التفصيلي بالكامل:", df_results['candidate_name'].tolist())
        
        if selected_candidate:
            c_data = df_results[df_results['candidate_name'] == selected_candidate].iloc[0]
            
            # عرض تفاصيل كارت المرشح المختار
            col_det1, col_det2 = st.columns([1, 2])
            
            with col_det1:
                # تصميم حلقة دائرية تظهر النسبة بشكل جميل
                match_col = "#10B981" if c_data['match_percentage'] >= 75 else "#F59E0B" if c_data['match_percentage'] >= 50 else "#EF4444"
                st.markdown(f"""
                    <div style="text-align: center; padding: 2rem; background: #f8fafc; border-radius: 15px; border: 2px solid #e2e8f0;">
                        <h4 style="margin: 0; color: #64748b;">معدل التوافق والمطابقة</h4>
                        <span style="font-size: 5rem; font-weight: 700; color: {match_col};">{c_data['match_percentage']}%</span>
                        <p style="font-weight: 600; color: {match_col};">{"مرشح واعد ومثالي ✅" if c_data['match_percentage'] >= 75 else "مطابقة متوسطة (تتطلب مقابلة)" if c_data['match_percentage'] >= 50 else "ضعيف المطابقة ❌"}</p>
                    </div>
                """, unsafe_allow_html=True)
                
            with col_det2:
                st.markdown("#### 📝 ملخص التقييم والخبرات:")
                st.write(c_data['experience_summary'])
                
            st.markdown("---")
            col_sw1, col_sw2 = st.columns(2)
            
            with col_sw1:
                st.markdown("#### ⭐ نقاط القوة والتميز المكتشفة:")
                if isinstance(c_data['strengths'], list):
                    for strength in c_data['strengths']:
                        st.markdown(f"🔹 {strength}")
                else:
                    st.write(c_data['strengths'])
                    
            with col_sw2:
                st.markdown("#### ⚠️ نقاط الضعف والفجوات المهارية:")
                if isinstance(c_data['weaknesses'], list):
                    for weakness in c_data['weaknesses']:
                        st.markdown(f"🔸 {weakness}")
                else:
                    st.write(c_data['weaknesses'])
                    
            st.markdown("---")
            st.markdown("### ❓ أسئلة المقابلة الشخصية المقترحة لهذا المرشح:")
            st.info("تم صياغة هذه الأسئلة بدقة من قبل الذكاء الاصطناعي بناءً على الفجوات أو تفاصيل الخبرة في السيرة الذاتية لاختبار مدى كفاءة المرشح الفنية:")
            
            if isinstance(c_data['interview_questions'], list):
                for i, q in enumerate(c_data['interview_questions']):
                    st.markdown(f"**السؤال {i+1}:** {q}")
            else:
                st.write(c_data['interview_questions'])
