import streamlit as st
import os
import pandas as pd
from src.graph import app_graph
from src.tools import FileTools
from src.assets import ICONS, CSS_STYLES
from src.utils import ensure_directories_exist
from dotenv import load_dotenv

if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

#  Configuration
load_dotenv()
ensure_directories_exist()
st.set_page_config(page_title="CRIS Enterprise", page_icon="🩺", layout="wide")
st.markdown(CSS_STYLES, unsafe_allow_html=True)


with st.sidebar:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
        {ICONS['main_logo']}
        <div>
            <h2 style="margin: 0; font-size: 1.2rem; font-weight: 700;">CRIS System</h2>
            <span style="color: #64748b; font-size: 0.75rem; letter-spacing: 0.05em;">ENTERPRISE v2.2</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"""
    <div style="margin-bottom: 15px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 0.85rem; color: #64748b;">System Status</span>
            <span class="status-badge">{ICONS['secure']} Secure</span>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 0.85rem; color: #64748b;">AI Engine</span>
            <span style="font-size: 0.85rem; color: #10b981; font-weight: 600;">Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("Administration"):
        st.caption("Data Source: Internal Knowledge Graph")
        st.caption("Compliance: HIPAA / GDPR Ready")


st.markdown(f"""
<div class="header-container">
    <div style="display: flex; align-items: center; gap: 15px;">
        {ICONS['main_logo']}
        <div>
            <h1 style="margin: 0; font-size: 1.5rem; font-weight: 600;">Clinical Intelligence Workstation</h1>
            <p style="margin: 4px 0 0 0; color: #64748b; font-size: 0.9rem;">
                Multi-Modal Diagnostic Support & Pharmacological Analysis
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2], gap="medium")

# Session State
if "result" not in st.session_state: st.session_state.result = None
if "intent" not in st.session_state: st.session_state.intent = None


with col1:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
        {ICONS['dashboard']} <span style="font-weight: 600;">Case Intake</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        input_mode = st.radio("Select Modality", ["Clinical Notes", "Radiology / Labs"], horizontal=True, label_visibility="collapsed")
        
        user_input = ""
        image_data = None
        input_type = "text"
        
        if input_mode == "Clinical Notes":
            user_input = st.text_area("Case Notes", height=250, 
                placeholder="Patient ID: ---\nSymptoms:\n- \n\nQuery:")
        else:
            uploaded_file = st.file_uploader("Upload Medical Record (PDF/Image)", type=['pdf', 'png', 'jpg'])
            if uploaded_file:
                input_type = "file"
                if uploaded_file.type == 'application/pdf':
                    user_input = FileTools.extract_text_from_pdf(uploaded_file)
                    st.info("Document ready for analysis")
                else:
                    image_data = FileTools.process_image(uploaded_file)
                    st.image(image_data, use_container_width=True)

        if st.button("Run Clinical Analysis", use_container_width=True):
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("System Error: API Key Missing.")
            elif input_mode == "Clinical Notes" and not user_input.strip():
                st.warning("⚠️ Please enter clinical notes or a query before running analysis.")
            elif input_mode == "Radiology / Labs" and not uploaded_file:
                st.warning("⚠️ Please upload a medical image or PDF document.")
            else:
                with st.spinner("Processing Clinical Data..."):
                    try:
                        inputs = {"user_input": user_input, "input_type": input_type, "image_data": image_data}
                        response = app_graph.invoke(inputs)
                        st.session_state.result = response['structured_response']
                        st.session_state.intent = response['intent']
                    except Exception as e:
                        st.error(f"Analysis Failed: {str(e)}")


