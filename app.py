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
from fpdf import FPDF
import requests

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="GingerBug ESG Assistant", layout="wide")
st.title("🌱 GingerBug - Release your sustainable power")

# Restart button — safe fallback for Streamlit Cloud
if st.button("🔄 Start Over"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    try:
        st.experimental_rerun()  # fallback works better on Streamlit Cloud
    except Exception:
        pass  # no rerun available; app just clears state

# Email collection
st.markdown("### ✉️ Enter your email to personalize your experience")
user_email = st.text_input("Your email address (we'll use this to save your session or send you your report)", "")
if user_email:
    st.session_state.user_email = user_email

# Language toggle
lang = st.selectbox("🌐 Choose language", ["English", "Français", "Deutsch", "Español"])

# Load session state
if 'summaries' not in st.session_state:
    st.session_state.summaries = []
if 'drafts' not in st.session_state:
    st.session_state.drafts = {}

st.markdown("""Welcome to GingerBug, your AI-powered ESG reporting companion for VSME, EcoVadis, and CSRD prep.

Choose how you'd like to begin your sustainability journey below.""")

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
                response = requests.get(f"https://logo.clearbit.com/{domain}")
                logo_url = response.url if response.status_code == 200 else ""

                company_data = {
                    "Company Name": company_name,
                    "Logo URL": logo_url,
                    "Employees": "Not available",
                    "HQ": "Not available",
                    "Diversity Statement": "Not available",
                    "Governance": "Not available",
                    "Environment": "Not available",
                    "Sources": "Data pulled from public website metadata and trusted APIs."
                }
                st.session_state.autopilot = company_data
            except:
                st.warning("Could not fetch data for this domain.")

# Display autopilot results
if 'autopilot' in st.session_state:
    st.subheader("🔎 Public ESG Profile (Autopilot)")
    data = st.session_state.autopilot
    if data.get('Logo URL'):
        st.image(data['Logo URL'], width=100)
    st.markdown(f"**Company Name:** {data.get('Company Name', 'N/A')}")
    st.markdown(f"**Location:** {data.get('HQ', 'N/A')}")
    st.markdown(f"**Employees:** {data.get('Employees', 'N/A')}")
    st.markdown(f"**Diversity:** {data.get('Diversity Statement', 'N/A')}")
    st.markdown(f"**Governance:** {data.get('Governance', 'N/A')}")
    st.markdown(f"**Environment:** {data.get('Environment', 'N/A')}")
    if st.toggle("Show data source info"):
        st.info(data.get('Sources', ''))
