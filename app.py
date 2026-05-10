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
# STYLE (UNCHANGED - YOUR DESIGN SAFE)
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

.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    text-align: center;
}

div.stButton > button {
    width:100%;
    height:52px;
    border-radius:14px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color:white;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN (kept simple)
# =========================================================
if not st.session_state.authenticated:

    st.title("BART Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.authenticated = True
        st.rerun()

    st.stop()

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <p>Coffee • French Toast • Fresh Bites</p>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# MAIN BUTTONS
# =========================================================
col1, col2 = st.columns(2)

with col1:
    if st.button("👨‍💼 Staff Dashboard", key="staff_btn"):
        st.switch_page("staff_dashboard")

with col2:
    # ✅ FIXED MANAGEMENT BUTTON
    if st.button("📦 Management Dashboard", key="mgmt_btn"):
        st.switch_page("management_dashboard")

# =========================================================
# AI TOGGLE BUTTON (UNCHANGED BEHAVIOR)
# =========================================================
st.markdown("---")

col_ai = st.columns([1,2,1])[1]

with col_ai:
    if st.button("🤖 AI Assistant"):
        st.session_state.ai_open = not st.session_state.ai_open

# =========================================================
# AI INLINE CHAT (NO DESIGN BREAK)
# =========================================================
if st.session_state.ai_open:

    st.markdown("## 🤖 BART AI Assistant")

    for sender, msg in st.session_state.chat[-20:]:
        icon = "🧑" if sender == "You" else "🤖"
        st.markdown(f"**{icon} {sender}:** {msg}")

    user_input = st.text_input("Ask something...", key="ai_input")

    if st.button("Send AI") and user_input:

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

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<div class="section">
    <h3>Our Experience</h3>
    <p>Premium café experience in Jeddah.</p>
</div>

<div class="section">
    <h3>Visit Us</h3>
    <p>bart.sa • Jeddah Branches</p>
</div>
""", unsafe_allow_html=True)
