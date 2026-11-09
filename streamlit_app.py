
import streamlit as st
import pandas as pd
from io import BytesIO
import hashlib
from decimal import Decimal, InvalidOperation
import re

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Fintech Reconciliation",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# DASHBOARD STYLING
# --------------------------------------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    [data-testid="stMetric"] {
        background: #f5f8fc;
        border: 1px solid #e1e8f0;
        border-radius: 12px;
        padding: 18px;
    }

    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 700;
    }

    .dashboard-header {
        padding: 20px 0 15px 0;
    }

    .dashboard-subtitle {
        color: #64748b;
        font-size: 16px;
    }

    .status-banner {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 12px 18px;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        border-color: #2563eb;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:

    st.title("💳 Reconciliation")
    st.caption("Financial Operations Platform")

    st.divider()

    st.subheader("Workspace")

    page = st.radio(
        "Navigation",
        [
            "📊 Overview",
            "🔎 Transaction Review",
            "📁 Reports"
        ],
        label_visibility="collapsed",
