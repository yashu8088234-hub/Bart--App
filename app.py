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

if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# CSS ARCHITECTURE (ANIMATED HEADER + GLOW CARDS)
# =========================================================
st.markdown("""<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}

/* Animation Keyframes */
@keyframes fadeInUp {
    0% { opacity: 0; transform: translateY(30px); }
    100% { opacity: 1; transform: translateY(0); }
}
@keyframes rotate {
    100% { transform: rotate(360deg); }
}

.animate-text { animation: fadeInUp 0.8s ease-out forwards; opacity: 0; }
.delay-1 { animation-delay: 0.2s; }
.delay-2 { animation-delay: 0.4s; }
.delay-3 { animation-delay: 0.6s; }
.delay-4 { animation-delay: 0.8s; }

.stApp {background-color: #FFFFFF !important; font-family: 'Inter', system-ui, sans-serif;}

/* Glowing Card Effect */
.card-glow {
    position: relative;
    padding: 2px;
    background: #F1F3F5;
    border-radius: 22px;
    overflow: hidden;
}
.card-glow::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(transparent, #2ED47A, transparent 30%);
    animation: rotate 4s linear infinite;
}
.card-content {
    position: relative;
    background: #FFFFFF;
    border-radius: 20px;
    padding: 30px;
    z-index: 1;
}

/* Button Styling */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    height: 54px !important; border-radius: 50px !important; border: none !important;
    background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%) !important;
    color: #FFFFFF !important; font-weight: 900 !important; text-transform: uppercase !important;
    letter-spacing: 2px !important; transition: 0.3s !important;
}
div.stButton > button:hover { transform: scale(1.02) !important; box-shadow: 0 10px 20px rgba(46, 212, 122, 0.3) !important; }

.block-container {max-width: 900px !important; padding-top: 5rem !important;}
div[data-testid="stForm"] {background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 24px !important; padding: 35px !important;}
div[data-testid="stTextInput"] input {border-radius: 50px !important; background-color: #F8FAFC !important; border: 1px solid #E2E8F0 !important; height: 52px !important; text-align: center !important;}
</style>""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("<div class='animate-text delay-1' style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)
st.markdown("<h1 class='animate-text delay-2' style='text-align: center; font-size: 88px; font-weight: 800; color: #111111; margin-top: 5px; margin-bottom: -15px; letter-spacing: -2.5px;'><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>B A R T</span></h1>", unsafe_allow_html=True)
st.markdown("<h1 class='animate-text delay-3' style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px; margin-bottom: 0;'>Operations management <br><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='animate-text delay-4' style='text-align: center; font-size: 16px; color: #64748B; max-width: 520px; margin: 20px auto 40px auto;'>Welcome to the central command unit for BART. Seamlessly organize branch metrics, manage shift requirements, and deploy localized branch parameters.</p>", unsafe_allow_html=True)

# =========================================================
# GLOW CARDS
# =========================================================
grid_left, grid_right = st.columns(2, gap="large")

with grid_left:
    st.markdown('<div class="card-glow"><div class="card-content">', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; font-weight: 700;'>Staff Control</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Log daily updates, run item balance checkers, and communicate data parameters.</p>", unsafe_allow_html=True)
    if st.button("Access Staff Control →", use_container_width=True, key="staff_btn"):
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div></div>', unsafe_allow_html=True)

with grid_right:
    st.markdown('<div class="card-glow"><div class="card-content">', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; font-weight: 700;'>HQ Administration</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Analyze operational logs, secure administrative configurations, and edit global secrets.</p>", unsafe_allow_html=True)
    if is_mgmt_locked():
        st.button("Console Locked 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

# =========================================================
# PASSWORD SHEET
# =========================================================
if st.session_state.show_mgmt_password:
    st.write("---")
    st.markdown('<div id="security_form"></div>', unsafe_allow_html=True)
    st.components.v1.html("""<script>setTimeout(function() {var el = window.parent.document.getElementById('security_form'); if (el) { el.scrollIntoView({behavior: 'smooth'}); }}, 100);</script>""", height=0)
    
    _, sheet_center, _ = st.columns([1, 5, 1])
    with sheet_center:
        with st.form("pass_form", clear_on_submit=True):
            password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter System Password")
            col1, col2 = st.columns(2, gap="medium")
            with col1:
                if st.form_submit_button("Abort Login", use_container_width=True):
                    st.session_state.show_mgmt_password = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Verify & Open", use_container_width=True):
                    if password_input == st.secrets.get("MANAGER_PASSWORD"):
                        st.switch_page("pages/management_dashboard.py")
