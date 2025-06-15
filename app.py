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
import re

# Normalize name function for checklist tracking
def normalize_name(name):
    return re.sub(r'\W+', '', name).lower()

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")

if st.button("🔄 Start Over"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.markdown("### ✉️ Enter your email to personalize your experience")
user_email = st.text_input("Your email address (we'll use this to save your session or send you your report)", "")
if user_email:
    st.session_state.user_email = user_email

st.markdown("### 🏢 Company Info")
st.session_state.company_name = st.text_input("Company Name", st.session_state.get("company_name", ""))
st.session_state.company_url = st.text_input("Company Website URL", st.session_state.get("company_url", ""))
st.session_state.country = st.text_input("Country", st.session_state.get("country", ""))
st.session_state.report_goal = st.multiselect("📊 Reporting Goals", ["EcoVadis", "VSME", "CSRD Prep", "GRI"], default=["EcoVadis"])

if st.session_state.get("company_url"):
    try:
        st.image(f"https://logo.clearbit.com/{st.session_state.company_url}", width=100)
    except:
        st.warning("Could not load logo from Clearbit")

lang = st.selectbox("🌐 Choose language", ["English", "Français", "Deutsch", "Español"])

for key in ['summaries', 'drafts', 'generated_metrics', 'checklist_progress']:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'summaries' else {}

uploaded_files = st.file_uploader("📄 Upload ESG documents (PDF, DOCX, XLSX)", accept_multiple_files=True)

st.markdown("### ✅ Prefilled Checklist by Reporting Goal")
goal_to_checklist = {
    "EcoVadis": ["Code of Conduct", "Supplier Policy", "Diversity & Inclusion", "Environmental Policy"],
    "CSRD Prep": ["Double Materiality Assessment", "Energy Audit", "GRI Alignment", "Sustainability Governance Policy"]
}
completed_count = 0
total_items = 0
for goal in st.session_state.report_goal:
    checklist = goal_to_checklist.get(goal, [])
    if checklist:
        st.markdown(f"**{goal} requirements:**")
        for item in checklist:
            key = f"progress_{goal}_{item}"
            normalized_docs = [normalize_name(doc['file']) for doc in st.session_state.summaries] + [normalize_name(k) for k in st.session_state.get("drafts", {}).keys()]
            is_checked = normalize_name(item) in normalized_docs
            if is_checked:
                completed_count += 1
            total_items += 1
            st.session_state.checklist_progress[key] = st.checkbox(item, value=is_checked, key=key)

if total_items:
    completion_rate = int((completed_count / total_items) * 100)
    st.progress(completion_rate, text=f"Checklist Completion: {completion_rate}%")

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

if st.session_state.summaries:
    completeness = len(st.session_state.summaries) / 5
    st.markdown("### 🔦 ESG Readiness")
    if completeness >= 1:
        st.success("🟢 Ready: You have uploaded all key documents.")
    elif completeness >= 0.6:
        st.warning("🟠 In Progress: You have uploaded most of the documents.")
    else:
        st.error("🔴 Incomplete: Please upload more ESG documents.")

if st.button("✨ Generate Missing Policies"):
    with st.spinner("Generating missing policy drafts..."):
        missing = [item for goal in st.session_state.report_goal for item in goal_to_checklist.get(goal, []) if normalize_name(item) not in [normalize_name(k) for k in st.session_state.get("drafts", {}).keys()]]
        for topic in missing:
            try:
                prompt = f"Create a basic draft of a {topic} for a company in {st.session_state.country} named {st.session_state.company_name}. Please base it only on credible sources. Translate to {lang}"
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
        doc = docx.Document()
        doc.add_heading(title, 0)
        doc.add_paragraph(text)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button(label=f"🗕️ Download {title}.docx", data=buffer, file_name=f"{title}.docx")

if st.button("📌 Refine KPIs"):
    with st.spinner("Refining ESG metrics and KPIs..."):
        goals = ", ".join(st.session_state.get("report_goal", []))
        prompt = f"Based on the existing uploaded content and goals ({goals}), refine and suggest 5 actionable ESG KPIs for the company {st.session_state.company_name} in {st.session_state.country}. Translate to {lang}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        st.session_state.generated_metrics = response.choices[0].message.content.strip()
        st.success("✅ Refined KPIs generated.")

if st.session_state.generated_metrics:
    st.markdown("### 📈 Recommended ESG Metrics and KPIs")
    st.text_area("Suggested KPIs", st.session_state.generated_metrics, height=250)

# Dashboard section (activated)
st.markdown("### 📊 ESG Report Summary Dashboard")
if st.session_state.summaries or st.session_state.drafts:
    uploaded_count = len(st.session_state.summaries)
    generated_count = len(st.session_state.drafts)
    total = uploaded_count + generated_count
    st.write(f"Documents uploaded: {uploaded_count}")
    st.write(f"Policies generated: {generated_count}")
    st.write(f"Checklist items total: {total_items}, Completed: {completed_count}")
else:
    st.info("Upload or generate documents to see summary dashboard.")
