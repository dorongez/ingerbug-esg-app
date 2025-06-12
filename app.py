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
from fpdf import FPDF
import requests

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

# Autopilot mode
if mode == "Go Autopilot (Auto-scan from website)":
    st.subheader("🌐 Autopilot ESG Scan")
    domain = st.text_input("Enter your company website URL (e.g., example.com)")
    if st.button("Go Autopilot") and domain:
        with st.spinner("Scanning public ESG data..."):
            company_data = {
    "Company Name": domain,
    "Logo URL": f"https://logo.clearbit.com/{domain}",
    "Employees": "Not available",
    "HQ": "Not available",
    "Diversity Statement": "Not available",
    "Governance": "Not available",
    "Environment": "Not available"
}
            st.session_state.autopilot = company_data

if 'autopilot' in st.session_state:
    st.subheader("🔎 Public ESG Profile (Autopilot)")
    data = st.session_state.autopilot
    st.image(data['Logo URL'], width=100)
    st.markdown(f"**Company Name:** {data['Company Name']}")
    st.markdown(f"**Location:** {data['HQ']}")
    st.markdown(f"**Employees:** {data['Employees']}")
    st.markdown(f"**Diversity:** {data['Diversity Statement']}")
    st.markdown(f"**Governance:** {data['Governance']}")
    st.markdown(f"**Environment:** {data['Environment']}")

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

# File upload section
st.subheader("📂 Uploaded File Preview")
uploaded_files = st.file_uploader("Upload your ESG-related documents", accept_multiple_files=True)

def create_pdf(summary_list):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="GingerBug - ESG Summary Report", ln=True, align="C")
    pdf.ln(10)
    for idx, text in enumerate(summary_list):
        pdf.multi_cell(0, 10, txt=f"{idx+1}. {text}")
        pdf.ln(2)
    return pdf.output(dest="S").encode("latin1")

# Display uploaded content
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
        st.session_state.summaries.append(f"Summary for {file.name}")

# Download button for PDF
if st.session_state.summaries:
    pdf_data = create_pdf(st.session_state.summaries)
    st.download_button("📥 Download ESG Summary Report (PDF)", pdf_data, file_name="GingerBug_ESG_Summary.pdf")

# ESG Progress Dashboard
st.subheader("📊 ESG Progress Dashboard")
goals = {
    "VSME Report": ["Invoices", "HR Data", "Org Chart", "Policies", "Facility List"],
    "EcoVadis Submission": ["Policies", "Supplier Policy", "Trainings", "GHG Reports"],
    "CSRD Prep": ["Risk Matrix", "Governance Structure", "Stakeholder Engagement", "Internal Audit Files"]
}

progress_data = {}
for goal in report_goal:
    completed = 0
    total = len(goals[goal])
    for doc in goals[goal]:
        if any(doc.lower() in f.name.lower() for f in uploaded_files):
            completed += 1
    progress = int((completed / total) * 100)
    progress_data[goal] = progress
    st.markdown(f"**{goal}**")
    st.progress(progress, text=f"{completed} of {total} documents uploaded")

# Traffic light ESG score (placeholder logic)
st.subheader("🚦 ESG Readiness Indicator")
if uploaded_files:
    file_score = len(uploaded_files)
    if file_score > 5:
        st.success("🟢 High Readiness: Great job! You're on track.")
    elif file_score > 2:
        st.warning("🟡 Medium Readiness: You're making progress.")
    else:
        st.error("🔴 Low Readiness: Let’s gather more documents to complete your ESG profile.")
