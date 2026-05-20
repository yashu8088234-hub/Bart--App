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
# HIGH-END LUXURY LIGHT CSS
# =========================================================
st.markdown("""<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}

/* Premium Minimalist Light Background */
.stApp {
    background: radial-gradient(circle at top, #FCFAF7 0%, #F5ECE3 100%);
}

.block-container {
    max-width: 600px !important;
    padding-top: 12% !important;
}

/* Master Button Override */
div.stButton > button {
    height: 68px !important;
    border-radius: 18px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Staff Button: Deep Espresso Cream */
div.stButton > button[key="staff_btn"] {
    background: #2C2A28 !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 10px 25px rgba(44, 42, 40, 0.15) !important;
}
div.stButton > button[key="staff_btn"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 15px 30px rgba(44, 42, 40, 0.25) !important;
}

/* Management Button: Premium Bart Red */
div.stButton > button[key="mgmt_btn"] {
    background: #FFFFFF !important;
    color: #C0392B !important;
    border: 2px solid #C0392B !important;
    box-shadow: 0 10px 25px rgba(192, 57, 43, 0.08) !important;
}
div.stButton > button[key="mgmt_btn"]:hover {
    transform: translateY(-3px) !important;
    background: #C0392B !important;
    color: #FFFFFF !important;
    box-shadow: 0 15px 30px rgba(192, 57, 43, 0.25) !important;
}

/* Form Styling */
div[data-testid="stForm"] {
    background: #FFFFFF !important;
    border: 1px solid rgba(0,0,0,0.05) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    box-shadow: 0 15px 35px rgba(0,0,0,0.05) !important;
}

/* Elegant Text Inputs */
div[data-testid="stTextInput"] input {
    border-radius: 12px !important;
    background-color: #FAFAFA !important;
    border: 1px solid #EAEAEA !important;
    height: 48px !important;
    text-align: center !important;
    font-size: 16px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #C0392B !important;
    background-color: #FFFFFF !important;
}
</style>""", unsafe_allow_html=True)

# =========================================================
# THE VISUAL LAYOUT
# =========================================================

# Clean, Bold Typography Focus
st.markdown("<h1 style='text-align: center; font-size: 86px; font-weight: 900; color: #2C2A28; margin-bottom: 0; letter-spacing: -4px;'>BART</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 13px; color: #C0392B; font-weight: 800; text-transform: uppercase; letter-spacing: 5px; margin-top: -5px;'>Coffee & Fresh Bites • Jeddah</p>", unsafe_allow_html=True)

st.write("###")

# Compact Action Center
col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("👨‍💼 Staff Entry", use_container_width=True, key="staff_btn"):
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
        st.markdown("<p style='text-align: center; color: #7F8C8D; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px;'>Security Verification</p>", unsafe_allow_html=True)
        password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="••••••••")
        
        st.write("#")
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_mgmt_password = False
                st.rerun()
        with c2:
            if st.form_submit_button("Confirm →", use_container_width=True):
                if password_input == st.secrets["MANAGER_PASSWORD"]:
                    st.session_state.show_mgmt_password = False
                    st.switch_page("pages/management_dashboard.py")
                else:
                    st.error("Invalid Code")