with col2:
    if st.session_state.result:
        data = st.session_state.result
        intent = st.session_state.intent
        
        with st.container(border=True):
            
            
            if intent == "medicine_info":
                # Header
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid #e2e8f0;">
                    {ICONS['medicine']}
                    <div>
                        <h2 style="margin:0; font-size: 1.4rem;">{data.get('name')}</h2>
                        <span style="color: #64748b; font-size: 0.9rem;">Brands: {data.get('brand_names', 'Generic')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([1.2, 1])
                
                with c1:
                    st.markdown(f"<div class='section-header'>{ICONS['clipboard']} Indications</div>", unsafe_allow_html=True)
                    for use in data.get('uses', []): 
                        st.markdown(f"• {use}")
                    
                    
                    st.markdown(f"<div class='section-header' style='margin-top: 20px;'>{ICONS['chart']} Dosage & Administration</div>", unsafe_allow_html=True)
                    st.info(data.get('dosage', 'Refer to package insert.'))

                    st.markdown(f"<div class='section-header' style='margin-top: 20px;'>{ICONS['warning']} Adverse Effects</div>", unsafe_allow_html=True)
                    st.write(", ".join(data.get('side_effects', [])))

                with c2:
                    st.markdown(f"<div class='section-header'>{ICONS['mechanism']} Mechanism of Action</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="background-color: #eff6ff; border: 1px solid #dbeafe; border-radius: 8px; padding: 16px; color: #1e40af; font-size: 0.95rem; line-height: 1.5;">
                        {data.get('mechanism')}
                    </div>
                    """, unsafe_allow_html=True)

                    
                    st.markdown(f"<div class='section-header' style='margin-top: 20px;'>{ICONS['check']} Lifestyle & Diet</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; color: #166534; font-size: 0.95rem;">
                        {data.get('lifestyle_diet', 'No specific restrictions.')}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown(f"""
                <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; display: flex; gap: 12px;">
                    {ICONS['warning']}
                    <div>
                        <strong style="color: #991b1b; font-size: 1rem;">Black Box Warning / Contraindications</strong>
                        <p style="margin: 4px 0 0 0; color: #7f1d1d; font-size: 0.9rem;">{data.get('warnings')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            
            elif intent == "diagnosis":
                title = data.get('title', data.get('condition', 'Clinical Assessment'))
                severity_color = "#22c55e" if data.get('severity') == 'Low' else "#eab308" if data.get('severity') == 'Moderate' else "#ef4444"
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #e2e8f0;">
                    {ICONS['radiology']}
                    <h2 style="margin:0; font-size: 1.4rem;">{title}</h2>
                    <span style="background:{severity_color}20; color:{severity_color}; padding:4px 12px; border-radius:99px; font-weight:600; font-size:0.8rem; margin-left:auto; border: 1px solid {severity_color}40;">
                        {data.get('severity', 'Standard').upper()} ACUITY
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
                    <strong style="color: #334155; display: block; margin-bottom: 4px;">Executive Summary</strong>
                    <span style="color: #475569;">{data.get('summary', data.get('description'))}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if data.get('findings'):
                        st.markdown(f"<div class='section-header'>{ICONS['search']} Key Clinical Findings</div>", unsafe_allow_html=True)
                        for f in data['findings']: st.markdown(f"• {f}")
                
                with col_b:
                    if data.get('interpretation'):
                        st.markdown(f"<div class='section-header'>{ICONS['brain']} Clinical Interpretation</div>", unsafe_allow_html=True)
                        st.info(data.get('interpretation'))

                if data.get('table_data'):
                    st.markdown(f"<div class='section-header'>{ICONS['chart']} Quantitative Analysis</div>", unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame(data['table_data']), hide_index=True, use_container_width=True)

                st.markdown(f"<div class='section-header' style='margin-top: 15px;'>{ICONS['check']} Recommended Management Protocol</div>", unsafe_allow_html=True)
                for rec in data.get('recommendations', []): 
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #e2e8f0; border-left: 4px solid #10b981; padding: 12px; margin-bottom: 8px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                        {rec}
                    </div>
                    """, unsafe_allow_html=True)
                
                
                if data.get('lifestyle'):
                    st.markdown(f"<div class='section-header' style='margin-top: 15px;'>{ICONS['medicine']} Lifestyle Modification</div>", unsafe_allow_html=True)
                    st.info(data.get('lifestyle'))

            
            elif intent == "test_info":
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                    {ICONS['procedure']}
                    <h2 style="margin:0; font-size: 1.4rem;">Procedure Guide: {data.get('test_name')}</h2>
                </div>
                """, unsafe_allow_html=True)
                st.info(f"**Clinical Indication:** {data.get('purpose')}")
                t1, t2, t3 = st.tabs(["Step-by-Step Protocol", "Patient Preparation", "Reference Ranges"])
                with t1: st.markdown(data.get('procedure'))
                with t2: st.markdown(data.get('preparation'))
                with t3: st.markdown(f"**Normal Limits:** {data.get('normal_range')}")

    else:
        
        st.markdown(f"""
        <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
            {ICONS['dashboard']}
            <h3 style="color: #64748b; margin-top: 20px;">Clinical Decision Support Ready</h3>
            <p>Select a modality on the left to begin analysis.</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class="custom-footer">
        CONFIDENTIALITY NOTICE: This system is a Clinical Decision Support Tool (CDST). Output validity must be verified by a licensed practitioner.
    </div>
""", unsafe_allow_html=True)
