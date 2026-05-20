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
if "weekly_items" not in st.session_state: st.session_state.WEEKLY_ITEMS = {}
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
# DOM JAVASCRIPT OVERRIDE (TARGETS ONLY FLOOR CONTROL)
# =========================================================
st.components.v1.html("""
<script>
    const style = window.parent.document.createElement('style');
    style.innerHTML = `
        /* Hide unwanted boilerplate */
        #MainMenu, footer, header { visibility: hidden !important; }
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

        /* Global Font Face */
        .stApp {
            background-color: #FFFFFF !important;
            font-family: 'Times New Roman', Times, serif !important;
        }

        /* TARGETING ONLY THE FIRST BUTTON CONTAINER (FLOOR CONTROL)
        */
        div[data-testid="stHorizontalBlock"] > div:first-child button {
            background: #1C1D22 !important; /* Matte Charcoal */
            border: 3px solid #FF0033 !important; /* Thick High-Visibility Red */
            border-radius: 50px !important;
            height: 56px !important;
            box-shadow: 0 0 18px rgba(255, 0, 51, 0.4), inset 0 0 12px rgba(255, 0, 51, 0.2) !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        /* Bold White Typography for Floor Control Only */
        div[data-testid="stHorizontalBlock"] > div:first-child button * {
            color: #FFFFFF !important; 
            font-family: 'Times New Roman', Times, serif !important;
            font-size: 20px !important; 
            font-weight: 900 !important; 
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.8) !important;
        }

        /* Hover Response for Floor Control Only */
        div[data-testid="stHorizontalBlock"] > div:first-child button:hover {
            transform: translateY(-4px) scale(1.02) !important;
            background: #FF0033 !important; 
            border-color: #FF0033 !important;
            box-shadow: 0 12px 25px rgba(255, 0, 51, 0.5) !important;
        }

        /* TARGETING SECOND BUTTON CONTAINER (HQ ADMINISTRATION GHOST OUTLINE)
        */
        div[data-testid="stHorizontalBlock"] > div:last-child button {
            background: transparent !important;
            border: 1px solid #3B21E6 !important;
            border-radius: 50px !important;
            height: 56px !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"] > div:last-child button * {
            color: #3B21E6 !important;
            font-family: 'Times New Roman', Times, serif !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            text-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"] > div:last-child button:hover {
            background: rgba(59, 33, 230, 0.05) !important;
            border-color: #2A14CD !important;
        }
    `;
    window.parent.document.head.appendChild(style);
</script>
""", height=0)

# =========================================================
# STANDARD STYLESHEET FALLBACKS
# =========================================================
st.markdown("""<style>
.stApp {
    background-color: #FFFFFF;
    font-family: 'Times New Roman', Times, serif;
}
.block-container {
    max-width: 900px !important;
    padding-top: 5rem !important;
    padding-bottom: 5rem !important;
}
div[data-testid="stVerticalBlock"] > div:has(div.card-wrapper) {
    background-color: #F8F9FA !important;
    border-radius: 20px !important;
    padding: 30px !important;
    border: 1px solid #ECEFF1 !important;
}
</style>""", unsafe_allow_html=True)


# =========================================================
# CLEANED UP HEADER SYSTEM (NO BROKEN BLOCKS)
# =========================================================

# Clean Category Badge Accent
st.markdown(
    "<div style='text-align: center;'><span style='background: rgba(100, 116, 139, 0.08); color: #64748B; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; uppercase; letter-spacing: 1px; font-family: \"Times New Roman\", Times, serif;'>INTERNAL STAFF NETWORK</span></div>", 
    unsafe_allow_html=True
)

# Solid Clean Black Headline Title
st.markdown(
    "<h1 style='text-align: center; font-size: 56px; font-weight: 800; color: #111111; margin-top: 15px; margin-bottom: 0; letter-spacing: -1px; line-height: 1.2; font-family: \"Times New Roman\", Times, serif;'>\n"
    "Operations management just got easier."
    "</h1>", 
    unsafe_allow_html=True
)

# Clean Serif Description Subtext
st.markdown(
    "<p style='text-align: center; font-size: 18px; color: #475569; max-width: 580px; margin: 20px auto 40px auto; line-height: 1.6; font-family: \"Times New Roman\", Times, serif; font-style: italic;'>\n"
    "Welcome to the central command unit for BART. Seamlessly organize branch metrics, manage shift requirements, and deploy localized branch parameters."
    "</p>", 
    unsafe_allow_html=True
)


# =========================================================
# DUAL CARD INTERFACE MODULES
# =========================================================
grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 22px; font-weight: 700; color: #1E293B; margin-bottom: 4px; font-family: \"Times New Roman\", Times, serif;'>Floor Control</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 15px; color: #64748B; margin-bottom: 25px; font-family: \"Times New Roman\", Times, serif;'>Log daily updates, run item balance checkers, and communicate data parameters.</p>", unsafe_allow_html=True)
    
    if st.button("Access Floor Control →", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div>', unsafe_allow_html=True)

with grid_right:
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 22px; font-weight: 700; color: #1E293B; margin-bottom: 4px; font-family: \"Times New Roman\", Times, serif;'>HQ Administration</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 15px; color: #64748B; margin-bottom: 25px; font-family: \"Times New Roman\", Times, serif;'>Analyze operational logs, secure administrative configurations, and edit global secrets.</p>", unsafe_allow_html=True)
    
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"Console Locked ({remaining}s) 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# SECURITY SHEET FORM
# =========================================================
if st.session_state.show_mgmt_password:
    st.write("---")
    
    sheet_left, sheet_center, sheet_right = st.columns([1, 5, 1])
    with sheet_center:
        with st.form("pass_form", clear_on_submit=True):
            st.markdown("<h3 style='text-align: center; color: #1E293B; font-weight: 700; font-size: 22px; margin-bottom: 5px; font-family: \"Times New Roman\", Times, serif;'>Security Verification</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748B; font-size: 14px; margin-bottom: 20px; font-family: \"Times New Roman\", Times, serif;'>Input administrative access credentials to proceed into critical system files.</p>", unsafe_allow_html=True)
            
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
