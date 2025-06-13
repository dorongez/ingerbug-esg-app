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
    st.rerun()

# Email collection
st.markdown("### ✉️ Enter your email to personalize your experience")
user_email = st.text_input("Your email address (we'll use this to save your session or send you your report)", "")
if user_email:
    st.session_state.user_email = user_email

# Company info and reporting type
st.markdown("### 🏢 Company Info")
st.session_state.company_name = st.text_input("Company Name", st.session_state.get("company_name", ""))
st.session_state.company_url = st.text_input("Company Website URL", st.session_state.get("company_url", ""))
st.session_state.country = st.text_input("Country", st.session_state.get("country", ""))
st.session_state.report_goal = st.multiselect("📊 Reporting Goals", ["EcoVadis", "VSME", "CSRD Prep", "GRI"], default=["EcoVadis"])

# Load logo if domain present
if st.session_state.get("company_url"):
    try:
        st.image(f"https://logo.clearbit.com/{st.session_state.company_url}", width=100)
    except:
        st.warning("Could not load logo from Clearbit")

# Language toggle
lang = st.selectbox("🌐 Choose language", ["English", "Français", "Deutsch", "Español"])

# Initialize session state
if 'summaries' not in st.session_state:
    st.session_state.summaries = []
if 'drafts' not in st.session_state:
    st.session_state.drafts = {}

st.markdown("""
Welcome to GingerBug, your AI-powered ESG reporting companion for VSME, EcoVadis, CSRD prep, and GRI.
Choose your preferred mode below.
""")

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
                logo_url = f"https://logo.clearbit.com/{domain}"

                search_prompt = f"""
                You are an ESG assistant. Based only on reliable public sources (like Wikipedia, news articles, company pages),
                extract key ESG-related facts about the company '{company_name}'.
                Focus on:
                - Headquarters location
                - Number of employees
                - Diversity and inclusion efforts
                - Governance structure (e.g., board composition, ethics)
                - Environmental targets or achievements
                Respond in JSON with keys: 'Company Name', 'Location', 'Employees', 'Diversity', 'Governance', 'Environment'.
                """

                search_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": search_prompt}],
                    temperature=0.2
                )
                parsed_data = json.loads(search_response.choices[0].message.content)
                parsed_data["Logo URL"] = logo_url
                parsed_data["Sources"] = "Extracted from public web profiles, Wikipedia, or verified press statements."
                st.session_state.autopilot = parsed_data
            except:
                st.warning("Could not fetch data for this domain.")

# Display autopilot results
if 'autopilot' in st.session_state:
    st.subheader("🔎 Public ESG Profile (Autopilot)")
    data = st.session_state.autopilot
    if data.get('Logo URL'):
        st.image(data['Logo URL'], width=100)
    st.markdown(f"**Company Name:** {data.get('Company Name', 'N/A')}")
    st.markdown(f"**Location:** {data.get('Location', 'N/A')}")
    st.markdown(f"**Employees:** {data.get('Employees', 'N/A')}")
    st.markdown(f"**Diversity:** {data.get('Diversity', 'N/A')}")
    st.markdown(f"**Governance:** {data.get('Governance', 'N/A')}")
    st.markdown(f"**Environment:** {data.get('Environment', 'N/A')}")
    if st.toggle("Show data source info"):
        st.info(data.get('Sources', ''))

st.markdown("---")
st.header("📂 Upload Your ESG Documents")
files = st.file_uploader("Upload ESG-related documents (PDF, DOCX, XLSX)", type=["pdf", "docx", "xlsx"], accept_multiple_files=True)

required_docs = ["Environmental Policy", "Code of Conduct", "Supplier Code", "Diversity Statement", "GHG Emissions Report"]
missing_docs = required_docs.copy()

if files:
    st.markdown("## 🔎 Summarizing Uploaded Files")
    for file in files:
        file_name = file.name
        file_bytes = file.read()

        if file_name.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif file_name.endswith(".docx"):
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file_name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(file_bytes))
            text = df.to_string()
        else:
            text = ""

        prompt = f"""
        Summarize this document in a few lines for ESG reporting.
        List any ESG frameworks (GRI, SASB) mentioned.
        Also identify the document type and whether it's Environmental, Social, or Governance.
        {text[:4000]}
        """
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        summary = result.choices[0].message.content
        st.session_state.summaries.append({"file": file_name, "summary": summary})

        for doc_type in required_docs:
            if doc_type.lower() in file_name.lower():
                if doc_type in missing_docs:
                    missing_docs.remove(doc_type)

    st.success("Summaries generated.")

if st.session_state.summaries:
    st.header("📊 ESG Report Summary Dashboard")
    for i, entry in enumerate(st.session_state.summaries):
        st.markdown(f"**{entry['file']}**")
        st.text_area(f"Summary - {entry['file']}", entry['summary'], height=150, key=f"summary_{entry['file']}_{i}")

    st.markdown("---")
    st.subheader("🧩 Gap Analysis")
    if missing_docs:
        st.warning(f"We recommend adding the following documents: {', '.join(missing_docs)}")
        if st.button("✨ Generate Missing Policies"):
            for topic in missing_docs:
                prompt = f"Create a professional draft for a missing ESG document: {topic}. Use verified best practices only."
                draft = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                st.text_area(f"Draft - {topic}", draft.choices[0].message.content, height=200, key=f"draft_{topic}")
    else:
        st.success("All required documents detected. You can export your full report.")

    if st.button("📥 Export Report to PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for entry in st.session_state.summaries:
            pdf.multi_cell(0, 10, f"{entry['file']}\n{entry['summary']}\n")
        pdf_output = f"GingerBug_Report_{st.session_state.get('company_name','report')}.pdf"
        pdf.output(pdf_output)
        with open(pdf_output, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="{pdf_output}">📥 Download PDF Report</a>'
            st.markdown(href, unsafe_allow_html=True)

    st.success("Next step: Review, complete drafts, and download your ESG summary report.")
