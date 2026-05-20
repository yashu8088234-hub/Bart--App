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

# =========================================================
# CORE LOGIC CHECKS
# =========================================================
def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# ATLAS SAAS PRESTIGE LIGHT CSS (UNIFIED TEAL/GREEN GRADIENT)
# =========================================================
st.markdown("""<style>
/* Reset boilerplate elements */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}

.stApp {background-color: #FFFFFF; font-family: 'Inter', system-ui, sans-serif;}

.block-container {max-width: 900px !important; padding-top: 5rem !important; padding-bottom: 5rem !important;}

div[data-testid="stVerticalBlock"] > div:has(div.card-wrapper) {
    background-color: #F8F9FA !important;
    border-radius: 20px !important;
    padding: 30px !important;
    border: 1px solid #ECEFF1 !important;
}

/* --- UNIFIED PILL BUTTON ARCHITECTURE (Both Buttons) --- */
div.stButton > button {
    height: 54px !important;
    border-radius: 50px !important;
    border: none !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%) !important;
    box-shadow: 0 4px 15px rgba(46, 212, 122, 0.3) !important;
}

/* Text styling for buttons */
div.stButton > button p {
    color: #FFFFFF !important;
    font-size: 14px !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
}

/* Hover state for both buttons */
div.stButton > button:hover {
    transform: translateY(-2px) scale(1.01) !important;
    background: linear-gradient(90deg, #20C997 0%, #1aae82 100%) !important;
    box-shadow: 0 8px 20px rgba(46, 212, 122, 0.4) !important;
}

div.stButton > button:active {
    transform: translateY(-1px) scale(0.99) !important;
}

/* Locked Admin State Styling (Stays muted but distinct) */
div.stButton > button:disabled {
    background: #E9ECEF !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}
div.stButton > button:disabled p {
    color: #ADB5BD !important;
}

/* --- SECURITY SHEET GATEWAY --- */
div[data-testid="stForm"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 24px !important;
    padding: 35px !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.04) !important;
}

div[data-testid="stTextInput"] input {
    border-radius: 50px !important;
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    height: 52px !important;
    text-align: center !important;
    font-size: 16px !important;
}
</style>""", unsafe_allow_html=True)

# =========================================================
# UI LAYOUT
# =========================================================
st.markdown("<div style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px;'>"
            "Operations management <br><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span>"
            "</h1>", unsafe_allow_html=True)

grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("### Floor Control")
    if st.button("Access Floor Control →", key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div>', unsafe_allow_html=True)

with grid_right:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("### HQ Administration")
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"Console Locked ({remaining}s) 🔒", disabled=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.show_mgmt_password:
    st.write("---")
    _, sheet_center, _ = st.columns([1, 5, 1])
    with sheet_center:
        with st.form("pass_form"):
            password_input = st.text_input("Password", type="password", placeholder="Enter System Password")
            if st.form_submit_button("Verify & Open"):
                if password_input == st.secrets["MANAGER_PASSWORD"]:
                    st.switch_page("pages/management_dashboard.py")
                else:
                    st.error("Access Refused")
