import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def calculate_reading_time(text):
    """
    Estimates reading time in minutes.
    Assumes average reading speed of 200 wpm.
    """
    word_count = len(text.split())
    minutes = word_count / 200
    return round(minutes, 2)

def create_radar_chart(category_scores):
    """
    Creates a Radar Chart comparing Resume vs Job Description across categories.
    """
    categories = list(category_scores.keys())
    
    # Extracting counts
    # We want to see how many valid keywords were found in each
    # However, 'Resume Score' in analyzer.py was (Intersection / JD_Total).
    # To plot "Strength" vs "Requirement", we need raw counts of skills found in each doc.
    # But analyzer.py returned 'Match Count' and 'Total Required' (JD count).
    # It didn't return 'Total Resume Skills' (including those NOT in JD).
    # Let's trust simpler 'Match Count' (Resume Coverage) vs 'Total Required' (JD Demand)
    # This shows how well the resume FITS the job, not generic strength.
    
    resume_values = [data['Match Count'] for data in category_scores.values()]
    jd_values = [data['Total Required'] for data in category_scores.values()]
    
    fig = go.Figure()

    # Job Requirement Trace (Red/Pink Neon)
    fig.add_trace(go.Scatterpolar(
        r=jd_values,
        theta=categories,
        fill='toself',
        name='Job Requirement',
        line=dict(color='#EC4899', width=3),
        fillcolor='rgba(236, 72, 153, 0.2)'
    ))

    # Resume Match Trace (Cyan/Teal Neon)
    fig.add_trace(go.Scatterpolar(
        r=resume_values,
        theta=categories,
        fill='toself',
        name='Resume Match',
        line=dict(color='#2DD4BF', width=3),
        fillcolor='rgba(45, 212, 191, 0.4)'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(resume_values), max(jd_values)) + 1],
                gridcolor='#374151',
                linecolor='#374151',
                tickfont=dict(color='#9CA3AF'),
            ),
            angularaxis=dict(
                tickfont=dict(color='#E5E7EB', size=12, weight='bold'),
                linecolor='#374151'
            ),
            bgcolor='rgba(17, 24, 39, 0.5)'  # Dark background for the chart area
        ),
        legend=dict(
            font=dict(color='#E5E7EB'),
            bgcolor='rgba(0,0,0,0)'
        ),
        title=dict(
            text="Semantic Skill Gap Analysis",
            font=dict(color='#F3F4F6', size=20)
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    return fig

def render_gap_table(gap_data):
    """
    Renders the skill gap table using Streamlit dataframe or HTML.
    """
    if not gap_data:
        st.info("No common skills or gaps detected based on current dictionaries.")
        return

    df = pd.DataFrame(gap_data)
    
    # Add icons for status
    def get_status_icon(status):
        return "✅" if status == "Found" else "❌"
    
    df['Status Icon'] = df['Status'].apply(get_status_icon)
    
    # Rearrange columns
    display_df = df[['Category', 'Skill', 'Importance', 'Status Icon']]
    
    st.table(display_df)

def display_metric_cards(match_percentage, match_count, reading_time):
    col1, col2, col3 = st.columns(3)
    col1.metric("Match Score", f"{match_percentage:.1f}%")
    col2.metric("Matching Keywords", match_count)
    col3.metric("Est. Reading Time", f"{reading_time} min")

def generate_heatmap_html(text, found_skills):
    """
    Generates an HTML string with highlighted keywords for the heatmap visibility.
    The gradient logic is simplified here to 2 levels: Found (Deep Orange) vs Normal (Text).
    For a true 'semantic density' map, we would need per-sentence embedding scoring, 
    but for this prompt, we highlight the 'high-value' matched terms.
    """
    # Flatten found skills set
    all_found_skills = set()
    for cat in found_skills:
        all_found_skills.update(found_skills[cat])
        
    # Sort by length descending to avoid partial replacements (e.g. replacing 'Java' inside 'Javascript')
    sorted_skills = sorted(list(all_found_skills), key=len, reverse=True)
    
    # We will do a case-insensitive replacement, but preserve original case in text
    # A simple way to do this with correct highlighting:
    
    highlighted_text = text
    
    for skill in sorted_skills:
        # Improve regex to support case-insensitive finding but replacing safely
        import re
        pattern = re.compile(re.escape(skill), re.IGNORECASE)
        # Use a bright teal/gold highlighting for better contrast on dark bg
        # Text color inside highlight is dark for readability
        replacement = f'<span style="background-color: #F59E0B; color: #1f2937; font-weight: bold; border-radius: 4px; padding: 2px 4px; box-shadow: 0 0 5px rgba(245, 158, 11, 0.5);">{skill}</span>'
        highlighted_text = pattern.sub(replacement, highlighted_text)
        
    return f"""
    <div style="
        font-family: 'Inter', sans-serif; 
        line-height: 1.8; 
        padding: 24px; 
        background-color: #1f2937; 
        color: #e5e7eb;
        border-radius: 12px; 
        border: 1px solid #374151;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.3);
        max-height: 500px; 
        overflow-y: auto;">
        {highlighted_text}
    </div>
    """

def render_ats_report(ats_report):
    """
    Renders the ATS Compliance Report with a Score Gauge and visual indicators.
    """
    # Calculate Score
    total_checks = len(ats_report)
    passed_checks = sum(1 for v in ats_report.values() if v['status'] == "Pass")
    ats_score = int((passed_checks / total_checks) * 100)
    
    st.markdown("### 🤖 ATS Compatibility Score")
    
    # Custom Container for ATS
    with st.container():
        c1, c2 = st.columns([1, 2])
        
        with c1:
            # Simple Circular Gauge for Score using Plotly
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = ats_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "ATS Score"},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': "#10B981"},  # Green
                    'bgcolor': "#1F2937",
                    'borderwidth': 2,
                    'bordercolor': "#374151",
                    'steps': [
                        {'range': [0, 50], 'color': '#EF4444'},
                        {'range': [50, 80], 'color': '#F59E0B'}],
                }
            ))
            fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.markdown("#### Check Details")
            # Grid layout for checks
            cols = st.columns(2)
            for i, (check, result) in enumerate(ats_report.items()):
                color = "#10B981" if result['status'] == "Pass" else "#F59E0B" if result['status'] == "Warning" else "#EF4444"
                icon = "✅" if result['status'] == "Pass" else "⚠️" if result['status'] == "Warning" else "❌"
                
                # HTML Card for each check
                with cols[i % 2]:
                    st.markdown(f"""
                        <div style="background-color: #1F2937; border-left: 4px solid {color}; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                            <div style="font-weight: bold; font-size: 0.9em; color: #E5E7EB;">{icon} {check}</div>
                            <div style="font-size: 0.8em; color: #9CA3AF;">{result['msg']}</div>
                        </div>
                    """, unsafe_allow_html=True)


