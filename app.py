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
/* Hide default Streamlit elements safely */
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; visibility: hidden !important; }
#MainMenu, footer, header { visibility: hidden; }

/* Global reset & padding fixes */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] { 
    background: transparent !important; 
}

.block-container { 
    max-width: 100% !important; 
    padding-top: 2rem !important; 
    padding-bottom: 2rem !important;
    padding-left: 5% !important;  
    padding-right: 5% !important; 
}

/* RESPONSIVE HEADERS & BRANDING */
.internal-badge {
    display: inline-block;
    background: rgba(59, 33, 230, 0.08); 
    color: #3B21E6; 
    padding: 6px 16px; 
    border-radius: 100px; 
    font-size: 11px; 
    font-weight: 700; 
    letter-spacing: 1px;
}

.logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    margin-bottom: 5px;
}

.bart-logo { 
    display: inline-block; 
    font-size: clamp(48px, 8vw, 88px) !important;
    font-weight: 900 !important; 
    letter-spacing: -2px; 
    animation: breathe-bold 2s ease-in-out infinite; 
    background: linear-gradient(90deg, #F75D59 0%, #F75D59 100%); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
    cursor: default; 
}

.brand-wrapper {
    position: relative;
    display: inline-flex;
    align-items: center;
}

.oval-bg {
    position: absolute;
    width: 24px;
    height: 16px;
    background-color: #8B5CF6;
    border-radius: 50%;
    transform: rotate(-30deg);
    top: 20%;
    right: -15px;
    z-index: 1;
}

.registered {
    font-size: 20px;
    font-weight: 900;
    color: #8B5CF6 !important;
    position: relative;
    z-index: 2;
    margin-left: 18px;
}

.sub-header-title {
    font-size: clamp(32px, 5vw, 58px) !important;
    font-weight: 800;
    color: #111111;
    line-height: 1.1;
    margin-top: 15px;
}

.hero-paragraph {
    font-size: clamp(14px, 2vw, 16px);
    color: #64748B;
    max-width: 520px;
    margin: 20px auto 40px auto;
    padding: 0 15px;
}

/* MOBILE FRIENDLY RESPONSIVE BACKGROUND */
.background-layer { 
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -9999; 
    overflow: hidden; background-color: #F8FAFC; 
}
.orbit-wrap {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
    max-width: 100vw;
}
.orbit { position: absolute; border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 50%; left: 50%; top: 50%; transform: translate(-50%, -50%); }
.o1 { width: 150px; height: 150px; }
.o2 { width: 280px; height: 280px; }
.o3 { width: 420px; height: 420px; }
.o4 { width: 600px; height: 600px; }
.o5 { width: 800px; height: 800px; }

/* RESPONSIVE CARDS */
.card-glow { 
    position: relative; 
    padding: 2px; 
    background: #FFFFFF; 
    border-radius: 22px; 
    overflow: hidden; 
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px; /* Essential padding for stacked layout on mobile */
}
.card-glow::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, #F75D59, transparent 30%); animation: rotate 4s linear infinite; }
.card-content { position: relative; background: #FFFFFF; border-radius: 20px; padding: 25px 20px; z-index: 1; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between; }

/* BUTTONS */
div.stButton > button { 
    height: 50px !important; 
    border-radius: 50px !important; 
    border: none !important; 
    background: #F75D59 !important; 
    color: #FFFFFF !important; 
    font-weight: 900 !important; 
    text-transform: uppercase !important; 
    letter-spacing: 1px !important; 
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
}
div.stButton > button:hover {
    transform: scale(1.02) translateY(-1px);
    background: #e14c48 !important; 
    box-shadow: 0 8px 15px rgba(247, 93, 89, 0.35) !important;
}

/* ANIMATIONS */
@keyframes rotate { 100% { transform: rotate(360deg); } }
@keyframes breathe-bold { 0%, 100% { transform: scale(1); text-shadow: 0 0 10px rgba(247, 93, 89, 0.25); } 50% { transform: scale(1.03); text-shadow: 0 0 20px rgba(247, 93, 89, 0.45); } }
@keyframes fadeInUp { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
.animate-text { animation: fadeInUp 0.6s ease-out forwards; opacity: 0; }
.delay-1 { animation-delay: 0.1s; } .delay-2 { animation-delay: 0.2s; } .delay-3 { animation-delay: 0.3s; } .delay-4 { animation-delay: 0.4s; }

/* Force standard text alignment over hard structural columns for password forms on small screens */
@media (max-width: 768px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .card-content { min-height: auto; }
}
</style>""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
st.session_state.authenticated = True
if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0
if "show_hr_password" not in st.session_state: st.session_state.show_hr_password = False

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# BACKGROUND LAYER (Responsive Opacity & Size)
# =========================================================
st.markdown("""
<div class="background-layer">
    <div class="orbit-wrap">
        <div class="orbit o1"></div>
        <div class="orbit o2"></div>
        <div class="orbit o3"></div>
        <div class="orbit o4"></div>
        <div class="orbit o5"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ANIMATED HEADER & UI (Using fluid sizing tags)
# =========================================================
st.markdown("<div class='animate-text delay-1' style='text-align: center;'><span class='internal-badge'>INTERNAL STAFF NETWORK</span></div>", unsafe_allow_html=True)

st.markdown("""
<div class="logo-container animate-text delay-2">
    <div class="brand-wrapper">
        <span class="bart-logo">B A R T</span>
        <span class="oval-bg"></span>
        <span class="registered">®</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h2 class='animate-text delay-3 sub-header-title' style='text-align: center;'>Operations management <br><span style='background: linear-gradient(90deg, #F75D59 0%, #F75D59 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>just got easier.</span></h2>", unsafe_allow_html=True)
st.markdown("<p class='animate-text delay-4 hero-paragraph' style='text-align: center;'>Welcome to the central command unit for BART. Seamlessly organize branch metrics, manage shift requirements, and deploy localized branch parameters.</p>", unsafe_allow_html=True)

# =========================================================
# CARDS GRID (Automatically drops to 1 stacked column on mobile)
# =========================================================
grid_left, grid_center, grid_right = st.columns([1, 1, 1], gap="medium")

with grid_left:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">Staff Control
    <p style='font-family: sans-serif; font-size: 14px; color: #64748B; margin-top: 10px; font-weight: 400;'>Log daily updates, run item balance checkers, and communicate data parameters.</p></div>""", unsafe_allow_html=True)
    if st.button("Access Staff Control →", use_container_width=True, key="staff_btn"): 
        st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div></div>', unsafe_allow_html=True)

with grid_center:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">HR Management
    <p style='font-family: sans-serif; font-size: 14px; color: #64748B; margin-top: 10px; font-weight: 400;'>Manage employee records, oversee Schedule systems, and coordinate staff onboarding files.</p></div>""", unsafe_allow_html=True)
    if st.button("Unlock HR Portal →", use_container_width=True, key="hr_btn"):
        st.session_state.show_hr_password = True
        st.session_state.show_mgmt_password = False 
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

with grid_right:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center; font-family: 'Times New Roman', Times, serif; color: #1E293B; font-size: 20px; font-weight: 700;">HQ Administration
    <p style='font-family: sans-serif; font-size: 14px; color: #64748B; margin-top: 10px; font-weight: 400;'>Analyze operational logs, secure administrative configurations, and edit global secrets.</p></div>""", unsafe_allow_html=True)
    if is_mgmt_locked():
        remaining = int(st.session_state.mgmt_lock_until - time.time())
        st.button(f"Console Locked ({remaining}s) 🔒", disabled=True, use_container_width=True, key="mgmt_btn")
    else:
        if st.button("Unlock Admin Panel →", use_container_width=True, key="mgmt_btn"):
            st.session_state.show_mgmt_password = True
            st.session_state.show_hr_password = False
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# =========================================================
# PASSWORD VERIFICATION SHEETS (Refactored Form Columns)
# =========================================================

# 1. HR SECURITY VERIFICATION
if st.session_state.show_hr_password:
    st.write("---")
    st.markdown('<div id="security_form_hr"></div>', unsafe_allow_html=True)
    st.components.v1.html("""<script>setTimeout(function() {var el = window.parent.document.getElementById('security_form_hr'); if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }}, 100);</script>""", height=0)
    
    # Use a dynamic form container layout that naturally collapses
    _, sheet_center, _ = st.columns([0.1, 0.8, 0.1] if st.experimental_user.get("device") == "mobile" else [1, 2, 1])
    with sheet_center:
        with st.form("hr_pass_form", clear_on_submit=True):
            st.markdown("<h3 style='text-align: center; color: #1E293B; font-weight: 700; font-size: 20px; margin-bottom: 5px;'>HR Security Verification</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748B; font-size: 13px; margin-bottom: 20px;'>Input administrative access credentials to proceed into HR environments.</p>", unsafe_allow_html=True)
            
            hr_password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter HR System Password", key="hr_pwd_field")
            
            st.write("##")
            action_col1, action_col2 = st.columns(2, gap="small")
            with action_col2:
                if st.form_submit_button("Abort HR Login", use_container_width=True):
                    st.session_state.show_hr_password = False
                    st.rerun()
            with action_col1:
                if st.form_submit_button("Verify & Open HR", use_container_width=True):
                    if hr_password_input == st.secrets["HR_PASSWORD"]:
                        st.session_state.show_hr_password = False
                        st.switch_page("pages/hr_dashboard.py")
                    else:
                        st.error("Access Refused: Invalid token signature.")

# 2. HQ ADMINISTRATION SECURITY VERIFICATION
if st.session_state.show_mgmt_password:
    st.write("---")
    st.markdown('<div id="security_form"></div>', unsafe_allow_html=True)
    st.components.v1.html("""<script>setTimeout(function() {var el = window.parent.document.getElementById('security_form'); if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }}, 100);</script>""", height=0)
    
    _, sheet_center, _ = st.columns([0.1, 0.8, 0.1] if st.experimental_user.get("device") == "mobile" else [1, 2, 1])
    with sheet_center:
        with st.form("pass_form", clear_on_submit=True):
            st.markdown("<h3 style='text-align: center; color: #1E293B; font-weight: 700; font-size: 20px; margin-bottom: 5px;'>Administration Security Verification</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748B; font-size: 13px; margin-bottom: 20px;'>Input administrative access credentials to proceed into critical system files.</p>", unsafe_allow_html=True)
            
            password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter Administration Password", key="mgmt_pwd_field")
            
            st.write("##")
            action_col1, action_col2 = st.columns(2, gap="small")
            with action_col2:
                if st.form_submit_button("Abort Login", use_container_width=True):
                    st.session_state.show_mgmt_password = False
                    st.rerun()
            with action_col1:
                if st.form_submit_button("Verify & Open", use_container_width=True):
                    if password_input == st.secrets["MANAGER_PASSWORD"]:
                        st.session_state.show_mgmt_password = False
                        st.switch_page("pages/management_dashboard.py")
                    else:
                        st.error("Access Refused: Invalid token signature.")
