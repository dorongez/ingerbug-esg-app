# GingerBug MVP - Streamlit App Prototype
# Required: streamlit, openai


import streamlit as st
import openai
import os


# Set your OpenAI API key
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


# Submit Button
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


# File Uploads (future step)
st.header("2. Upload ESG-Related Documents")
uploaded_file = st.file_uploader("Upload a PDF, DOCX, or XLSX", type=["pdf", "docx", "xlsx"])
if uploaded_file:
    st.info("File received. AI data extraction feature coming next!")


st.markdown("---")
st.markdown("🚀 Powered by GPT-4o | GingerBug.ai")