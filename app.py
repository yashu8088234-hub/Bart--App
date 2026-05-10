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
# SESSION STATE
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "role" not in st.session_state:
    st.session_state.role = None

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

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

# =========================================================
# GLOBAL STYLES (YOUR ORIGINAL - UNCHANGED)
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {
    visibility: hidden;
}

[data-testid="stToolbar"] {
    display:none;
}

[data-testid="stSidebar"] {
    display:none;
}

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

.login-title h2 {
    text-align:center;
}

/* BUTTONS */
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

.hero h2 {
    font-size: 22px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <div class="login-logo">
            <h1>BART</h1>
        </div>
        <div class="login-title">
            <h2>Control Center</h2>
        </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if (
            username.lower() == st.secrets["MANAGER_USERNAME"].lower()
            and password == st.secrets["MANAGER_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.rerun()

        elif (
            username.lower() == st.secrets["STAFF_USERNAME"].lower()
            and password == st.secrets["STAFF_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.rerun()

        else:
            st.error("Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =========================================================
# MAIN DASHBOARD
# =========================================================
top1, top2 = st.columns([9,1])

with top2:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.chat = []
        st.session_state.ai_open = False
        st.rerun()

# HERO
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# MAIN BUTTONS
# =========================================================
col1, col2 = st.columns(2)

with col1:
    if st.button("👨‍💼 Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("📦 Management Dashboard"):
        st.switch_page("pages/management_dashboard.py")

# =========================================================
# ⭐ AI BUTTON (BELOW ALL BUTTONS - YOUR REQUEST)
# =========================================================
st.markdown("---")

col_ai = st.columns([1,2,1])[1]

with col_ai:
    if st.button("🤖 Open AI Assistant"):
        st.session_state.ai_open = True

# =========================================================
# 🤖 AI FLOATING PANEL (SAFE - DOES NOT BREAK DESIGN)
# =========================================================
if st.session_state.ai_open:

    st.markdown("""
    <div style="
        position: fixed;
        right: 25px;
        bottom: 25px;
        width: 370px;
        height: 520px;
        background: white;
        border-radius: 18px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.25);
        padding: 15px;
        overflow-y: auto;
        z-index: 9999;
    ">
    """, unsafe_allow_html=True)

    st.markdown("## 🤖 BART AI Assistant")

    if st.button("❌ Close AI"):
        st.session_state.ai_open = False
        st.rerun()

    st.divider()

    # CHAT HISTORY
    for sender, msg in st.session_state.chat[-15:]:
        icon = "🧑" if sender == "You" else "🤖"
        st.write(f"**{icon} {sender}:** {msg}")

    user_input = st.text_input("Ask something", key="ai_input")

    if st.button("Send") and user_input:

        context = {
            "cache_data": st.session_state.all_data,
            "branch_list": [b["BranchName"] for b in st.session_state.branches],
            "master_items": list(st.session_state.DAILY_ITEMS.keys()) +
                            list(st.session_state.WEEKLY_ITEMS.keys())
        }

        response = run_ai(user_input, context)

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<div class="hero" style="margin-top:20px;">
    <h2>Our Experience</h2>
    <p>Premium café experience in Jeddah</p>
</div>
""", unsafe_allow_html=True)
