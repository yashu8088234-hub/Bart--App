import streamlit as st
import time
from ai_core import run_ai

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
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
# LOGIC CHECKS (UNCHANGED LOGIC)
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
# STUNNING PREMIUM MINIMALIST CSS
# =========================================================
st.markdown("""<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}

.stApp {
    background: #0B0B0B;
}

.block-container {
    max-width: 680px !important;
    padding-top: 10% !important;
}

/* Premium Button Styling */
div.stButton > button {
    height: 70px !important;
    border-radius: 16px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
}

/* Staff Button: Velvet Red Glow */
div.stButton > button[key="staff_btn"] {
    background: linear-gradient(135deg, #1A0D0D 0%, #3A1010 100%) !important;
    color: #FF8F8F !important;
    box-shadow: 0 4px 20px rgba(192, 57, 43, 0.15) !important;
}
div.stButton > button[key="staff_btn"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(192, 57, 43, 0.3) !important;
    border-color: rgba(192, 57, 43, 0.4) !important;
}

/* Admin Button: Onyx Sleek */
div.stButton > button[key="mgmt_btn"] {
    background: linear-gradient(135deg, #161616 0%, #222222 100%) !important;
    color: #E0E0E0 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
}
div.stButton > button[key="mgmt_btn"]:hover {
    transform: translateY(-2px) !important;
    border-color: rgba(255,255,255,0.15) !important;
}

/* Form container */
div[data-testid="stForm"] {
    background: #111111 !important;
    border: 1px solid #222222 !important;
    border-radius: 16px !important;
    padding: 25px !important;
}
</style>""", unsafe_allow_html=True)

# =========================================================
# THE DISPLAY
# =========================================================

# Ultra-clean Brand Identity
st.markdown("<h1 style='text-align: center; font-size: 82px; font-weight: 900; color: #FFFFFF; margin-bottom: 0; letter-spacing: -3px;'>BART</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #C0392B; font-weight: 700; text-transform: uppercase; letter-spacing: 4px; margin-top: 0px;'>Jeddah • Coffee & Bites</p>", unsafe_allow_html=True)

st.write("##")

# Compact Action Center
col1, col2 = st.columns(2, gap="medium")

with col1:
    if st.button("👨‍💼 Floor Staff", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"🔒 Locked ({remaining}s)", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("📦 Management", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True

# Minimalist Dynamic Password Prompt
if st.session_state.show_mgmt_password:
    st.write("##")
    with st.form("pass_form", clear_on_submit=True):
        st.markdown("<p style='color: #888888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;'>Secure Admin Verification</p>", unsafe_allow_html=True)
        password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="••••••••")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.form_submit_button("Verify Identity", use_container_width=True):
                if password_input == st.secrets["MANAGER_PASSWORD"]:
                    st.session_state.show_mgmt_password = False
                    st.switch_page("pages/management_dashboard.py")
                else:
                    st.error("Access Denied")
        with c2:
            if st.form_submit_button("Cancel Layout", use_container_width=True):
                st.session_state.show_mgmt_password = False
                st.rerun()
