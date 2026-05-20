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
# BRAND COLOUR PILL BUTTON CSS
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

/* --- MASTER BUTTON ARCHITECTURE --- */
div.stButton > button {
    height: 54px !important;
    border-radius: 50px !important; /* Premium Atlas Pill Style */
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: -0.2px !important;
    transition: all 0.2s ease-in-out !important;
    border: none !important;
}

/* Apply Your Gradient Palette to BOTH Buttons */
div.stButton > button[key="staff_btn"], 
div.stButton > button[key="mgmt_btn"] {
    background: linear-gradient(135deg, #2C2A28, #C0392B) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(192, 57, 43, 0.2) !important;
}

/* Hover effects for both buttons */
div.stButton > button[key="staff_btn"]:hover, 
div.stButton > button[key="mgmt_btn"]:hover {
    transform: translateY(-2px) !important;
    opacity: 0.93 !important;
    box-shadow: 0 6px 20px rgba(192, 57, 43, 0.35) !important;
}

/* Locked Admin State Styling Overrides */
div.stButton > button[key="mgmt_btn"]:disabled {
    background: #F1F3F5 !important;
    color: #ADB5BD !important;
    border: 1px solid #E9ECEF !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: none !important;
}

/* --- SECURITY SHEET GATEWAY --- */
div[data-testid="stForm"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 24px !important;
    padding: 35px !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.04) !important;
}

/* Dynamic Verification Password Field */
div[data-testid="stTextInput"] input {
    border-radius: 50px !important;
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    height: 52px !important;
    text-align: center !important;
    font-size: 16px !important;
    color: #1E293B !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #C0392B !important;
    background-color: #FFFFFF !important;
    box-shadow: 0 0 0 1px #C0392B !important;
}

/* Override form buttons to look smaller and cohesive */
div[data-testid="stForm"] div.stButton > button {
    height: 48px !important;
}
</style>""", unsafe_allow_html=True)


# =========================================================
# PREMIUM SAAS VISUAL HEADER
# =========================================================

# Clean Category Badge Accent (Using your Crimson brand highlight)
st.markdown(
    "<div style='text-align: center;'><span style='background: rgba(192, 57, 43, 0.08); color: #C0392B; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; uppercase; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", 
    unsafe_allow_html=True
)

# Main Title Headline Structure
st.markdown(
    "<h1 style='text-align: center; font-size: 58px; font-weight: 800; color: #2C2A28; margin-top: 15px; margin-bottom: 0; letter-spacing: -1.5px; line-height: 1.1;'>"
    "Operations management <br><span style='background: linear-gradient(90deg, #C0392B 0%, #E74C3C 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span>"
    "</h1>", 
    unsafe_allow_html=True
)

# Meta Info Text Description Block
st.markdown(
    "<p style='text-align: center; font-size: 16px; color: #64748B; max-width: 520px; margin: 20px auto 40px auto; line-height: 1.6;'>"
    "Welcome to the central command unit for BART. Seamlessly organize branch metrics, manage shift requirements, and deploy localized branch parameters."
    "</p>", 
    unsafe_allow_html=True
)


# =========================================================
# HIGH-END DUAL EXECUTIVE CARDS
# =========================================================
grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; font-weight: 700; color: #2C2A28; margin-bottom: 4px;'>Floor Control</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; color: #64748B; margin-bottom: 25px;'>Log daily updates, run item balance checkers, and communicate data parameters.</p>", unsafe_allow_html=True)
    
    if st.button("Access Floor Control →", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div>', unsafe_allow_html=True)

with grid_right:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; font-weight: 700; color: #2C2A28; margin-bottom: 4px;'>HQ Administration</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; color: #64748B; margin-bottom: 25px;'>Analyze operational logs, secure administrative configurations, and edit global secrets.</p>", unsafe_allow_html=True)
    
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"Console Locked ({remaining}s) 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# MODERN SLIDE-IN PASSWORD VERIFICATION SHEET
# =========================================================
if st.session_state.show_mgmt_password:
    st.write("---")
    
    sheet_left, sheet_center, sheet_right = st.columns([1, 5, 1])
    with sheet_center:
        with st.form("pass_form", clear_on_submit=True):
            st.markdown("<h3 style='text-align: center; color: #2C2A28; font-weight: 700; font-size: 20px; margin-bottom: 5px;'>Security Verification</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748B; font-size: 13px; margin-bottom: 20px;'>Input administrative access credentials to proceed into critical system files.</p>", unsafe_allow_html=True)
            
            password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter System Password")
            
            st.write("##")
            action_col1, action_col2 = st.columns(2, gap="medium")
            with action_col1:
                if st.form_submit_button("Abort Login", use_container_width=True):
                    st.session_state.show_mgmt_password = False
                    st.rerun()
            with action_col2:
                if st.form_submit_button("Verify & Open", use_container_width=True):
                    if password_input == st.secrets["MANAGER_PASSWORD"]:
                        st.session_state.show_mgmt_password = False
                        st.switch_page("pages/management_dashboard.py")
                    else:
                        st.error("Access Refused: Invalid token signature.")
