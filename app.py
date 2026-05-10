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
defaults = {
    "authenticated": False,
    "role": None,
    "chat": [],
    "all_data": [],
    "branches": [],
    "DAILY_ITEMS": {},
    "WEEKLY_ITEMS": {},
    "ai_open": False
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# STYLES (YOUR ORIGINAL - RESTORED)
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

/* HERO */
.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 60px 30px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 70px;
    font-weight: 900;
    color: #C0392B;
}

/* SECTIONS (YOUR ORIGINAL LOOK KEPT) */
.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    text-align: center;
}

/* BUTTON */
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
# LOGIN (kept simple for structure)
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <h1 style="text-align:center;color:#C0392B;">BART</h1>
        <p style="text-align:center;">Control Center</p>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.authenticated = True
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =========================================================
# HERO (YOUR ORIGINAL)
# =========================================================
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# MAIN BUTTONS (UNCHANGED STRUCTURE)
# =========================================================
col1, col2 = st.columns(2)

with col1:
    if st.button("👨‍💼 Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("📦 Management Dashboard"):
        st.switch_page("pages/management_dashboard.py")

# =========================================================
# ⭐ AI BUTTON (ADDED BELOW ALL BUTTONS)
# =========================================================
st.markdown("---")

col_ai = st.columns([1,2,1])[1]

with col_ai:
    if st.button("🤖 Open AI Assistant"):
        st.session_state.ai_open = True

# =========================================================
# 🧠 AI FLOATING PANEL (SAFE ADDITION ONLY)
# =========================================================
if st.session_state.ai_open:

    st.markdown("""
    <div style="
        position: fixed;
        right: 20px;
        bottom: 20px;
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

    st.markdown("## 🤖 BART AI")

    if st.button("❌ Close AI"):
        st.session_state.ai_open = False
        st.rerun()

    st.divider()

    # CHAT
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
# FOOTER SECTIONS (RESTORED ORIGINAL STRUCTURE)
# =========================================================
st.markdown("""
<div class="section">
    <h2>Our Experience</h2>
    <p>Relax in a cozy café environment with fast service and premium coffee experience.</p>
</div>

<div class="section">
    <h2>Visit Us</h2>
    <p>Find us in Jeddah branches or visit bart.sa</p>
</div>
""", unsafe_allow_html=True)
