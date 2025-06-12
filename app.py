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
Choose how you'd like to begin your sustainability journey below.
""")

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
- Train
