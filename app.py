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
    background-color: #F8FAFC; 
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 400'%3E%3Cpath fill='%23CBD5E1' d='M100 100c50 0 50 50 100 50s50-50 100-50 50 50 100 50 50-50 100-50 50 50 100 50 50-50 100-50 50 50 100 50'/%3E%3C/svg%3E");
    background-size: cover; background-position: center; opacity: 0.6; 
}

/* Animations & UI */
@keyframes rotate { 100% { transform: rotate(360deg); } }
.card-glow { position: relative; padding: 2px; background: #FFFFFF; border-radius: 22px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); }
.card-glow::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, #2ED47A, transparent 30%); animation: rotate 4s linear infinite; }
.card-content { position: relative; background: #FFFFFF; border-radius: 20px; padding: 30px; z-index: 1; }

/* SHARED BUTTON ANIMATION */
div.stButton > button { 
    border: none !important; border-radius: 50px !important; font-weight: 900 !important; 
    text-transform: uppercase !important; letter-spacing: 2px !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}
div.stButton > button::before { display: none !important; }
div.stButton > button:hover { transform: scale(1.05) translateY(-2px); box-shadow: 0 10px 20px rgba(32, 201, 151, 0.3) !important; }
div.stButton > button:active { transform: scale(0.98) translateY(0); }

/* MAIN BUTTONS (Cards) */
div:not([data-testid="stForm"]) > div > div > div > div > div.stButton > button { height: 54px !important; background: #20C997 !important; color: #FFFFFF !important; }
div:not([data-testid="stForm"]) > div > div > div > div > div.stButton > button:hover { background: #19a37a !important; }

/* FORM BUTTONS (Small) */
[data-testid="stForm"] div.stButton > button { height: 40px !important; font-size: 12px !important; background: #20C997 !important; color: #FFFFFF !important; }
[data-testid="stForm"] div.stButton > button:hover { background: #19a37a !important; }
</style>""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
st.session_state.authenticated = True
if "show_mgmt_password" not in st.session_state: st.session_state.show_mgmt_password = False
if "mgmt_lock_until" not in st.session_state: st.session_state.mgmt_lock_until = 0

def is_mgmt_locked():
    return time.time() < st.session_state.mgmt_lock_until

# =========================================================
# UI
# =========================================================
st.markdown('<div class="background-layer"></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; font-size: 88px; font-weight: 800; color: #111111;'>B A R T</h1>", unsafe_allow_html=True)

grid_left, grid_right = st.columns(2, gap="large")
with grid_left:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center;"><h3>Staff Control</h3>""", unsafe_allow_html=True)
    if st.button("Access Staff Control →", use_container_width=True): st.switch_page("pages/staff_dashboard.py")
    st.markdown('</div></div>', unsafe_allow_html=True)
with grid_right:
    st.markdown("""<div class="card-glow"><div class="card-content" style="text-align: center;"><h3>HQ Administration</h3>""", unsafe_allow_html=True)
    if is_mgmt_locked():
        st.button(f"Locked ({int(st.session_state.mgmt_lock_until - time.time())}s)", disabled=True, use_container_width=True)
    else:
        if st.button("Unlock Admin Panel", use_container_width=True):
            st.session_state.show_mgmt_password = True
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

# =========================================================
# PASSWORD SHEET
# =========================================================
if st.session_state.show_mgmt_password:
    st.write("---")
    sheet_left, sheet_center, sheet_right = st.columns([1, 2, 1])
    with sheet_center:
        with st.form("pass_form"):
            password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter Password")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Abort Login", use_container_width=True):
                    st.session_state.show_mgmt_password = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Verify & Open", use_container_width=True):
                    if password_input == st.secrets.get("MANAGER_PASSWORD", "admin"):
                        st.switch_page("pages/management_dashboard.py")
                    else:
                        st.error("Invalid")
