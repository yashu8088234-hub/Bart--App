import streamlit as st
import time
from ai_core import run_ai

# =========================================================
# SYSTEM CONFIG
# =========================================================
st.set_page_config(
    page_title="BART Portal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# SESSION STATE (UNCHANGED LOGIC)
# =========================================================
st.session_state.authenticated = True

if "chat" not in st.session_state: st.session_state.chat = []
if "all_data" not in st.session_state: st.session_state.all_data = []
if "branches" not in st.session_state: st.session_state.branches = []
if "DAILY_ITEMS" not in st.session_state: st.session_state.DAILY_ITEMS = {}
if "WEEKLY_ITEMS" not in st.session_state: st.session_state.WEEKLY_ITEMS = {}
if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0

# =========================================================
# CORE LOGIC CHECKS (UNCHANGED LOGIC)
# =========================================================
def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

def data_missing():
    return (
        not st.session_state.all_data
        and not st.session_state.branches
        and not st.session_state.DAILY_ITEMS
        and not st.session_state.WEEKLY_ITEMS
    )

# =========================================================
# REFINED BRAND BRAND COLOR CSS
# =========================================================
st.markdown("""<style>
/* Reset boilerplate elements */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}

/* Pure Minimalist Tech White Background */
.stApp {
    background-color: #FFFFFF;
    font-family: 'Inter', system-ui, sans-serif;
}

/* Perfect container alignment based on premium SaaS layouts */
.block-container {
    max-width: 900px !important;
    padding-top: 5rem !important;
    padding-bottom: 5rem !important;
}

/* --- THE SYSTEM MODULES / CARD CONTAINER --- */
div[data-testid="stVerticalBlock"] > div:has(div.card-wrapper) {
    background-color: #F8F9FA !important;
    border-radius: 20px !important;
    padding: 30px !important;
    border: 1px solid #ECEFF1 !important;
}

/* --- BUTTON ARCHITECTURE --- */
div.stButton > button {
    height: 54px !important;
    border-radius: 50px !important; /* Premium Atlas Pill Style */
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: -0.2px !important;
    transition: all 0.2s ease-in-out !important;
}

/* Pill 1: Your Deep Charcoal/Crimson Combo (Floor Staff Button) */
div.stButton > button[key="staff_btn"] {
    background: linear-gradient(135deg, #2C2A28, #C0392B) !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(192, 57, 43, 0.2) !important;
}
div.stButton > button[key="staff_btn"]:hover {
    transform: translateY(-2px) !important;
    opacity: 0.95 !important;
    box-shadow: 0 6px 20px rgba(192, 57, 43, 0.35) !important;
}

/* Pill 2: Your Brand Outline Style (Management HQ Button) */
div.stButton > button[key="mgmt_btn"] {
    background: transparent !important;
    color: #C0392B !important;
    border: 2px solid #C0392B !important;
}
div.stButton > button[key="mgmt_btn"]:hover {
    transform: translateY(-2px) !important;
    background: #C0392B !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 20px rgba(192, 57, 43, 0.25) !important;
}

/* Locked Admin State Styling */
div.stButton > button[key="mgmt_btn"]:disabled {
    background: #F1F3F5 !important;
    color:
