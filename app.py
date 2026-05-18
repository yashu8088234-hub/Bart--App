import streamlit as st
import time
from ai_core import run_ai

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SESSION STATE
# =========================================================
st.session_state.authenticated = True

if "chat" not in st.session_state:
    st.session_state.chat = []

if "all_data" not in st.session_state:
    st.session_state.all_data = []

if "branches" not in st.session_state:
    st.session_state.branches = []

if "DAILY_ITEMS" not in st.session_state:
    st.session_state.DAILY_ITEMS = {}

if "WEEKLY_ITEMS" not in st.session_state:
    st.session_state.WEEKLY_ITEMS = {}

if "show_mgmt_password" not in st.session_state:
    st.session_state.show_mgmt_password = False

# 🔥 GLOBAL MANAGEMENT LOCK
if "mgmt_lock_until" not in st.session_state:
    st.session_state.mgmt_lock_until = 0


# =========================================================
# LOCK CHECK
# =========================================================
def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until


# =========================================================
# DATA CHECK
# =========================================================
def data_missing():
    return (
        not st.session_state.all_data
        and not st.session_state.branches
        and not st.session_state.DAILY_ITEMS
        and not st.session_state.WEEKLY_ITEMS
    )


# =========================================================
# STYLE (UNCHANGED)
# =========================================================
st.markdown("""<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

[data-testid="stSidebar"] {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="collapsedControl"] {
    display: none !important;
}

section.main > div {
    padding-left: 2rem;
    padding-right: 2rem;
}

.hero {
    background: white;
    padding: 60px;
    text-align: center;
    border-radius: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.hero h1 {font-size: 70px; color: #C0392B;}
.hero h2 {color: #2C2A28;}

div.stButton > button {
    width: 100%;
    height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color: white;
    font-weight: 700;
    border: none;
}

div.stButton > button:hover {opacity: 0.9;}

.section {
    background: white;
    padding: 25px;
    margin-top: 15px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    text-align: center;
}
</style>""", unsafe_allow_html=True)


# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# MAIN BUTTONS
# =========================================================
col1, col3, col2 = st.columns(3, gap="large")

with col1:
    if st.button("👨‍💼 Staff Dashboard", use_container_width=True):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    # 🔥 LOCKED BUTTON LOGIC
    if is_mgmt_locked():
        st.button("📦 Management Dashboard 🔒 Locked", disabled=True, use_container_width=True)
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.warning(f"Locked for {remaining} seconds")
    else:
        if st.button("📦 Management Dashboard", use_container_width=True):
            st.session_state.show_mgmt_password = True

with col3:
    st.empty()


# =========================================================
# PASSWORD CHECK
# =========================================================
if st.session_state.show_mgmt_password:

    st.markdown("### 🔐 Manager Access Required")

    password_input = st.text_input("Enter Manager Password", type="password")

    if st.button("Validate & Continue"):

        if password_input == st.secrets["MANAGER_PASSWORD"]:
            st.session_state.show_mgmt_password = False
            st.switch_page("pages/management_dashboard.py")
        else:
            st.error("❌ Incorrect password")



