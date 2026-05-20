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
# CORE LOGIC
# =========================================================
def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# CSS ARCHITECTURE
# =========================================================
st.markdown("""<style>
/* --- ANIMATED BACKGROUND --- */
.background-container {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: -1; overflow: hidden; pointer-events: none;
}
.orbit {
    position: absolute; top: 50%; left: 50%;
    width: 600px; height: 300px; border: 1px dashed rgba(46, 212, 122, 0.15);
    border-radius: 50%; animation: spin 20s linear infinite;
    transform: translate(-50%, -50%);
}
.icon {
    position: absolute; top: -15px; left: 50%; font-size: 20px;
    animation: counter-spin 20s linear infinite;
}
@keyframes spin { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes counter-spin { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }

/* --- ORIGINAL CSS --- */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}

/* Header Animations */
@keyframes fadeInUp {
    0% { opacity: 0; transform: translateY(30px); }
    100% { opacity: 1; transform: translateY(0); }
}
.animate-text { animation: fadeInUp 0.8s ease-out forwards; opacity: 0; }
.delay-1 { animation-delay: 0.2s; }
.delay-2 { animation-delay: 0.4s; }
.delay-3 { animation-delay: 0.6s; }
.delay-4 { animation-delay: 0.8s; }

/* Enhanced High-Impact BART Pulse */
@keyframes breathe-bold {
    0%, 100% { 
        transform: scale(1); 
        text-shadow: 0 0 10px rgba(46, 212, 122, 0.2);
    }
    50% { 
        transform: scale(1.05); 
        text-shadow: 0 0 30px rgba(46, 212, 122, 0.6); 
    }
}
.bart-logo {
    display: inline-block;
    animation: breathe-bold 2s ease-in-out infinite;
    background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    cursor: default;
    font-weight: 900 !important;
    letter-spacing: -2px;
}

/* Glow Card Effect */
@keyframes rotate { 100% { transform: rotate(360deg); } }
.card-glow {
    position: relative; padding: 2px;
    background: #F8F9FA; border-radius: 22px; overflow: hidden;
}
.card-glow::before {
    content: ''; position: absolute;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: conic-gradient(transparent, #2ED47A, transparent 30%);
    animation: rotate 4s linear infinite;
}
.card-content {
    position: relative; background: #F8F9FA;
    border-radius: 20px; padding: 30px; z-index: 1;
}

/* Glow Button Effect */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    position: relative;
    height: 54px !important; border-radius: 50px !important;
    border: none !important; background: #20C997 !important;
    color: #FFFFFF !important; font-weight: 900 !important;
    text-transform: uppercase !important; letter-spacing: 2px !important;
    overflow: hidden; z-index: 1;
}
div.stButton > button::before, div[data-testid="stFormSubmitButton"] > button::before {
    content: ''; position: absolute; z-index: -1;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: conic-gradient(transparent, #2ED47A, transparent 50%);
    animation: rotate 3s linear infinite;
}
div.stButton > button:hover { transform: translateY(-2px); }

/* Containers */
.stApp {background-color: #FFFFFF !important; font-family: 'Inter', system-ui, sans-serif;}
.block-container {max-width: 900px !important; padding-top: 5rem !important;}
div[data-testid="stForm"] {background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 24px !important; padding: 35px !important;}
div[data-testid="stTextInput"] input {border-radius: 50px !important; background-color: #F8FAFC !important; height: 52px !important; text-align: center !important;}
</style>""", unsafe_allow_html=True)

# Inject the Background HTML
st.markdown("""
<div class="background-container">
    <div class="orbit" style="animation-duration: 25s;"><div class="icon">🍴</div></div>
    <div class="orbit" style="animation-duration: 35s; transform: translate(-50%, -50%) rotate(72deg);"><div class="icon">🔒</div></div>
    <div class="orbit" style="animation-duration: 45s; transform: translate(-50%, -50%) rotate(144deg);"><div class="icon">📝</div></div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ANIMATED HEADER
# =========================================================
st.markdown("<div class='animate-text delay-1' style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)

# BART Title with High-Impact Pulse
st.markdown("""
    <h1 class='animate-text delay-2' style='text-align: center; font-size: 88px; font-weight: 800; color: #111111; margin-top: 5px; margin-bottom: -15px; letter-spacing: -2.5px;'>
        <span class='bart-logo'>B A R T</span>
    </h1>
""", unsafe_allow_html=True)

st.markdown("<h1 class='animate-text delay-3' style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px; margin-bottom: 0;'>Operations management <br><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='animate-text delay-4' style='text-align: center; font-size: 16px; color: #64748B; max-width: 520px; margin: 20px auto 40px auto;'>Welcome to the central command unit for BART. Seamlessly organize branch metrics, manage shift requirements, and deploy localized branch parameters.</p>", unsafe_allow_html=True)

# =========================================================
# CARDS
# =========================================================
grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">Staff Control """, unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; color: #64748B; margin-bottom: 25px;'>Log daily updates, run item balance checkers, and communicate data parameters.</p>", unsafe_allow_html=True)
    if st.button("Access Staff Control →", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div></div>', unsafe_allow_html=True)

with grid_right:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">HQ Administration""", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; color: #64748B; margin-bottom: 25px;'>Analyze operational logs, secure administrative configurations, and edit global secrets.</p>", unsafe_allow_html=True)
    
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"Console Locked ({remaining}s) 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

# =========================================================
# PASSWORD VERIFICATION SHEET
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