def render_intelligent_fixes(suggestions):
    """
    Renders AI-Drafted Quick Fixes as copy-paste cards.
    """
    if not suggestions:
        return

    st.markdown("### ⚡ Smart Fixes (Actionable Content)")
    
    # Scrollable container CSS
    st.markdown("""
        <style>
        .fix-card {
            background-color: #111827;
            border: 1px solid #374151;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            transition: transform 0.2s;
        }
        .fix-card:hover {
            border-color: #6366F1;
            transform: translateX(5px);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Show only top 5-6 to avoid clutter, or put in a scrollbox
    # We'll use a container with a fixed max-height if possible, but standard streamlit is easier
    
    for i, sug in enumerate(suggestions):
        st.markdown(f"""
            <div class="fix-card">
                <div style="color: #A78BFA; font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">RECOMMENDATION #{i+1}</div>
                <div style="color: #E5E7EB; font-family: monospace;">{sug}</div>
            </div>
        """, unsafe_allow_html=True)


def render_fluff_removal(fluff_items):
    """
    Renders 'Cut the Fluff' as distinct warning cards.
    """
    if not fluff_items:
        return

    st.markdown("### ✂️ Optimization Candidates (Remove/Rewrite)")
    
    for item in fluff_items:
        score_pct = int(item['score'] * 100)
        # Red/Orange theme for removals
        st.markdown(f"""
            <div style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="color: #EF4444; font-weight: bold; font-size: 0.9rem;">⚠️ Low Relevance ({score_pct}%)</span>
                </div>
                <div style="color: #D1D5DB; font-style: italic; margin-bottom: 5px;">"{item['text']}"</div>
                <div style="color: #9CA3AF; font-size: 0.8rem;">👉 {item['suggestion']}</div>
            </div>
        """, unsafe_allow_html=True)

def render_tone_analysis(resume_tone, resume_scores, jd_tone):
    """
    Renders the Tone Analysis comparison.
    """
    st.markdown("#### 🎭 Tone & Culture Match")
    
    # Just show dominant tones first
    c1, c2 = st.columns(2)
    c1.info(f"Resume Tone: **{resume_tone}**")
    c2.success(f"JD Culture Vibe: **{jd_tone}**")
    
    # Simple Bar Chart for Resume Tone Distribution
    st.caption("Resume Tone Profile")
    tone_df = pd.DataFrame(list(resume_scores.items()), columns=['Tone', 'Score'])
    
    # Normalize for display
    tone_df['Score'] = tone_df['Score'] * 100
    
    fig = go.Figure(go.Bar(
        x=tone_df['Score'],
        y=tone_df['Tone'],
        orientation='h',
        marker=dict(
            color='#8B5CF6',
            line=dict(color='#7C3AED', width=1)
        )
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=200,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)
