import streamlit as st
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")
st.markdown("Create your first VSME or EcoVadis ESG report with AI guidance.")

# Onboarding Inputs
st.header("1. Company Information")
industry = st.selectbox("Select your industry", ["Manufacturing", "Retail", "Tech", "Healthcare", "Other"])
location = st.text_input("Country of operation", "Germany")
employees = st.slider("Number of employees", 1, 500, 180)
report_goal = st.multiselect("Reporting Goals", ["VSME Report", "EcoVadis Submission", "CSRD Prep"])

# Submit Button for Roadmap
if st.button("Generate ESG Roadmap"):
    with st.spinner("Generating roadmap using GPT-4o..."):
        prompt = f"""You are GingerBug, a sustainability assistant. Help a company in the {industry} sector with {employees} employees in {location} prepare for {', '.join(report_goal)}.
        Generate an 8-step ESG roadmap starting from onboarding to first report submission.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        roadmap = response['choices'][0]['message']['content']
        st.subheader("📋 Your ESG Roadmap")
        st.markdown(roadmap)

# Document Upload Guidance
st.header("2. Upload ESG-Related Documents")

if "VSME Report" in report_goal:
    st.markdown("**Recommended for VSME:** Upload invoices, HR policies, energy/waste data, org chart.")
if "EcoVadis Submission" in report_goal:
    st.markdown("**Recommended for EcoVadis:** Upload code of conduct, supplier policy, training reports, emissions data.")
if "CSRD Prep" in report_goal:
    st.markdown("**Recommended for CSRD Prep:** Upload risk analysis, governance structure, stakeholder engagement summaries, internal audits.")

uploaded_file = st.file_uploader("Upload a PDF, DOCX, or XLSX document", type=["pdf", "docx", "xlsx"])
if uploaded_file:
    st.info("File received. AI data extraction feature coming soon!")

st.markdown("---")
st.markdown("🚀 Powered by GPT-4o | GingerBug.ai")
