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
# CSS ARCHITECTURE
# =========================================================
st.markdown("""<style>
/* Force transparency across all Streamlit containers */
.stApp, .stAppViewContainer, .main, .block-container, [data-testid="stAppViewContainer"] {
    background: transparent !important;
}

/* Background Layer */
.background-layer {
    position: fixed !important;
    top: 0 !important; left: 0 !important;
    width: 100vw !important; height: 100vh !important;
    z-index: -9999 !important;
    background-color: #FFFFFF !important;
    background-image: url("https://upload.wikimedia.org/wikipedia/commons/8/83/World_map_blank_gmt.svg") !important;
    background-size: cover !important;
    background-position: center !important;
    opacity: 0.15 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    pointer-events: none !important;
}

/* Orbits */
.orbit-wrap { position: relative !important; }
.orbit { 
    position: absolute !important; 
    border: 1px solid rgba(46, 212, 122, 0.25) !important; 
    border-radius: 50% !important; 
    animation: spin linear infinite !important;
    left: 50% !important; top: 50% !important; 
    transform: translate(-50%, -50%) !important;
}
.o1 { width: 200px; height: 200px; animation-duration: 20s; }
.o2 { width: 350px; height: 350px; animation-duration: 30s; }
.o3 { width: 500px; height: 500px; animation-duration: 40s; }
.o4 { width: 650px; height: 650px; animation-duration: 50s; }
.o5 { width: 800px; height: 800px; animation-duration: 65s; }
.o6 { width: 950px; height: 950px; animation-duration: 85s; }
.o7 { width: 1100px; height: 1100px; animation-duration: 110s; }

@keyframes spin { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes counter { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }
.icon { animation: counter linear infinite; font-size: 24px; position: absolute; top: -12px; left: 50%; margin-left: -12px; }

/* --- YOUR ORIGINAL CSS --- */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display: none !important; visibility: hidden !important;}
@keyframes fadeInUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
.animate-text { animation: fadeInUp 0.8s ease-out forwards; opacity: 0; }
.delay-1 { animation-delay: 0.2s; } .delay-2 { animation-delay: 0.4s; } .delay-3 { animation-delay: 0.6s; } .delay-4 { animation-delay: 0.8s; }
@keyframes breathe-bold { 0%, 100% { transform: scale(1); text-shadow: 0 0 10px rgba(46, 212, 122, 0.2); } 50% { transform: scale(1.05); text-shadow: 0 0 30px rgba(46, 212, 122, 0.6); } }
.bart-logo { display: inline-block; animation: breathe-bold 2s ease-in-out infinite; background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; cursor: default; font-weight: 900 !important; letter-spacing: -2px; }
@keyframes rotate { 100% { transform: rotate(360deg); } }
.card-glow { position: relative; padding: 2px; background: #F8F9FA; border-radius: 22px; overflow: hidden; }
.card-glow::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, #2ED47A, transparent 30%); animation: rotate 4s linear infinite; }
.card-content { position: relative; background: #F8F9FA; border-radius: 20px; padding: 30px; z-index: 1; }
div.stButton > button, div[data-testid="stFormSubmitButton"] > button { position: relative; height: 54px !important; border-radius: 50px !important; border: none !important; background: #20C997 !important; color: #FFFFFF !important; font-weight: 900 !important; text-transform: uppercase !important; letter-spacing: 2px !important; overflow: hidden; z-index: 1; }
div.stButton > button::before, div[data-testid="stFormSubmitButton"] > button::before { content: ''; position: absolute; z-index: -1; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, #2ED47A, transparent 50%); animation: rotate 3s linear infinite; }
div.stButton > button:hover { transform: translateY(-2px); }
.block-container {max-width: 900px !important; padding-top: 5rem !important;}
div[data-testid="stForm"] {background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 24px !important; padding: 35px !important;}
div[data-testid="stTextInput"] input {border-radius: 50px !important; background-color: #F8FAFC !important; height: 52px !important; text-align: center !important;}
</style>""", unsafe_allow_html=True)

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

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# BACKGROUND LAYER
# =========================================================
st.markdown("""
<div class="background-layer">
    <div class="orbit-wrap">
        <div class="orbit o1"><div class="icon" style="animation-duration: 20s;">🌍</div></div>
        <div class="orbit o2"><div class="icon" style="animation-duration: 30s;">🪐</div></div>
        <div class="orbit o3"><div class="icon" style="animation-duration: 40s;">☄️</div></div>
        <div class="orbit o4"><div class="icon" style="animation-duration: 50s;">🌑</div></div>
        <div class="orbit o5"><div class="icon" style="animation-duration: 65s;">☀️</div></div>
        <div class="orbit o6"><div class="icon" style="animation-duration: 85s;">🌕</div></div>
        <div class="orbit o7"><div class="icon" style="animation-duration: 110s;">🌟</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# UI CONTENT (Original Structure)
# =========================================================
st.markdown("<div class='animate-text delay-1' style='text-align: center;'><span style='background: rgba(59, 33, 230, 0.08); color: #3B21E6; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700; letter-spacing: 1px;'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)
st.markdown("""<h1 class='animate-text delay-2' style='text-align: center; font-size: 88px; font-weight: 800; color: #111111; margin-top: 5px; margin-bottom: -15px; letter-spacing: -2.5px;'><span class='bart-logo'>B A R T</span></h1>""", unsafe_allow_html=True)
st.markdown("<h1 class='animate-text delay-3' style='text-align: center; font-size: 58px; font-weight: 800; color: #111111; margin-top: 15px; margin-bottom: 0;'>Operations management <br><span style='background: linear-gradient(90deg, #2ED47A 0%, #20C997 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='animate-text delay-4' style='text-align: center; font-size: 16px; color: #64748B; max-width: 520px; margin: 20px auto 40px auto;'>Welcome to the central command unit for BART.</p>", unsafe_allow_html=True)

grid_left, grid_right = st.columns(2, gap="large")
with grid_left:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">Staff Control """, unsafe_allow_html=True)
    if st.button("Access Staff Control →", use_container_width=True, key="staff_btn"): st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div></div>', unsafe_allow_html=True)
with grid_right:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">HQ Administration""", unsafe_allow_html=True)
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"Console Locked ({remaining}s) 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

if st.session_state.show_mgmt_password:
    st.write("---")
    st.markdown('<div id="security_form"></div>', unsafe_allow_html=True)
    sheet_left, sheet_center, sheet_right = st.columns([1, 5, 1])
    with sheet_center:
        with st.form("pass_form", clear_on_submit=True):
            password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter System Password")
            if st.form_submit_button("Verify & Open", use_container_width=True):
                if password_input == st.secrets["MANAGER_PASSWORD"]:
                    st.session_state.show_mgmt_password = False
                    st.switch_page("pages/management_dashboard.py")
                else: st.error("Access Refused: Invalid token signature.")
