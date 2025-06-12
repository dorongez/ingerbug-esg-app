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

# Email collection
st.markdown("### ✉️ Enter your email to personalize your experience")
user_email = st.text_input("Your email address (we'll use this to save your session or send you your report)", "")
if user_email:
    st.session_state.user_email = user_email

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

# Full Autopilot Ginger Mode
if mode == "Go Autopilot (Auto-scan from website)":
    st.subheader("🌐 Enter Your Company Website")
    website_url = st.text_input("Company Website (e.g., https://example.com)")
    if st.button("🔍 Start Full Autopilot") and website_url:
        with st.spinner("Scanning online presence and generating ESG draft..."):
            autopilot_prompt = f"""
            You are GingerBug, a smart ESG assistant.
            Based only on the public web presence of the company at: {website_url}, simulate the following:

            1. Company overview (industry, employee estimate, location)
            2. Any ESG-related policies or values likely found on the site
            3. Mentions of certifications, initiatives, or stakeholder engagement
            4. A first-draft ESG report based on this simulated data
            
            Format the answer with clear headings.
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

# File Upload
st.header("2. Upload ESG-Related Documents")
if mode == "Quick Start (Let AI work with what I upload)":
    st.markdown("Upload any document you think might help. We'll analyze and extract useful ESG data.")
else:
    st.markdown("Step-by-step upload with category suggestions. You can skip any part.")

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
                gpt_prompt = f"You are an ESG assistant. Based on this document, provide:\n1. A concise ESG summary\n2. Categorize it as Environmental, Social, Governance, or Other\n3. Mention any missing key policies or documents.\n4. If missing, suggest a brief draft outline.\n\nDocument content:\n{text[:4000]}"
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": gpt_prompt}],
                        temperature=0.3
                    )
                    summary = response.choices[0].message.content
                    st.session_state.summaries.append((uploaded_file.name, summary))

                    st.markdown(f"**AI Summary for {uploaded_file.name}:**")
                    st.write(summary)

                    if "suggest a brief draft outline" in gpt_prompt.lower():
                        st.markdown("✅ **Policy suggestion detected**. You can convert this into a full draft below.")
                        if st.button(f"✍️ Generate full draft for {uploaded_file.name}"):
                            draft_prompt = f"Generate a full ESG policy draft based on this summary: {summary}"
                            draft_response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": draft_prompt}],
                                temperature=0.5
                            )
                            draft_text = draft_response.choices[0].message.content
                            st.session_state.drafts[uploaded_file.name] = draft_text
                            st.markdown("**✍️ Draft Policy:**")
                            st.text_area("Edit your draft below:", draft_text, height=300)

                except Exception as e:
                    st.error(f"⚠️ An error occurred: {str(e)}")

# Export all summaries + drafts
if st.session_state.summaries or st.session_state.drafts:
    st.header("📤 Export Your Work")
    export_text = ""
    for name, summary in st.session_state.summaries:
        export_text += f"## {name} Summary\n{summary}\n\n"
    for name, draft in st.session_state.drafts.items():
        export_text += f"## {name} Draft Policy\n{draft}\n\n"
    b64_export = base64.b64encode(export_text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64_export}" download="ESG_Report_and_Policies.txt">📥 Download Full Report</a>'
    st.markdown(href, unsafe_allow_html=True)
