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
# CSS ARCHITECTURE
# =========================================================
st.markdown("""<style>
/* Forces transparency and reduces top padding */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] { background: transparent !important; }
.block-container { max-width: 900px !important; padding-top: 1rem !important; }

/* Background Layer */
.background-layer { 
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -9999; 
    overflow: hidden; background-color: #F8FAFC; 
    display: flex; justify-content: center; align-items: center;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 400'%3E%3Cpath fill='%23CBD5E1' d='M100 100c50 0 50 50 100 50s50-50 100-50 50 50 100 50 50-50 100-50 50 50 100 50 50-50 100-50 50 50 100 50'/%3E%3C/svg%3E");
    background-size: cover;
    background-position: center;
    opacity: 0.6; 
}

/* Orbit lines */
.orbit { position: absolute; border: 1px solid rgba(0, 0, 0, 0.2); border-radius: 50%; animation: spin linear infinite; left: 50%; top: 50%; transform: translate(-50%, -50%); }
.o1 { width: 200px; height: 200px; animation-duration: 20s; }
.o2 { width: 350px; height: 350px; animation-duration: 30s; }
.o3 { width: 500px; height: 500px; animation-duration: 40s; }
.o4 { width: 650px; height: 650px; animation-duration: 50s; }
.o5 { width: 800px; height: 800px; animation-duration: 65s; }
.o6 { width: 950px; height: 950px; animation-duration: 85s; }
.o7 { width: 1100px; height: 1100px; animation-duration: 110s; }

/* UI Elements */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}
@keyframes spin { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes counter { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }
.icon { animation: counter linear infinite; font-size: 24px; position: absolute; top: -12px; left: 50%; margin-left: -12px; }
@keyframes fadeInUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
.animate-text { animation: fadeInUp 0.8s ease-out forwards; opacity: 0; }
.delay-1 { animation-delay: 0.2s; } .delay-2 { animation-delay: 0.4s; } .delay-3 { animation-delay: 0.6s; } .delay-4 { animation-delay: 0.8s; }

/* BART LOGO STYLING */
@keyframes breathe-pink { 0%, 100% { transform: scale(1); text-shadow: 0 0 10px rgba(234, 7, 99, 0.2); } 50% { transform: scale(1.05); text-shadow: 0 0 30px rgba(234, 7, 99, 0.6); } }
.bart-logo { display: inline-block; animation: breathe-pink 2s ease-in-out infinite; color: #ea0763 !important; cursor: default; font-weight: 900 !important; letter-spacing: -2px; }
@keyframes rotate { 100% { transform: rotate(360deg); } }

.card-glow { position: relative; padding: 2px; background: #FFFFFF; border-radius: 22px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); }
.card-glow::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, #ea0763, transparent 30%); animation: rotate 4s linear infinite; }
.card-content { position: relative; background: #FFFFFF; border-radius: 20px; padding: 30px; z-index: 1; }

/* INNOVATIVE LIQUID-SPRING BUTTON */
div.stButton > button { 
    position: relative; 
    height: 54px !important; 
    border-radius: 50px !important; 
    border: none !important; 
    background: #ea0763 !important; 
    color: #FFFFFF !important; 
    font-weight: 900 !important; 
    text-transform: uppercase !important; 
    letter-spacing: 2px !important; 
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
}
div.stButton > button::before { display: none !important; }
div.stButton > button:hover {
    transform: scale(1.05) translateY(-2px);
    background: #c50653 !important; 
    box-shadow: 0 10px 20px rgba(234, 7, 99, 0.3) !important;
    letter-spacing: 4px !important;
}
div.stButton > button:active {
    transform: scale(0.98) translateY(0);
}
</style>""", unsafe_allow_html=True)

# [Remaining code logic is unchanged as requested]
# =========================================================
# SESSION STATE - Assuming no changes requested here
# =========================================================
st.session_state.authenticated = True
if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# BACKGROUND LAYER - Assuming no changes requested here
# =========================================================
st.markdown("""
<div class="background-layer">
    <div class="orbit-wrap">
        <div class="orbit o1"><div class="icon">☿</div></div>
        <div class="orbit o2"><div class="icon">♀</div></div>
        <div class="orbit o3"><div class="icon">☄️</div></div>
        <div class="orbit o4"><div class="icon">🌎</div></div>
        <div class="orbit o5"><div class="icon">🪐</div></div>
        <div class="orbit o6"><div class="icon">🌐</div></div>
        <div class="orbit o7"><div class="icon">🪐</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ANIMATED HEADER & UI - Text preserved exactly
# =========================================================
st.markdown("<div class='animate-text delay-1' style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)
st.markdown("""<h1 class='animate-text delay-2' style='text-align: center; font-size: 88px; font-weight: 800; color: #111111; margin-top: 5px; margin-bottom: -15px; letter-spacing: -2.5px;'><span class='bart-logo'>B A R T</span></h1>""", unsafe_allow_html=True)
st.markdown("<h1 class='animate-text delay-3' style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px; margin-bottom: 0;'>Operations management <br><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='animate-text delay-4' style='text-align: center; font-size: 16px; color: #64748B; max-width: 520px; margin: 20px auto 40px auto;'>Welcome to the central command unit for BART. Seamlessly organize branch metrics, manage shift requirements, and deploy localized branch parameters.</p>", unsafe_allow_html=True)

# =========================================================
# CARDS - Assuming no changes requested here
# =========================================================
grid_left, grid_right = st.columns(2, gap="large")
with grid_left:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">Staff Control """, unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; color: #64748B; margin-bottom: 25px;'>Log daily updates, run item balance checkers, and communicate data parameters.</p>", unsafe_allow_html=True)
    if st.button("Access Staff Control →", use_container_width=True, key="staff_btn"): st.switch_page("pages/staff_dashboard.py")
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
# PASSWORD VERIFICATION SHEET - Assuming no changes requested here
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
