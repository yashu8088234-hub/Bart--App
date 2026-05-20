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

if "mgmt_lock_until" not in st.session_state:
    st.session_state.mgmt_lock_until = 0


# =========================================================
# LOCK & DATA CHECKS (UNCHANGED LOGIC)
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
# REFRESHED CAFE-STYLE CSS
# =========================================================
st.markdown("""<style>
/* Hide default boilerplate elements */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
    visibility: hidden !important;
}

/* Warm, premium coffee-shop color scheme */
.stApp {
    background-color: #FBF9F6;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Container limits for an elegant, non-stretched look on ultra-wide screens */
.block-container {
    max-width: 900px !important;
    padding-top: 4rem !important;
    padding-bottom: 4rem !important;
}

/* Subtly style text inputs and passwords */
div[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    border: 1px solid #E0DCD6 !important;
    padding: 12px !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #C0392B !important;
    box-shadow: 0 0 0 1px #C0392B !important;
}
</style>""", unsafe_allow_html=True)


# =========================================================
# REDESIGNED BRAND HEADER
# =========================================================
# Using Streamlit columns + native typography for a modern, accessible layout
left_space, center_card, right_space = st.columns([1, 6, 1])

with center_card:
    st.markdown(
        "<h1 style='text-align: center; font-size: 72px; font-weight: 800; color: #1E1E1E; margin-bottom: 0; letter-spacing: -2px;'>BART</h1>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-size: 18px; color: #C0392B; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px; margin-bottom: 5px;'>Coffee • French Toast • Fresh Bites</p>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #7F8C8D; font-size: 14px;'>📍 Jeddah • bart.sa</p>", 
        unsafe_allow_html=True
    )
    
    st.write("---") # Soft visual divider
    
    # Check data status inline with a modern status notice if empty
    if data_missing():
        st.info("💡 System is ready. Waiting for initial operational data payload.")

    st.write("##") # Spacer

    # =========================================================
    # ACTION DASHBOARDS (2-COLUMN GRID)
    # =========================================================
    dash_col1, dash_col2 = st.columns(2, gap="large")
    
    with dash_col1:
        with st.container(border=True):
            st.markdown("### 👨‍💼 Floor Staff")
            st.caption("Access daily logs, item checklists, and localized branch operations counters.")
            st.write("##") # Align button push
            if st.button("Open Staff Dashboard →", use_container_width=True, type="secondary"):
                st.switch_page("pages/staff_dashboard.py")
                
    with dash_col2:
        with st.container(border=True):
            st.markdown("### 📦 Administration")
            st.caption("Manage menu items, access raw configurations, and view cross-branch performance.")
            st.write("##")
            
            # 🔥 LOCKED BUTTON LOGIC
            if is_mgmt_locked():
                st.button("Dashboard Locked 🔒", disabled=True, use_container_width=True)
                remaining = int(st.session_state.mgmt_lock_until - time.time())
                st.error(f"Security lock active for {remaining}s")
            else:
                if st.button("Unlock Admin Panel ✨", use_container_width=True, type="primary"):
                    st.session_state.show_mgmt_password = True


    # =========================================================
    # PASSWORD CHECK IN-LINE INTERACTION
    # =========================================================
    if st.session_state.show_mgmt_password:
        st.write("---")
        
        # Center the password form nicely within the view block
        p_left, p_mid, p_right = st.columns([1, 4, 1])
        with p_mid:
            with st.container(border=True):
                st.markdown("🔒 **Manager Authentication Required**")
                password_input = st.text_input("Enter credentials to proceed", type="password", label_visibility="collapsed", placeholder="Enter Manager Password")
                
                # Align action buttons nicely side by side
                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_mgmt_password = False
                        st.rerun()
                with btn2:
                    if st.button("Verify Identity", use_container_width=True, type="primary"):
                        if password_input == st.secrets["MANAGER_PASSWORD"]:
                            st.session_state.show_mgmt_password = False
                            st.switch_page("pages/management_dashboard.py")
                        else:
                            st.error("❌ Invalid Access Token")
