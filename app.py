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

# Upload documents
uploaded_files = st.file_uploader("📄 Upload ESG documents (PDF, DOCX, XLSX)", accept_multiple_files=True)

def extract_text(file):
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.name.endswith(".xlsx") or file.name.endswith(".xls"):
        df = pd.read_excel(file)
        return df.to_string()
    else:
        return file.read().decode(errors="ignore")

def summarize_text(text):
    prompt = f"Summarize this ESG-related document content:\n{text[:3000]}"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

if uploaded_files:
    st.markdown("## 📝 Uploaded File Summaries")
    for file in uploaded_files:
        content = extract_text(file)
        summary = summarize_text(content)
        key_safe = file.name.replace("/", "_").replace(".", "_")
        st.session_state.summaries.append({"file": file.name, "summary": summary})
        st.text_area(f"Summary - {file.name}", summary, height=150, key=f"summary_{key_safe}_{len(st.session_state.summaries)}")

# Show traffic light indicator based on summary completeness
if st.session_state.summaries:
    completeness = len(st.session_state.summaries) / 5
    st.markdown("### 🔦 ESG Readiness")
    if completeness >= 1:
        st.success("🟢 Ready: You have uploaded all key documents.")
    elif completeness >= 0.6:
        st.warning("🟠 In Progress: You have uploaded most of the documents.")
    else:
        st.error("🔴 Incomplete: Please upload more ESG documents.")

# Generate missing policies with spinner and exception handling
if st.button("✨ Generate Missing Policies"):
    with st.spinner("Generating missing policy drafts..."):
        missing = ["Environmental Policy", "Code of Conduct", "Diversity & Inclusion Policy"]
        st.session_state.drafts = {}
        for i, topic in enumerate(missing):
            try:
                st.markdown(f"⏳ Generating: **{topic}**...")
                prompt = f"Create a basic draft of a {topic} for a company in {st.session_state.country} named {st.session_state.company_name}. Please base it only on credible sources."
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                st.session_state.drafts[topic] = response.choices[0].message.content.strip()
                st.success(f"✅ {topic} generated.")
            except Exception as e:
                st.error(f"⚠️ Failed to generate {topic}: {str(e)}")

if st.session_state.get("drafts"):
    st.markdown("## 📄 Drafted Policies")
    for title, text in st.session_state.drafts.items():
        key_safe = title.replace(" ", "_").replace("/", "_")
        st.text_area(f"{title}", text, height=200, key=f"draft_{key_safe}_{len(st.session_state.drafts)}")

# Enhanced full report export with UTF-8 support
class PDF(FPDF):
    def __init__(self):
        super().__init__()
        try:
            self.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
            self.set_font("DejaVu", size=12)
        except:
            self.set_font("Arial", size=12)

if st.button("📅 Export Full ESG Report"):
    with st.spinner("Bundling full ESG report..."):
        pdf = PDF()
        pdf.add_page()
        pdf.multi_cell(0, 10, f"Company: {st.session_state.get('company_name', '')}\nEmail: {user_email}\nCountry: {st.session_state.get('country', '')}\n")
        pdf.multi_cell(0, 10, f"Goals: {', '.join(st.session_state.get('report_goal', []))}\n")

        if 'autopilot' in st.session_state:
            pdf.set_font("DejaVu", "B", 12)
            pdf.multi_cell(0, 10, "Autopilot Profile")
            pdf.set_font("DejaVu", size=12)
            for k, v in st.session_state['autopilot'].items():
                if k != "Logo URL":
                    pdf.multi_cell(0, 10, f"{k}: {v}")

        pdf.add_page()
        pdf.set_font("DejaVu", "B", 12)
        pdf.multi_cell(0, 10, "Uploaded Document Summaries")
        pdf.set_font("DejaVu", size=12)
        for entry in st.session_state.summaries:
            safe_summary = entry['summary'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, f"{entry['file']}\n{safe_summary}\n")

        if st.session_state.drafts:
            pdf.add_page()
            pdf.set_font("DejaVu", "B", 12)
            pdf.multi_cell(0, 10, "Generated Policies")
            pdf.set_font("DejaVu", size=12)
            for topic, content in st.session_state.drafts.items():
                safe_content = content.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, f"{topic}\n{safe_content}\n")

        full_pdf_name = f"GingerBug_Full_Report_{st.session_state.get('company_name', 'report')}.pdf"
        pdf.output(full_pdf_name)

        with open(full_pdf_name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="{full_pdf_name}">📅 Download Full ESG PDF</a>'
            st.markdown(href, unsafe_allow_html=True)

# Dashboard section
st.markdown("### 📊 ESG Report Summary Dashboard")
if st.session_state.summaries:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Uploaded Documents", len(st.session_state.summaries))
        st.metric("Generated Policies", len(st.session_state.drafts))
    with col2:
        st.markdown("**Reporting Goals:**")
        for goal in st.session_state.report_goal:
            st.markdown(f"- ✅ {goal}")

    st.markdown("---")
    st.markdown("**Next Steps:**")
    st.markdown("1. Upload missing documents based on your reporting goal")
    st.markdown("2. Finalize your policies (review and export)")
    st.markdown("3. Use the generated full report for your ESG submission or as a draft")
