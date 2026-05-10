import streamlit as st
from ai_core import run_ai

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# SESSION STATE (UNCHANGED LOGIC)
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
# STYLE (CARD UI ONLY)
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {
    visibility: hidden;
}

.stApp {
    background: linear-gradient(135deg,#F7F1EA,#FFFFFF);
    font-family:Segoe UI;
}

/* HERO */
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

/* CARD STYLE */
.card {
    background: white;
    padding: 30px;
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    text-align: center;
    transition: 0.2s;
    cursor: pointer;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 35px rgba(0,0,0,0.12);
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 10px;
}

.card-btn button {
    width: 100%;
    height: 45px;
    border-radius: 12px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color: white;
    font-weight: 700;
    border: none;
}

/* AI SECTION */
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
# LOGIN (UNCHANGED LOGIC)
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
# HERO (UNCHANGED)
# =========================================================
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <p>Coffee • French Toast • Fresh Bites</p>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CARD DASHBOARD UI (OPTION 2 IMPLEMENTATION)
# =========================================================

col1, col2, col3 = st.columns(3)

# ================= STAFF CARD =================
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👨‍💼 Staff Dashboard</div>', unsafe_allow_html=True)

    if st.button("Open Staff", key="staff_card"):
        st.switch_page("pages/staff_dashboard.py")

    st.markdown('</div>', unsafe_allow_html=True)

# ================= MANAGEMENT CARD =================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📦 Management Dashboard</div>', unsafe_allow_html=True)

    if st.button("Open Management", key="mgmt_card"):
        st.switch_page("pages/management_dashboard.py")

    st.markdown('</div>', unsafe_allow_html=True)

# ================= AI CARD =================
with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🤖 AI Assistant</div>', unsafe_allow_html=True)

    if st.button("Open AI", key="ai_card"):
        st.session_state.ai_open = not st.session_state.ai_open

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# AI CHAT (UNCHANGED LOGIC)
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
<div style="margin-top:25px; background:white; padding:25px; border-radius:15px; text-align:center;">
    <h3>Our Experience</h3>
    <p>Premium café experience in Jeddah</p>
</div>
""", unsafe_allow_html=True)
