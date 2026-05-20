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
if "WEEKLY_ITEMS" not in st.session_state: st.session_state.WEEKLY_ITEMS = {}
if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# GLOBAL STYLING (FULL SCREEN BACKGROUND + FROSTED CARDS)
# =========================================================
st.markdown("""<style>
/* Reset boilerplate */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important;}

/* Full Screen Earth Background */
.stApp {
    background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    font-family: 'Inter', sans-serif;
}

/* Frosted Glass Container */
div[data-testid="stVerticalBlock"] > div:has(div.card-wrapper) {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(15px) !important;
    border-radius: 24px !important;
    padding: 30px !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1) !important;
}

/* Button Styling */
div.stButton > button {
    height: 54px !important;
    border-radius: 50px !important;
    border: none !important;
    background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%) !important;
    color: #FFFFFF !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    box-shadow: 0 4px 15px rgba(46, 212, 122, 0.3) !important;
}
</style>""", unsafe_allow_html=True)

# =========================================================
# UI COMPONENTS
# =========================================================
st.markdown("<div style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.1); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px;'>BART Operations</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; color: #64748B; margin-bottom: 40px;'>Central command unit for operational management.</p>", unsafe_allow_html=True)

grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("<h3>Floor Control</h3>", unsafe_allow_html=True)
    if st.button("Access Floor Control →", use_container_width=True):
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div>', unsafe_allow_html=True)

with grid_right:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("<h3>HQ Administration</h3>", unsafe_allow_html=True)
    if is_mgmt_locked():
        st.button(f"Locked", disabled=True, use_container_width=True)
    else:
        if st.button("Unlock Admin Panel", use_container_width=True):
            st.session_state.show_mgmt_password = True
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.show_mgmt_password:
    with st.form("pass_form"):
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Verify"):
            if password == st.secrets["MANAGER_PASSWORD"]:
                st.switch_page("pages/management_dashboard.py")
            else:
                st.error("Invalid token.")
