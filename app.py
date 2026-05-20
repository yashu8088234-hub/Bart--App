import streamlit as st
import time
from ai_core import run_ai

# =========================================================
# SYSTEM CONFIG
# =========================================================
st.set_page_config(
    page_title="BART Ops",
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
# PREMIUM INDUSTRIAL OPERATIONAL CSS
# =========================================================
st.markdown("""<style>
/* Clean system workspace reset */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}

/* Luxury Corporate Light Canvas */
.stApp {
    background: radial-gradient(ellipse at top, #FAF9F5 0%, #EFEBE4 100%);
}

/* Tight layout window optimized for functional tools */
.block-container {
    max-width: 580px !important;
    padding-top: 10% !important;
}

/* Master Button Layout & Physics Engine */
div.stButton > button {
    height: 76px !important;
    border-radius: 14px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

/* 👨‍💼 STAFF ENTRY BUTTON: COMMANDING GRAPHITE SHIELD */
div.stButton > button[key="staff_btn"] {
    background: #1C1B1A !important;
    color: #F5ECE3 !important;
    border: none !important;
    box-shadow: 0 10px 30px rgba(28, 27, 26, 0.15) !important;
}
div.stButton > button[key="staff_btn"]:hover {
    transform: translateY(-2px) !important;
    background: #2D2B2A !important;
    box-shadow: 0 15px 35px rgba(28, 27, 26, 0.25) !important;
}
div.stButton > button[key="staff_btn"]:active {
    transform: translateY(1px) !important;
}

/* 📦 MANAGEMENT BUTTON: STERLING BRUSHED METAL DEEP REACTION */
div.stButton > button[key="mgmt_btn"] {
    background: #FFFFFF !important;
    color: #1C1B1A !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important;
}
div.stButton > button[key="mgmt_btn"]:hover {
    transform: translateY(-2px) !important;
    color: #C0392B !important;
    border-color: #C0392B !important;
    box-shadow: 0 12px 25px rgba(192, 57, 43, 0.1) !important;
}
div.stButton > button[key="mgmt_btn"]:active {
    transform: translateY(1px) !important;
}

/* Locked Admin Button State Overrides */
div.stButton > button[key="mgmt_btn"]:disabled {
    background: rgba(0, 0, 0, 0.03) !important;
    color: #A09E9B !important;
    border-color: transparent !important;
    cursor: not-allowed !important;
    transform: none !important;
}

/* Security Frame Overlay */
div[data-testid="stForm"] {
    background: #FFFFFF !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 20px 40px rgba(0,0,0,0.06) !important;
}

/* Data Input Vault UI */
div[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    background-color: #FDFDFD !important;
    border: 1px solid #E2DFD9 !important;
    height: 50px !important;
    text-align: center !important;
    font-size: 16px !important;
    letter-spacing: 4px !important;
    font-weight: 700 !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #1C1B1A !important;
    box-shadow: 0 0 0 1px #1C1B1A !important;
}
</style>""", unsafe_allow_html=True)


# =========================================================
# INTERFACE LAYOUT
# =========================================================

# Clean Industrial Core Identity
st.markdown("<h1 style='text-align: center; font-size: 64px; font-weight: 900; color: #1C1B1A; margin-bottom: 0; letter-spacing: -2px;'>BART</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 11px; color: #7A7875; font-weight: 700; text-transform: uppercase; letter-spacing: 6px; margin-top: -5px;'>Operations Console • Internal Access Only</p>", unsafe_allow_html=True)

st.write("###")

# Symmetrical Execution Grid
col1, col2 = st.columns(2, gap="medium")

with col1:
    if st.button("Floor Control", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"SYS LOCK ({remaining}s)", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("HQ Admin", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True


# =========================================================
# SYSTEM SECURITY GATE
# =========================================================
if st.session_state.show_mgmt_password:
    st.write("##")
    with st.form("pass_form", clear_on_submit=True):
        st.markdown("<p style='text-align: center; color: #1C1B1A; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px;'>CRITICAL REGION AUTHENTICATION</p>", unsafe_allow_html=True)
        password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="••••••••")
        
        st.write("#")
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.form_submit_button("Abort System", use_container_width=True):
                st.session_state.show_mgmt_password = False
                st.rerun()
        with c2:
            if st.form_submit_button("Grant Access", use_container_width=True):
                if password_input == st.secrets["MANAGER_PASSWORD"]:
                    st.session_state.show_mgmt_password = False
                    st.switch_page("pages/management_dashboard.py")
                else:
                    st.error("Authentication Refused")
