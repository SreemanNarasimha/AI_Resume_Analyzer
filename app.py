import streamlit as st
import time

# Set page config FIRST
st.set_page_config(page_title="AI Resume Analyzer", layout="wide", page_icon="📄")

from utils import extractor, analyzer, visualizer

# --- Custom CSS for Styling ---
# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark Theme Background */
    .stApp {
        background-color: #0B0E14; /* Deep, semantic dark */
        color: #E2E8F0;
    }
    
    /* Gradient Headings */
    h1, h2, h3 {
        background: linear-gradient(90deg, #A78BFA, #2DD4BF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* Cards */
    .css-1r6slb0, .css-12oz5g7, div[data-testid="stExpander"] {
        background-color: #151B28;
        border: 1px solid #2D3748;
        border-radius: 16px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    }
    
    /* Bright Buttons with Gradient */
    .stButton>button {
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.8rem 2rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.6);
    }
    
    /* Metrics Styling */
    div[data-testid="metric-container"] {
        background-color: #1F2937;
        border-left: 5px solid #6366F1;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    label[data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
        font-size: 0.9rem;
    }
    
    div[data-testid="stMetricValue"] {
        color: #F3F4F6 !important;
        font-weight: 700;
    }
    
    /* Text Inputs */
    .stTextArea>div>div>textarea {
        background-color: #111827;
        color: #E5E7EB;
        border: 1px solid #374151;
        border-radius: 10px;
    }

    /* File Uploader */
    .stFileUploader {
        border: 2px dashed #4F46E5;
        border-radius: 12px;
        padding: 20px;
        background-color: rgba(79, 70, 229, 0.05);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #374151;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar (Sticky Logic) ---
with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/000000/resume.png", width=100)
    st.title("AI Analyzer Config")
    
    match_sensitivity = st.slider("Match Sensitivity", 0.0, 1.0, 0.5)
    
    # Real-time Readiness Score placeholder
    # In a real app, we'd recalc this on every keystroke if we wanted true RT, 
    # but that's heavy on resources. We'll simulate or use a lighter check.
    readiness_placeholder = st.empty()
    
    st.info(
        """
        **How to Use:**
        1. Upload Resume (PDF/DOCX)
        2. Paste Job Description
        3. Click 'Analyze Gap'
        """
    )
    st.markdown("---")
    st.caption("v2.0 | Powered by Spacy & Transformers")

# --- Main Layout ---
# --- Main Layout ---
st.title("🚀 AI-Powered Resume Analyzer")
st.markdown("<h3 style='text-align: center; color: #9CA3AF; font-weight: 400;'>Analyze gaps, optimize keywords, and boost your interview chances.</h3>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📂 Upload Resume")
    uploaded_file = st.file_uploader("Drop your resume here...", type=['pdf', 'docx'])

with col2:
    st.subheader("📋 Job Description Source")
    jd_source = st.radio("Input Type", ["Paste Text", "Job Post URL"], horizontal=True, label_visibility="collapsed")
    
    jd_text = ""
    if jd_source == "Paste Text":
        jd_text = st.text_area("Paste the JD here...", height=250)
    else:
        jd_url = st.text_input("Enter Job URL (LinkedIn, Indeed, Company Site)", placeholder="https://...")
        if jd_url:
            with st.spinner("Fetching Job Description..."):
                fetched = extractor.fetch_job_description(jd_url)
                if "Error" in fetched:
                    st.error(fetched)
                else:
                    st.success("JD Fetched Successfully!")
                    with st.expander("Preview Fetched JD"):
                        st.text(fetched[:500] + "...")
                    jd_text = fetched

# --- State Management ---
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

# --- Analysis Trigger ---
# --- Real-time Readiness Logic ---
if jd_text:
    # A simple length/keyword check for "Readiness" before full analysis
    # This keeps it fast for the sidebar
    word_count = len(jd_text.split())
    if word_count > 50:
         readiness_placeholder.metric("Readiness Score", "High", "Ready to Match")
    elif word_count > 20:
         readiness_placeholder.metric("Readiness Score", "Medium", "Keep adding details")
    else:
         readiness_placeholder.metric("Readiness Score", "Low", "Paste more content")

# --- Analysis Trigger ---
if st.button("Analyze Gap"):
    if uploaded_file and jd_text:
        with st.spinner("Processing Semantic Analysis..."):
            try:
                # 1. Parsing
                resume_text = extractor.parse_file(uploaded_file)
                
                if "Error" in resume_text:
                    st.error(resume_text)
                else:
                    # 1b. ATS Sanity Check (Feature A)
                    ats_check = extractor.analyze_ats_compliance(uploaded_file, resume_text)
                    
                    # 2. NLP Analysis
                    start = time.time()
                    match_score, category_scores, gap_data, r_skill_dict, jd_skill_dict = analyzer.analyze_gap(resume_text, jd_text)
                    
                    # 2b. Tone Analysis (Feature C)
                    r_tone, r_tone_scores = analyzer.analyze_tone(resume_text)
                    jd_tone, _ = analyzer.analyze_tone(jd_text)
                    
                    # 2c. Fluff Removal (New Feature)
                    fluff_items = analyzer.identify_irrelevant_content(resume_text, jd_text)
                    
                    # Generate Suggestions (Feature B)
                    # Flatten missing skills from gap_data
                    missing_skills_list = [item['Skill'] for item in gap_data if item['Status'] == 'Missing']
                    suggestions = analyzer.get_improvement_suggestions(missing_skills_list)
                    
                    end = time.time()
                    
                    # 3. Visualization
                    st.success(f"Analysis Complete in {round(end-start, 2)}s")
                    
                    # ATS Report (Direct Display)
                    visualizer.render_ats_report(ats_check)
                    st.markdown("---")
                        
                    # Metrics
                    r_time = visualizer.calculate_reading_time(resume_text)
                    total_match_count = sum([d['Match Count'] for d in category_scores.values()])
                    
                    st.markdown("### 📈 Match Metrics")
                    visualizer.display_metric_cards(match_score * 100, total_match_count, r_time)
                    
                    st.markdown("---")
                    
                    # Radar, Heatmap & Tone
                    st.subheader("📊 Semantic Deep Dive")
                    tab1, tab2, tab3 = st.tabs(["Skill Gap Visualizer", "Resume Heatmap", "Tone & Culture"])
                    
                    with tab1:
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            fig = visualizer.create_radar_chart(category_scores)
                            st.plotly_chart(fig, use_container_width=True)
                        with c2:
                            st.markdown("#### Skill Gap Details")
                            visualizer.render_gap_table(gap_data)
                            
                    with tab2:
                        st.markdown("**Resume Density Heatmap** (Orange = High Match)")
                        heatmap_html = visualizer.generate_heatmap_html(resume_text, r_skill_dict)
                        st.markdown(heatmap_html, unsafe_allow_html=True)
                        
                    with tab3:
                        visualizer.render_tone_analysis(r_tone, r_tone_scores, jd_tone)
                    
                    # Actionable Suggestions (Feature B) & Fluff Removal
                    # Two columns for "Add" vs "Remove"
                    st.markdown("---")
                    col_fix, col_fluff = st.columns(2)
                    
                    with col_fix:
                        visualizer.render_intelligent_fixes(suggestions)
                        
                    with col_fluff:
                        visualizer.render_fluff_removal(fluff_items)

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
                import traceback
                st.code(traceback.format_exc())

    else:
        st.warning("Please upload a resume and paste a job description first.")

