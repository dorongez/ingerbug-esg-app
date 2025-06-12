import streamlit as st
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")

st.markdown("""Welcome to GingerBug, your AI-powered ESG reporting companion for VSME, EcoVadis, and CSRD prep. 
Choose how you'd like to begin your sustainability journey below.
""")

# Mode selection
st.header("🧭 Choose Your Mode")
mode = st.radio("How would you like to start?", [
    "Quick Start (Let AI work with what I upload)",
    "Guided Upload (Step-by-step document upload)"
])

# Checklist view (always shown at start)
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

# Upload Area
st.header("2. Upload ESG-Related Documents")
if mode == "Quick Start (Let AI work with what I upload)":
    st.markdown("Upload any document you think might help. We'll analyze and extract useful ESG data.")
else:
    st.markdown("Step-by-step upload with category suggestions. You can skip any part.")

# Upload tips based on goals
if "VSME Report" in report_goal:
    st.markdown("**VSME Upload Hints:** Invoices, HR policies, org chart, facility list.")
if "EcoVadis Submission" in report_goal:
    st.markdown("**EcoVadis Upload Hints:** Code of conduct, supplier policy, training reports, emissions.")
if "CSRD Prep" in report_goal:
    st.markdown("**CSRD Upload Hints:** Risk matrix, stakeholder engagement, internal audits.")

uploaded_file = st.file_uploader("Upload a PDF, DOCX, or XLSX document", type=["pdf", "docx", "xlsx"])
if uploaded_file:
    st.info("File received. Document parsing and analysis coming next!")

st.markdown("---")
st.markdown("🚀 Powered by GPT-4o | GingerBug.ai")
