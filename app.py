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
# SESSION STATE
# =========================================================
st.session_state.authenticated = True

if "chat" not in st.session_state: st.session_state.chat = []
if "all_data" not in st.session_state: st.session_state.all_data = []
if "branches" not in st.session_state: st.session_state.branches = []
if "DAILY_ITEMS" not in st.session_state: st.session_state.DAILY_ITEMS = {}
if "weekly_items" not in st.session_state: st.session_state.WEEKLY_ITEMS = {}
if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# CSS: CHARCOAL & RED METALLIC GLOW
# =========================================================
st.markdown("""<style>
/* Reset */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important;}

.stApp {background-color: #FFFFFF; font-family: 'Inter', system-ui, sans-serif;}
.block-container {max-width: 900px !important; padding-top: 5rem !important;}

/* --- BUTTON ARCHITECTURE (Red Base -> Charcoal Hover) --- */
div.stButton > button {
    height: 54px !important;
    border-radius: 50px !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    background: #FF0033 !important; /* RED BASE */
    border: 2px solid #FF0033 !important;
    color: #FFFFFF !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
}

div.stButton > button:hover {
    background: #1C1D22 !important; /* CHARCOAL HOVER */
    border-color: #1C1D22 !important;
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3) !important;
}

/* --- HQ MANAGEMENT GHOST BUTTON --- */
div.stButton > button[key="mgmt_btn"] {
    background: transparent !important;
    color: #3B21E6 !important;
    border: 1px solid #3B21E6 !important;
}
div.stButton > button[key="mgmt_btn"]:hover {
    background: rgba(59, 33, 230, 0.04) !important;
}

/* --- SECURITY FORM --- */
div[data-testid="stForm"] {border-radius: 24px !important; padding: 35px !important;}
</style>""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown(
    "<div style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; uppercase; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", 
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px; margin-bottom: 0; letter-spacing: -1.5px; line-height: 1.1;'>"
    "Operations management <br><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span>"
    "</h1>", 
    unsafe_allow_html=True
)

# =========================================================
# CARDS
# =========================================================
grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown("<p style='font-size: 20px; font-weight: 700;'>Floor Control</p>", unsafe_allow_html=True)
    if st.button("Access Floor Control →", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")

with grid_right:
    st.markdown("<p style='font-size: 20px; font-weight: 700;'>HQ Administration</p>", unsafe_allow_html=True)
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"Console Locked ({remaining}s) 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True

# =========================================================
# PASSWORD SHEET
# =========================================================
if st.session_state.show_mgmt_password:
    with st.form("pass_form"):
        password_input = st.text_input("Password", type="password")
        if st.form_submit_button("Verify & Open"):
            if password_input == st.secrets.get("MANAGER_PASSWORD"):
                st.switch_page("pages/management_dashboard.py")
            else:
                st.error("Invalid credentials.")
