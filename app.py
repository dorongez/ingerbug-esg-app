import streamlit as st
import openai
import os
import io
import docx
from PyPDF2 import PdfReader
import pandas as pd

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")

st.markdown("""Welcome to GingerBug, your AI-powered ESG reporting companion for VSME, EcoVadis, and CSRD prep. 
Choose how you'd like to begin your sustainability journey below.
""")

# Mode selection
st.header("🗌️ Choose Your Mode")
mode = st.radio("How would you like to start?", [
    "Quick Start (Let AI work with what I upload)",
    "Guided Upload (Step-by-step document upload)"
])

# Checklist view
with st.expander("📋 Beginner's Document Checklist (Click to view)"):
    st.markdown("#### VSME Report")
    st.markdown("""
- Invoices (electricity, water, waste) — PDF/XLSX  
- HR Data (gender ratio, contracts) — XLSX/DOCX  
- Org Chart — PDF/DOCX  
- Policies (HR, conduct) — PDF/DOCX  
- Facility List — XLSX  
    """)
    st.markdown("#### EcoVadis Submission")
    st.markdown("""
- Policies (ethics, environment) — PDF/DOCX  
- Supplier Policy — PDF/DOCX  
- Trainings — XLSX/PPTX  
- GHG Reports — XLSX/PDF  
    """)
    st.markdown("#### CSRD Preparation")
    st.markdown("""
- Risk Matrix — XLSX/DOCX  
- Governance Structure — PDF/DOCX  
- Stakeholder Engagement Summaries — PDF/DOCX  
- Internal Audit Files — PDF  
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
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        roadmap = response['choices'][0]['message']['content']
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

# Text extraction helpers
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_text_from_docx(uploaded_file):
    doc = docx.Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_xlsx(uploaded_file):
    dfs = pd.read_excel(uploaded_file, sheet_name=None)
    text = ""
    for sheet_name, df in dfs.items():
        text += f"--- Sheet: {sheet_name} ---\n"
        text += df.astype(str).to_string(index=False)
        text += "\n"
    return text

# File processing
st.header("3. Upload Multiple ESG Documents")
uploaded_files = st.file_uploader("Upload one or more PDF, DOCX, or XLSX files", type=["pdf", "docx", "xlsx"], accept_multiple_files=True)
summaries = []

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"🔍 Analyzing {uploaded_file.name}..."):
            file_text = ""
            name = uploaded_file.name.lower()
            if name.endswith(".pdf"):
                file_text = extract_text_from_pdf(uploaded_file)
            elif name.endswith(".docx"):
                file_text = extract_text_from_docx(uploaded_file)
            elif name.endswith(".xlsx"):
                file_text = extract_text_from_xlsx(uploaded_file)
            else:
                st.warning(f"{uploaded_file.name} skipped (unsupported type).")
                continue
            if file_text:
                gpt_prompt = f"""You are an ESG assistant. Analyze the document below. Summarize findings under the following headers:

### Environmental
(Write if any content is relevant here)

### Social
(Write if any content is relevant here)

### Governance
(Write if any content is relevant here)

--- Document Content Start ---

{file_text[:6000]}

--- Document Content End ---
"""
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": gpt_prompt}],
                    temperature=0.5
                )
                summary_text = response["choices"][0]["message"]["content"]
                summaries.append((uploaded_file.name, summary_text))
                st.subheader(f"📄 {uploaded_file.name} Summary")
                st.markdown(summary_text)

# Download
if summaries:
    st.markdown("### 📅 Download All Summaries")
    combined_text = "\n\n".join([f"===== {name} =====\n{content}" for name, content in summaries])
    st.download_button("Download .txt file", combined_text, file_name="gingerbug_esg_summaries.txt")

# Dashboard & Drafting
st.header("4. ESG Summary Review & Policy Drafts")
tab1, tab2, tab3 = st.tabs(["📁 Uploaded Files", "📄 GPT Drafts", "📊 Readiness & Gaps"])
file_labels = {}
drafts = {}
esg_scores = {}

with tab1:
    st.markdown("#### Label Uploaded Documents")
    for file_name, summary in summaries:
        label = st.text_input(f"Label for: {file_name}", placeholder="e.g. Code of Conduct, GHG Report")
        file_labels[file_name] = label

with tab2:
    st.markdown("#### Generate Missing ESG Policies")
    policy_needed = st.selectbox("Choose a missing policy to generate", [
        "Code of Conduct",
        "Supplier Code of Conduct",
        "Anti-Corruption Policy",
        "Environmental Policy",
        "Diversity & Inclusion Policy"
    ])
    if st.button("Generate Draft Policy"):
        draft_prompt = f"Generate a clear, professional {policy_needed} suitable for an SME starting ESG reporting. Include 3-5 bullet points in plain language."
        draft_response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": draft_prompt}],
            temperature=0.6
        )
        policy_text = draft_response["choices"][0]["message"]["content"]
        drafts[policy_needed] = policy_text
        st.markdown(f"##### 📄 {policy_needed}")
        st.text_area("Review and edit your policy draft below", value=policy_text, height=300)

with tab3:
    st.markdown("#### ESG Readiness Insights")
    for file_name, summary in summaries:
        score_prompt = f"""You are a sustainability compliance assistant. Based on this document summary, rate its usefulness for scoring in VSME, EcoVadis, or CSRD frameworks.

Provide scores (0-5) for:
- Environmental
- Social
- Governance

Document Summary:
{summary}
"""
        score_response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": score_prompt}],
            temperature=0.5
        )
        score_text = score_response["choices"][0]["message"]["content"]
        esg_scores[file_name] = score_text
        st.markdown(f"**{file_name}**")
        st.markdown(score_text)

st.markdown("---")
st.markdown("🚀 Powered by GPT-4o | GingerBug.ai")
