import streamlit as st
import hashlib
from ai_core import run_ai

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# SECURITY HELPERS
# =========================================================
def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def check_password(input_password: str, stored_password: str) -> bool:
    return hash_text(input_password) == hash_text(stored_password)

# =========================================================
# STYLES
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* LOGIN */
.login-container {
    max-width: 460px;
    margin: 80px auto;
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(12px);
    border-radius: 28px;
    padding: 45px 35px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
}

.login-logo h1 {
    font-size:70px;
    font-weight:900;
    letter-spacing:8px;
    color:#C0392B;
    text-align:center;
}

div.stButton > button {
    width:100%;
    height:52px;
    border-radius:14px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color:white;
    font-weight:700;
}

/* HERO */
.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 60px 30px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
}

.hero h1 {
    font-size: 70px;
    font-weight: 900;
    color: #C0392B;
    margin: 0;
}

.ai-button {
    display:flex;
    justify-content:center;
    margin-top:20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "authenticated": False,
    "role": None,
    "chat": [],
    "all_data": [],
    "branches": [],
    "DAILY_ITEMS": {},
    "WEEKLY_ITEMS": {},
    "login_attempts": 0,
    "ai_open": False   # ⭐ AI SIDEBAR TOGGLE
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

MAX_CHAT = 50

# =========================================================
# LOGIN PAGE
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <div class="login-logo">
            <h1>BART</h1>
        </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.session_state.login_attempts >= 5:
        st.error("Too many attempts. Restart app.")
        st.stop()

    if st.button("Login"):

        MANAGER_USER = st.secrets["MANAGER_USERNAME"].lower()
        MANAGER_PASS = st.secrets["MANAGER_PASSWORD"]

        STAFF_USER = st.secrets["STAFF_USERNAME"].lower()
        STAFF_PASS = st.secrets["STAFF_PASSWORD"]

        ok_manager = username.lower() == MANAGER_USER and check_password(password, MANAGER_PASS)
        ok_staff = username.lower() == STAFF_USER and check_password(password, STAFF_PASS)

        if ok_manager:
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.session_state.login_attempts = 0
            st.rerun()

        elif ok_staff:
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.session_state.login_attempts = 0
            st.rerun()

        else:
            st.session_state.login_attempts += 1
            st.error("Invalid credentials")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =========================================================
# MAIN DASHBOARD
# =========================================================
top1, top2 = st.columns([9, 1])

with top2:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.chat = []
        st.rerun()

# HERO
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <p>Coffee • French Toast • Fresh Bites</p>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🤖 AI BUTTON (OPEN SIDEBAR)
# =========================================================
st.markdown('<div class="ai-button">', unsafe_allow_html=True)

if st.button("🤖 Open AI Assistant"):
    st.session_state.ai_open = True
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# NAVIGATION BUTTONS
# =========================================================
c1, c2 = st.columns(2)

with c1:
    if st.button("👨‍💼 Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

with c2:
    if st.button("📦 Management Dashboard"):
        st.switch_page("pages/management_dashboard.py")

# =========================================================
# 🧠 AI SIDEBAR (TOGGLE SYSTEM)
# =========================================================
if st.session_state.ai_open:

    with st.sidebar:
        st.markdown("## 🤖 BART AI Assistant")

        # CLOSE BUTTON
        if st.button("❌ Close AI"):
            st.session_state.ai_open = False
            st.rerun()

        st.divider()

        # CHAT HISTORY
        for sender, msg in st.session_state.chat[-20:]:
            icon = "🧑" if sender == "You" else "🤖"
            st.markdown(f"**{icon} {sender}:** {msg}")

        st.divider()

        # CHAT INPUT
        with st.form("ai_chat_form", clear_on_submit=True):
            user_input = st.text_input("Ask something...")
            send = st.form_submit_button("Send")

        if send and user_input:

            context = {
                "cache_data": st.session_state.all_data[-100:],
                "branch_list": [b["BranchName"] for b in st.session_state.branches],
                "master_items": list(st.session_state.DAILY_ITEMS.keys()) +
                                list(st.session_state.WEEKLY_ITEMS.keys())
            }

            try:
                response = run_ai(user_input, context)
            except Exception as e:
                response = f"AI error: {str(e)}"

            st.session_state.chat.append(("You", user_input))
            st.session_state.chat.append(("AI", response))

            st.session_state.chat = st.session_state.chat[-MAX_CHAT:]

            st.rerun()

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<div style="
    background: rgba(255,255,255,0.9);
    padding: 30px;
    border-radius: 16px;
    margin-top: 25px;
    text-align:center;
">
    <h3 style="color:#C0392B;">Our Experience</h3>
    <p>Fast service, premium coffee, and modern café culture in Jeddah.</p>
</div>

<div style="
    background: rgba(255,255,255,0.9);
    padding: 30px;
    border-radius: 16px;
    margin-top: 15px;
    text-align:center;
">
    <h3 style="color:#C0392B;">Visit Us</h3>
    <p>bart.sa • Jeddah Branches</p>
</div>
""", unsafe_allow_html=True)
