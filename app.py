import streamlit as st
import hashlib
from ai_core import run_ai

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
    layout="wide"
)

# =========================================================
# SESSION STATE
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "chat" not in st.session_state:
    st.session_state.chat = []

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if "all_data" not in st.session_state:
    st.session_state.all_data = []

if "branches" not in st.session_state:
    st.session_state.branches = []

if "DAILY_ITEMS" not in st.session_state:
    st.session_state.DAILY_ITEMS = {}

if "WEEKLY_ITEMS" not in st.session_state:
    st.session_state.WEEKLY_ITEMS = {}

# =========================================================
# STYLE (YOUR DESIGN KEPT)
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {visibility:hidden;}

.stApp {
    background: linear-gradient(135deg,#F7F1EA,#FFFFFF);
    font-family:Segoe UI;
}

.hero {
    background:white;
    padding:60px;
    text-align:center;
    border-radius:25px;
    box-shadow:0 10px 30px rgba(0,0,0,0.1);
    margin-bottom:20px;
}

.hero h1 {
    font-size:70px;
    color:#C0392B;
    margin:0;
}

.section {
    background:white;
    padding:25px;
    border-radius:15px;
    margin-top:15px;
    box-shadow:0 5px 20px rgba(0,0,0,0.08);
}

/* BUTTON */
div.stButton > button {
    width:100%;
    height:52px;
    border-radius:12px;
    background:linear-gradient(135deg,#2C2A28,#C0392B);
    color:white;
    font-weight:700;
}

.ai-box {
    background:white;
    padding:20px;
    border-radius:18px;
    margin-top:20px;
    box-shadow:0 10px 25px rgba(0,0,0,0.1);
}

.chat-msg {
    padding:10px;
    margin:5px 0;
    border-radius:10px;
}

.user {
    background:#f1f1f1;
}

.ai {
    background:#ffecec;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN (simple)
# =========================================================
if not st.session_state.authenticated:
    st.title("BART Login")

    u = st.text_input("User")
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
    st.button("👨‍💼 Staff Dashboard")

with col2:
    st.button("📦 Management Dashboard")

# =========================================================
# ⭐ AI TOGGLE BUTTON (SAME BUTTON OPENS/CLOSES)
# =========================================================
if st.button("🤖 AI Assistant (Chat Toggle)"):
    st.session_state.ai_open = not st.session_state.ai_open

# =========================================================
# 🧠 INLINE AI CHAT (NO BOX, NO SIDEBAR)
# =========================================================
if st.session_state.ai_open:

    st.markdown("## 🤖 BART AI Assistant")

    st.markdown('<div class="ai-box">', unsafe_allow_html=True)

    # CHAT HISTORY
    for sender, msg in st.session_state.chat[-15:]:
        css = "user" if sender == "You" else "ai"
        st.markdown(f'<div class="chat-msg {css}"><b>{sender}:</b> {msg}</div>', unsafe_allow_html=True)

    # INPUT
    user_input = st.text_input("Ask something...", key="chat_input")

    if st.button("Send"):
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
# FOOTER SECTIONS (UNCHANGED IDEA)
# =========================================================
st.markdown("""
<div class="section">
    <h3>Our Experience</h3>
    <p>Relax in a cozy café environment with premium service.</p>
</div>

<div class="section">
    <h3>Visit Us</h3>
    <p>Jeddah Branches • bart.sa</p>
</div>
""", unsafe_allow_html=True)
