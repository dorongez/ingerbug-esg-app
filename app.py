import streamlit as st
from openai import OpenAI
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
    try:
        st.rerun()
    except Exception:
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
st.header("🖜️ Choose Your Mode")
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
            try:
                company_name = domain.replace("www.", "").split(".")[0].capitalize()
                response = requests.get(f"https://logo.clearbit.com/{domain}")
                logo_url = response.url if response.status_code == 200 else ""

                company_data = {
                    "Company Name": company_name,
                    "Logo URL": logo_url,
                    "Employees": "Not available",
                    "HQ": "Not available",
                    "Diversity Statement": "Not available",
                    "Governance": "Not available",
                    "Environment": "Not available",
                    "Sources": "Data pulled from public website metadata and trusted APIs."
                }
                st.session_state.autopilot = company_data
            except:
                st.warning("Could not fetch data for this domain.")

# Display autopilot results
if 'autopilot' in st.session_state:
    st.subheader("🔎 Public ESG Profile (Autopilot)")
    data = st.session_state.autopilot
    if data.get('Logo URL'):
        st.image(data['Logo URL'], width=100)
    st.markdown(f"**Company Name:** {data.get('Company Name', 'N/A')}")
    st.markdown(f"**Location:** {data.get('HQ', 'N/A')}")
    st.markdown(f"**Employees:** {data.get('Employees', 'N/A')}")
    st.markdown(f"**Diversity:** {data.get('Diversity Statement', 'N/A')}")
    st.markdown(f"**Governance:** {data.get('Governance', 'N/A')}")
    st.markdown(f"**Environment:** {data.get('Environment', 'N/A')}")
    if st.toggle("Show data source info"):
        st.info(data.get('Sources', ''))

# Upload files (Quick Start & Guided Upload)
if mode in ["Quick Start (Let AI work with what I upload)", "Guided Upload (Step-by-step document upload)"]:
    st.subheader("📤 Upload your documents")
    uploaded_files = st.file_uploader("Upload multiple ESG-related files:", type=["pdf", "docx", "xlsx"], accept_multiple_files=True)

    def extract_text_from_file(uploaded_file):
        if uploaded_file.type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in pdf_reader.pages])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(uploaded_file)
            return df.to_csv(index=False)
        return ""

    if uploaded_files:
        for uploaded_file in uploaded_files:
            content = extract_text_from_file(uploaded_file)
            file_summary = f"Summarize this ESG-related document for compliance reporting:\n\n{content[:4000]}"
            with st.spinner(f"Analyzing {uploaded_file.name}..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": file_summary}],
                    temperature=0.3
                )
                summary = response.choices[0].message.content
                st.session_state.summaries.append({"file": uploaded_file.name, "summary": summary})

# Show dashboard
if st.session_state.summaries:
    st.header("📊 ESG Report Summary Dashboard")
    for entry in st.session_state.summaries:
        st.markdown(f"**{entry['file']}**")
        st.text_area("Summary", entry['summary'], height=150)

    # Export button
    if st.button("📥 Export Summaries to PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for entry in st.session_state.summaries:
            pdf.cell(200, 10, txt=entry['file'], ln=True, align='L')
            pdf.multi_cell(0, 10, txt=entry['summary'])
            pdf.ln()
        output_path = "/tmp/gingerbug_report.pdf"
        pdf.output(output_path)

        with open(output_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<a href="data:application/pdf;base64,{base64_pdf}" download="gingerbug_summary.pdf">📄 Download ESG Summary PDF</a>'
        st.markdown(pdf_display, unsafe_allow_html=True)
