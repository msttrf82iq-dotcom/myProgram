import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import io

st.set_page_config(
    page_title="محلل البيانات الذكي - لوحة تحكم تفاعلية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI, Arabic RTL direction, and smooth fonts
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        text-align: right;
        direction: RTL;
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
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .card-container {
        background-color: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def query_gemini_api(api_key, df_summary, user_question):
    """
    Sends data structure and user question to Gemini API for smart analysis.
    """
    if not api_key:
        return "⚠️ يرجى إدخال مفتاح API لـ Gemini في الشريط الجانبي لتفعيل المساعد الذكي."
    
    # We construct a rich context for the LLM to understand the dataset's structure
    prompt = f"""
    لقد تم تحميل مجموعة بيانات في لوحة التحكم. إليك تفاصيل البيانات وملخصها الإحصائي:
    
    {df_summary}
    
    سؤال المستخدم: "{user_question}"
    
    قم بتحليل البيانات بناءً على السؤال المطروح وقدم إجابة احترافية، دقيقة، وموجهة لمساعدة صاحب العمل أو متخذ القرار باللغة العربية الفصحى. استخدم نقاطاً واضحة وجداول مبسطة إذا لزم الأمر.
    """
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    try:
        # Appending key to URL parameters
        response = requests.post(f"{url}?key={api_key}", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            error_details = response.json()
            return f"❌ خطأ من الخادم (كود {response.status_code}): {error_details.get('error', {}).get('message', 'حدث خطأ غير معروف')}"
    except Exception as e:
        return f"❌ فشل الاتصال بالذكاء الاصطناعي: {str(e)}"

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ إعدادات التحكم</h2>", unsafe_allow_html=True)
    
    # File Uploader
    uploaded_file = st.file_uploader(
        "قم برفع ملف البيانات الخاص بك", 
        type=["csv", "xlsx"],
        help="ندعم ملفات Excel (.xlsx) و CSV"
    )
    
    st.markdown("---")
    st.markdown("### 🤖 إعدادات المساعد الذكي")
    gemini_key = st.text_input(
        "مفتاح Gemini API (اختياري)", 
        type="password",
        help="احصل على مفتاح مجاني من Google AI Studio لتفعيل ميزة تحليل البيانات بالذكاء الاصطناعي."
    )
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; font-size: 0.85rem; color: gray;'>"
        "لوحة تحكم ذكية تم تطويرها بواسطة مطور الويب المحترف الخاص بك 🚀"
        "</div>", 
        unsafe_allow_html=True
    )

st.markdown("""
    <div class="main-header">
        <h1>📊 لوحة تحكم تحليل البيانات الذكية والتفاعلية</h1>
        <p>قم برفع ملفاتك، واستكشف الرسومات التفاعلية، واسأل الذكاء الاصطناعي للحصول على توصيات مباشرة!</p>
    </div>
""", unsafe_allow_html=True)

if uploaded_file is not None:
    try:
        # Load data dynamically based on format
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Ensure there are no styling bugs with empty columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="🔢 عدد الصفوف (السجلات)", value=f"{df.shape[0]:,}")
        with col2:
            st.metric(label="🗂️ عدد الأعمدة", value=df.shape[1])
        with col3:
            total_missing = df.isnull().sum().sum()
            st.metric(label="⚠️ القيم المفقودة الإجمالية", value=f"{total_missing:,}", delta=f"{'نظيفة' if total_missing == 0 else 'تحتاج معالجة'}", delta_color="inverse")
        with col4:
            total_duplicates = df.duplicated().sum()
            st.metric(label="👥 السجلات المكررة", value=f"{total_duplicates:,}")

        tab_overview, tab_visuals, tab_ai = st.tabs([
            "🔍 نظرة عامة واستكشاف البيانات", 
            "📈 التحليل المرئي والتفاعلي", 
            "🤖 المساعد الذكي بالذكاء الاصطناعي"
        ])
        
        # ----------------- Tab 1: Overview -----------------
        with tab_overview:
            st.markdown("### 📋 استعراض عينة من البيانات")
            st.dataframe(df.head(15), use_container_width=True)
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("<div class='card-container'>", unsafe_allow_html=True)
                st.markdown("### 🛠️ معلومات وهيكل الأعمدة")
                info_df = pd.DataFrame({
                    "نوع البيانات": df.dtypes.astype(str),
                    "القيم غير الفارغة": df.notnull().sum(),
                    "القيم المفقودة": df.isnull().sum(),
                    "القيم الفريدة": df.nunique()
                })
                st.dataframe(info_df, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_right:
                st.markdown("<div class='card-container'>", unsafe_allow_html=True)
                st.markdown("### 📊 الإحصاءات الوصفية للأعمدة الرقمية")
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    st.dataframe(df[numeric_cols].describe().T, use_container_width=True)
                else:
                    st.info("لا توجد أعمدة رقمية في مجموعة البيانات المرفوعة لتوليد الإحصاءات الوصفية.")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_visuals:
            st.markdown("### 🎨 قم بإنشاء رسوماتك التفاعلية المخصصة")
            
            all_cols = df.columns.tolist()
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
            
            col_v1, col_v2, col_v3 = st.columns([1, 1, 1])
            
            with col_v1:
                chart_type = st.selectbox(
                    "اختر نوع الرسم البياني",
                    ["مخطط شريطي (Bar)", "مخطط خطي (Line)", "مخطط مبعثر (Scatter)", "مخطط دائري (Pie)", "مخطط الصندوق (Box)"]
                )
            with col_v2:
                x_axis = st.selectbox("المحور السيني (X-Axis)", all_cols)
            with col_v3:
                # Fallback to same axis or numerical if available
                y_default = num_cols[0] if num_cols else all_cols[0]
                y_axis = st.selectbox("المحور الصادي (Y-Axis)", all_cols, index=all_cols.index(y_default))
                
            # Extra customization options
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                color_by = st.selectbox("تلوين وتقسيم البيانات بواسطة (اختياري)", ["بلا تلوين"] + all_cols)
            with col_opt2:
                chart_title = st.text_input("عنوان مخصص للرسم البياني", f"{chart_type} لـ {y_axis} مقابل {x_axis}")
            
            # Generating Chart based on selection
            color_param = color_by if color_by != "بلا تلوين" else None
            fig = None
            
            try:
                if chart_type == "مخطط شريطي (Bar)":
                    fig = px.bar(df, x=x_axis, y=y_axis, color=color_param, title=chart_title, template="plotly_white")
                elif chart_type == "مخطط خطي (Line)":
                    fig = px.line(df, x=x_axis, y=y_axis, color=color_param, title=chart_title, template="plotly_white")
                elif chart_type == "مخطط مبعثر (Scatter)":
                    fig = px.scatter(df, x=x_axis, y=y_axis, color=color_param, title=chart_title, template="plotly_white")
                elif chart_type == "مخطط دائري (Pie)":
                    # For pie, aggregate if there's duplicate X categories
                    pie_data = df.groupby(x_axis)[y_axis].sum().reset_index() if y_axis in num_cols else df[x_axis].value_counts().reset_index()
                    pie_data.columns = [x_axis, y_axis]
                    fig = px.pie(pie_data, names=x_axis, values=y_axis, title=chart_title, template="plotly_white")
                elif chart_type == "مخطط الصندوق (Box)":
                    fig = px.box(df, x=x_axis, y=y_axis, color=color_param, title=chart_title, template="plotly_white")
                
                if fig:
                    # Aesthetic touches to the generated plotly chart
                    fig.update_layout(
                        font_family="Cairo",
                        title_font_size=20,
                        title_x=0.5,
                        xaxis_title=x_axis,
                        yaxis_title=y_axis
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("عذراً، تعذر إنشاء الرسم البياني المطلوب.")
            except Exception as chart_err:
                st.error(f"⚠️ حدث خطأ أثناء محاولة رسم هذه البيانات: {str(chart_err)}")
                st.info("نصيحة: تأكد من ملاءمة أنواع البيانات المختارة (مثلاً: المخطط الخطي يعمل بشكل أفضل مع التواريخ أو السلاسل الزمنية).")

        with tab_ai:
            st.markdown("### 🤖 اسأل محلل البيانات الذكي (AI Assistant)")
            st.write("يقوم المساعد الذكي بدراسة الهيكل العام لبياناتك، مسميات الأعمدة، والملخص الإحصائي، ثم يجيب على أي سؤال تطرحه لمساعدتك في استخراج القيمة الحقيقية للبيانات.")
            
            # Prepare summarized information of the dataset for the API
            # Limit head representation to reduce token sizes while keeping structural information clear
            buffer = io.StringIO()
            df.info(buf=buffer)
            info_summary = buffer.getvalue()
            
            describe_summary = ""
            if len(num_cols) > 0:
                describe_summary = df[num_cols].describe().to_string()
                
            sample_data = df.head(5).to_string()
            
            full_summary_context = f"""
            أعمدة مجموعة البيانات ومعلوماتها الأساسية:
            {info_summary}
            
            الملخص الإحصائي للأعمدة الرقمية:
            {describe_summary}
            
            عينة من أول 5 صفوف في البيانات:
            {sample_data}
            """
            
            # Quick suggestions
            st.markdown("**💡 أسئلة مقترحة سريعة:**")
            suggestions = [
                "ما هي الملاحظات الأساسية والأنماط الهامة التي يمكنك استنتاجها من عينة وملخص هذه البيانات؟",
                "إذا كانت هذه بيانات مبيعات أو أعمال، كيف يمكنني زيادة الكفاءة أو الأرباح بناءً على هيكلها؟",
                "هل هناك أي مشاكل أو قيم شاذة واضحة في ملخص الإحصاءات يجب علي معالجتها؟"
            ]
            
            selected_suggestion = st.selectbox("اختر سؤالاً جاهزاً أو اكتب سؤالك بالأسفل:", ["-- اختر سؤالاً مقترحاً --"] + suggestions)
            
            user_input = st.text_area(
                "اكتب سؤالك التفصيلي هنا بكل وضوح:",
                value="" if selected_suggestion == "-- اختر سؤالاً مقترحاً --" else selected_suggestion,
                placeholder="مثال: هل هناك علاقة واضحة بين الأعمدة؟ أو أي أفكار تسويقية تقترحها علي من هذه البيانات؟"
            )
            
            if st.button("🚀 اطلب التحليل الآن", use_container_width=True):
                if not gemini_key:
                    st.warning("🔑 يرجى توفير مفتاح Gemini API في الشريط الجانبي لتتمكن من استخدام هذه الميزة.")
                elif not user_input.strip():
                    st.warning("✍️ يرجى كتابة سؤالك أولاً قبل إرسال الطلب.")
                else:
                    with st.spinner("⏳ يقوم الذكاء الاصطناعي الآن بقراءة البيانات وصياغة تقرير احترافي لك..."):
                        response_text = query_gemini_api(gemini_key, full_summary_context, user_input)
                        st.markdown("---")
                        st.markdown("### 📊 التقرير والتحليل الذكي المستنتج:")
                        st.markdown(response_text)
                        st.markdown("---")
                        
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء معالجة الملف المرفوع: {str(e)}")
        st.info("تأكد من أن الملف سليم ولا يحتوي على تنسيقات تالفة أو أوراق عمل فارغة.")

else:
    st.markdown("""
        <div style="text-align: center; padding: 3rem; background-color: #f8fafc; border-radius: 15px; border: 2px dashed #cbd5e1; margin-top: 2rem;">
            <span style="font-size: 4rem;">📥</span>
            <h3 style="margin-top: 1rem; color: #1E3A8A;">بانتظار رفع ملف البيانات الخاص بك</h3>
            <p style="color: #64748b; max-width: 600px; margin: 0 auto;">
                الرجاء سحب وإفلات ملف Excel أو CSV في الجزء المخصص بالشريط الجانبي (على اليمين أو اليسار بحسب لغة متصفحك) للبدء في استخراج البيانات وبناء اللوحة التفاعلية فوراً.
            </p>
        </div>
    """, unsafe_allow_html=True)
