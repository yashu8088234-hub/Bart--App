import streamlit as st
import time
from ai_core import run_ai

# =========================================================
# SYSTEM CONFIG
# =========================================================
st.set_page_config(page_title="BART Portal", layout="wide", initial_sidebar_state="collapsed")

# =========================================================
# SESSION STATE
# =========================================================
st.session_state.authenticated = True
if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# COMPACT CSS ARCHITECTURE
# =========================================================
st.markdown("""<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important;}

/* Extremely Compact Spacing */
.animate-text { margin: 0px !important; padding: 0px !important; }
h1 { margin: 0px !important; padding: 0px !important; line-height: 1 !important; }
p { margin: 0px !important; padding: 0px !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

/* Buttons */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    height: 45px !important; border-radius: 50px !important;
}
</style>""", unsafe_allow_html=True)

# =========================================================
# ANIMATED HEADER (COMPACT)
# =========================================================
st.markdown("<div class='animate-text' style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 2px 10px; border-radius: 100px; font-size: 10px; font-weight: 700;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)
st.markdown("<h1 class='animate-text' style='text-align: center; font-size: 70px; font-weight: 800;'>B A R T</h1>", unsafe_allow_html=True)
st.markdown("<h1 class='animate-text' style='text-align: center; font-size: 40px; font-weight: 800; color: #111111;'>Operations management just got easier.</h1>", unsafe_allow_html=True)
st.markdown("<p class='animate-text' style='text-align: center; font-size: 14px; color: #64748B;'>Central command unit for BART. Organize metrics, manage shifts, and deploy parameters.</p>", unsafe_allow_html=True)

# =========================================================
# CARDS
# =========================================================
grid_left, grid_right = st.columns(2, gap="medium")
with grid_left:
    st.subheader("Staff Control")
    st.write("Log daily updates and balance checkers.")
    if st.button("Access Staff Control →", use_container_width=True): st.switch_page("pages/staff_dashboard.py")

with grid_right:
    st.subheader("HQ Administration")
    st.write("Analyze logs and edit global secrets.")
    if is_mgmt_locked(): st.button("Locked 🔒", disabled=True, use_container_width=True)
    elif st.button("Unlock Admin Panel", use_container_width=True): 
        st.session_state.show_mgmt_password = True
        st.rerun()

# =========================================================
# PASSWORD VERIFICATION SHEET (YOUR ORIGINAL)
# =========================================================
if st.session_state.show_mgmt_password:
    st.write("---")
    st.markdown('<div id="security_form"></div>', unsafe_allow_html=True)
    st.components.v1.html("""<script>setTimeout(function() {var el = window.parent.document.getElementById('security_form'); if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }}, 100);</script>""", height=0)
    
    sheet_left, sheet_center, sheet_right = st.columns([1, 5, 1])
    with sheet_center:
        with st.form("pass_form", clear_on_submit=True):
            st.markdown("<h3 style='text-align: center; color: #1E293B; font-weight: 700; font-size: 20px; margin-bottom: 5px;'>Security Verification</h3>", unsafe_allow_html=True)
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
