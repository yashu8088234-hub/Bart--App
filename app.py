import streamlit as st
import time

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

# =========================================================
# CORE LOGIC
# =========================================================
def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# CSS ARCHITECTURE
# =========================================================
st.markdown("""<style>
/* Reset boilerplate */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important;}

.stApp { background-color: #FFFFFF; font-family: 'Inter', system-ui, sans-serif; }
.block-container { max-width: 900px !important; padding-top: 5rem !important; }

/* Card Styling */
div[data-testid="stVerticalBlock"] > div:has(div.card-wrapper) {
    background-color: #F8F9FA !important;
    border-radius: 20px !important;
    padding: 30px !important;
    border: 1px solid #ECEFF1 !important;
}

/* --- GREEN GRADIENT BUTTONS --- */
div.stButton > button {
    height: 54px !important;
    border-radius: 50px !important;
    transition: all 0.3s ease !important;
    border: none !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
}

div.stButton > button[key="staff_btn"] {
    background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(46, 212, 122, 0.3) !important;
}

div.stButton > button[key="staff_btn"]:hover {
    transform: translateY(-4px) scale(1.02) !important;
    background: linear-gradient(90deg, #28B96A 0%, #1CA87F 100%) !important;
    box-shadow: 0 12px 30px rgba(46, 212, 122, 0.4) !important;
}

/* HQ Button (Ghost style) */
div.stButton > button[key="mgmt_btn"] {
    background: transparent !important;
    color: #3B21E6 !important;
    border: 1px solid #3B21E6 !important;
}
div.stButton > button[key="mgmt_btn"]:hover {
    background: rgba(59, 33, 230, 0.05) !important;
}

/* Form Styles */
div[data-testid="stForm"] { border-radius: 24px !important; padding: 35px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.05) !important; }
</style>""", unsafe_allow_html=True)

# =========================================================
# UI LAYOUT
# =========================================================
st.markdown("<div style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px; margin-bottom: 0; letter-spacing: -1.5px; line-height: 1.1;'>"
    "Operations management <br><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span>"
    "</h1>", unsafe_allow_html=True
)

st.markdown("<p style='text-align: center; font-size: 16px; color: #64748B; max-width: 520px; margin: 20px auto 40px auto; line-height: 1.6;'>Welcome to the central command unit for BART. Seamlessly organize branch metrics and manage shift requirements.</p>", unsafe_allow_html=True)

grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("### Floor Control")
    st.markdown("<p style='color: #64748B; font-size: 14px;'>Log daily updates and run item balance checkers.</p>", unsafe_allow_html=True)
    if st.button("Access Floor Control →", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div>', unsafe_allow_html=True)

with grid_right:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("### HQ Administration")
    st.markdown("<p style='color: #64748B; font-size: 14px;'>Analyze operational logs and edit global secrets.</p>", unsafe_allow_html=True)
    if is_mgmt_locked():
        st.button("Console Locked 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
    st.markdown('</div>', unsafe_allow_html=True)

# Password Logic
if st.session_state.show_mgmt_password:
    st.write("---")
    _, c, _ = st.columns([1, 3, 1])
    with c:
        with st.form("pass_form"):
            p = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter System Password")
            if st.form_submit_button("Verify & Open", use_container_width=True):
                if p == st.secrets.get("MANAGER_PASSWORD"):
                    st.session_state.show_mgmt_password = False
                    st.switch_page("pages/management_dashboard.py")
                else:
                    st.error("Access Refused")
