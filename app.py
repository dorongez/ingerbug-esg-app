import streamlit as st
from openai import OpenAI
import os
import io
import docx
from PyPDF2 import PdfReader
import pandas as pd
import base64
from fpdf import FPDF
import requests

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")

# Restart session
if st.button("🔄 Start Over"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Email
st.markdown("### ✉️ Your Email")
user_email = st.text_input("We'll use this to save your session or send reports", "")
if user_email:
    st.session_state.user_email = user_email

# Company Info
st.markdown("### 🏢 Company Info")
st.session_state.company_name = st.text_input("Company Name", st.session_state.get("company_name", ""))
st.session_state.company_url = st.text_input("Company Website URL", st.session_state.get("company_url", ""))
st.session_state.country = st.text_input("Country", st.session_state.get("country", ""))

# Logo
if st.session_state.get("company_url"):
    try:
        st.image(f"https://logo.clearbit.com/{st.session_state.company_url}", width=100)
    except:
        st.warning("Logo not found.")

# Reporting Goals
st.session_state.report_goal = st.multiselect(
    "📊 Reporting Goals",
    ["EcoVadis", "VSME", "CSRD Prep", "GRI"],
    default=["EcoVadis"]
)

# Language (placeholder)
lang = st.selectbox("🌐 Language", ["English", "Français", "Deutsch", "Español"])

# Session init
if 'summaries' not in st.session_state:
    st.session_state.summaries = []
if 'drafts' not in st.session_state:
    st.session_state.drafts = {}

# Upload files
uploaded_files = st.file_uploader("📤 Upload ESG-related documents (PDF, DOCX, XLSX)", accept_multiple_files=True)

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
        st.session_state.summaries.append({"file": file.name, "summary": summary})
        st.text_area(f"Summary - {file.name}", summary, height=150, key=f"summary_{file.name}")

# Traffic Light
if st.session_state.summaries:
    st.markdown("### 🔦 ESG Readiness")
    count = len(st.session_state.summaries)
    if count >= 5:
        st.success("🟢 Ready: All key documents uploaded.")
    elif count >= 3:
        st.warning("🟠 In Progress: Upload more ESG documents.")
    else:
        st.error("🔴 Incomplete: Please upload more.")

# Generate missing policies
if st.button("✨ Generate Missing Policies"):
    missing = ["Environmental Policy", "Code of Conduct", "Diversity & Inclusion Policy"]
    st.session_state.drafts = {}
    for topic in missing:
        prompt = f"Create a basic draft of a {topic} for a company in {st.session_state.country} named {st.session_state.company_name}."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        st.session_state.drafts[topic] = response.choices[0].message.content.strip()

if st.session_state.get("drafts"):
    st.markdown("## 📄 Drafted Policies")
    for title, text in st.session_state.drafts.items():
        st.text_area(f"{title}", text, height=200, key=f"draft_{title}")

# Export Full Report PDF
if st.button("📥 Export Full ESG Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Company: {st.session_state.get('company_name', '')}")
    pdf.multi_cell(0, 10, f"Email: {user_email}")
    pdf.multi_cell(0, 10, f"Country: {st.session_state.get('country', '')}")
    pdf.multi_cell(0, 10, f"Goals: {', '.join(st.session_state.get('report_goal', []))}")

    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, "📄 Document Summaries")
    pdf.set_font("Arial", size=12)
    for entry in st.session_state.summaries:
        pdf.multi_cell(0, 10, f"{entry['file']}\n{entry['summary']}\n")

    if st.session_state.drafts:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.multi_cell(0, 10, "📑 Generated Policies")
        pdf.set_font("Arial", size=12)
        for title, text in st.session_state.drafts.items():
            pdf.multi_cell(0, 10, f"{title}\n{text}\n")

    full_pdf = f"GingerBug_ESG_Report_{st.session_state.get('company_name', 'company')}.pdf"
    pdf.output(full_pdf)
    with open(full_pdf, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{full_pdf}">📥 Download Full ESG PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
