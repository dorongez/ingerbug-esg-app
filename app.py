import streamlit as st
from openai import OpenAI
import os
import io
import docx
from PyPDF2 import PdfReader
import pandas as pd

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")

st.markdown("""Welcome to GingerBug, your AI-powered ESG reporting companion for VSME, EcoVadis, and CSRD prep.

Choose how you'd like to begin your sustainability journey below.""")

# Mode selection
st.header("🗜️ Choose Your Mode")
mode = st.radio("How would you like to start?", [
    "Quick Start (Let AI work with what I upload)",
    "Guided Upload (Step-by-step document upload)"
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

# Onboarding fields
st.header("1. Company Information")
industry = st.selectbox("Industry", ["Manufacturing", "Retail", "Tech", "Healthcare", "Other"])
location = st.text_input("Country of operation", "Germany")
employees = st.slider("Number of employees", 1, 500, 180)
report_goal = st.multiselect("Reporting Goals", ["VSME Report", "EcoVadis Submission", "CSRD Prep"])

# Submit Button for Roadmap
if st.button("Generate ESG Roadmap"):
    with st.spinner("Generating roadmap using GPT-4o..."):
        prompt = f"""You are GingerBug, a sustainability assistant. Help a company in the {industry} sector with {employees} employees in {location} prepare for {', '.join(report_goal)}.
Generate an 8-step ESG roadmap starting from onboarding to first report submission."""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        roadmap = response.choices[0].message.content
        st.subheader("📋 Your ESG Roadmap")
        st.markdown(roadmap)

# Upload hints
st.header("2. Upload ESG-Related Documents")
if mode == "Quick Start (Let AI work with what I upload)":
    st.markdown("Upload any document you think might help. We'll analyze and extract useful ESG data.")
else:
    st.markdown("Step-by-step upload with category suggestions. You can skip any part.")
if "VSME Report" in report_goal:
    st.markdown("**VSME Upload Hints:** Invoices, HR policies, org chart, facility list.")
if "EcoVadis Submission" in report_goal:
    st.markdown("**EcoVadis Upload Hints:** Code of conduct, supplier policy, training reports, emissions.")
if "CSRD Prep" in report_goal:
    st.markdown("**CSRD Upload Hints:** Risk matrix, stakeholder engagement, internal audits.")

# File uploader and processing
st.header("3. Upload Files")
uploaded_files = st.file_uploader("Upload your ESG-related documents", type=["pdf", "docx", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_details = {"filename": uploaded_file.name, "type": uploaded_file.type, "size": uploaded_file.size}
        st.write(file_details)

        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(uploaded_file)
            text = df.to_string()
        else:
            text = "Unsupported file type."

        if text:
            with st.spinner("Analyzing file with GPT..."):
                gpt_prompt = f"You are an ESG assistant. Summarize the ESG-relevant contents of this document:\n{text[:4000]}"
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": gpt_prompt}],
                    temperature=0.3
                )
                summary = response.choices[0].message.content
                st.markdown("**AI Summary:**")
                st.write(summary)
