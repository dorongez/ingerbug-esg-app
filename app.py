import streamlit as st
from openai import OpenAI
import openai
import os
import io
import docx
import json
from PyPDF2 import PdfReader
import pandas as pd
import base64
from collections import defaultdict

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")

# Restart button
if st.button("🔄 Start Over"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# Email collection
st.markdown("### ✉️ Enter your email to personalize your experience")
user_email = st.text_input("Your email address (we'll use this to save your session or send you your report)", "")
if user_email:
    st.session_state.user_email = user_email

# Language toggle
lang = st.selectbox("🌐 Choose language", ["English", "Français", "Deutsch", "Español"])

# Load session state
if 'summaries' not in st.session_state:
    st.session_state.summaries = []
if 'drafts' not in st.session_state:
    st.session_state.drafts = {}

st.markdown("""Welcome to GingerBug, your AI-powered ESG reporting companion for VSME, EcoVadis, and CSRD prep.

Choose how you'd like to begin your sustainability journey below.""")

# Mode selection
st.header("🗜️ Choose Your Mode")
mode = st.radio("How would you like to start?", [
    "Quick Start (Let AI work with what I upload)",
    "Guided Upload (Step-by-step document upload)",
    "Go Autopilot (Auto-scan from website)"
])

# Checklist view
with st.expander("📋 Beginner's Document Checklist (Click to view)"):
    st.markdown("#### VSME Report")
    st.markdown("""
- Invoices (electricity, water, waste) -- PDF/XLSX  
- HR Data (gender ratio, contracts) -- XLSX/DOCX  
- Org Chart -- PDF/DOCX  
- Policies (HR, conduct) -- PDF/DOCX  
- Facility List -- XLSX  
    """)
    st.markdown("#### EcoVadis Submission")
    st.markdown("""
- Policies (ethics, environment) -- PDF/DOCX  
- Supplier Policy -- PDF/DOCX  
- Trainings -- XLSX/PPTX  
- GHG Reports -- XLSX/PDF  
    """)
    st.markdown("#### CSRD Preparation")
    st.markdown("""
- Risk Matrix -- XLSX/DOCX  
- Governance Structure -- PDF/DOCX  
- Stakeholder Engagement Summaries -- PDF/DOCX  
- Internal Audit Files -- PDF  
    """)

# Company Info
st.header("1. Company Information")
industry = st.selectbox("Industry", ["Manufacturing", "Retail", "Tech", "Healthcare", "Other"])
location = st.text_input("Country of operation", "Germany")
employees = st.slider("Number of employees", 1, 500, 180)
report_goal = st.multiselect("Reporting Goals", ["VSME Report", "EcoVadis Submission", "CSRD Prep"])

# Roadmap Generation
if st.button("Generate ESG Roadmap"):
    with st.spinner("Generating roadmap using GPT..."):
        prompt = f"You are GingerBug, a sustainability assistant. Help a company in the {industry} sector with {employees} employees in {location} prepare for {', '.join(report_goal)}. Generate an 8-step ESG roadmap."
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            roadmap = response.choices[0].message.content
            st.session_state.roadmap = roadmap
        except Exception as e:
            roadmap = f"⚠️ Error: {str(e)}"
            st.session_state.roadmap = roadmap

if 'roadmap' in st.session_state:
    st.subheader("📋 Your ESG Roadmap")
    st.markdown(st.session_state.roadmap)

# Autopilot Mode
if mode == "Go Autopilot (Auto-scan from website)":
    st.subheader("🌐 Enter Your Company Website")
    website_url = st.text_input("Company Website (e.g., https://example.com)")
    show_sources = st.checkbox("🔍 Show Source Details and Confidence Levels", value=True)
    if st.button("🚀 Go Autopilot") and website_url:
        with st.spinner("Scanning online presence and generating ESG draft..."):
            autopilot_prompt = f"""
You are GingerBug, a smart ESG assistant.
Based only on the public web presence of the company at: {website_url}, simulate the following:

1. Extract the company name, logo URL, address, and employee estimate
2. List 3–5 factual company bio points (industry, mission, values, etc.)
3. Any ESG-related policies or values likely found on the site
4. Mentions of certifications, initiatives, or stakeholder engagement
5. Environmental claims, climate goals, renewable energy use, emissions disclosures if any
6. Social responsibility indicators such as employee well-being, DEI, community projects
7. Governance practices or leadership ethics, diversity on board, anti-bribery if mentioned
8. A first-draft ESG report based on this simulated data

Also:
- Show the logo using markdown if found.
- Identify which indicators align with EcoVadis or CSRD if possible.
- Add confidence level (high/medium/low) per datapoint.
- If sources like press releases or social media are referenced, note them.

Format clearly with markdown. Keep it readable and structured.
{"Include all source details and confidence levels." if show_sources else "Keep summary short and exclude source details."}
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": autopilot_prompt}],
                    temperature=0.6
                )
                autopilot_output = response.choices[0].message.content
                st.subheader("📄 Simulated ESG Draft")
                st.markdown(autopilot_output)
                st.download_button("📥 Download ESG Draft", autopilot_output, file_name="Simulated_ESG_Report.txt")
            except Exception as e:
                st.error(f"⚠️ Autopilot failed: {str(e)}")

# File preview section for uploads
st.subheader("📂 Uploaded File Preview")
uploaded_files = st.file_uploader("Upload your ESG-related documents", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        st.markdown(f"**Filename:** {file.name}")
        if file.type == "application/pdf":
            pdf = PdfReader(file)
            st.text("\n".join(page.extract_text()[:500] for page in pdf.pages[:1]))
        elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            doc = docx.Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
            st.text(text[:500])
        elif file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            df = pd.read_excel(file)
            st.dataframe(df.head())
        else:
            content = file.read().decode(errors="ignore")
            st.text(content[:500])

# Traffic light ESG score (placeholder logic)
st.subheader("🚦 ESG Readiness Indicator")
if len(uploaded_files) > 0:
    file_score = len(uploaded_files)
    if file_score > 5:
        st.success("🟢 High Readiness: Great job! You're on track.")
    elif file_score > 2:
        st.warning("🟡 Medium Readiness: You're making progress.")
    else:
        st.error("🔴 Low Readiness: Let’s gather more documents to complete your ESG profile.")
