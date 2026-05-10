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
# SESSION STATE (UNCHANGED)
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
# YOUR ORIGINAL RED DESIGN (UNCHANGED)
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {
    visibility: hidden;
}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* HERO */
.hero {
    background: white;
    padding: 60px;
    text-align: center;
    border-radius: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.hero h1 {
    font-size: 70px;
    color: #C0392B;
    margin: 0;
}

.hero h2 {
    font-size: 22px;
    color: #2C2A28;
}

/* SECTION */
.section {
    background: white;
    padding: 25px;
    margin-top: 15px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    text-align: center;
}

/* BUTTON STYLE (YOUR ORIGINAL RED LOOK KEPT) */
div.stButton > button {
    width: 100%;
    height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color: white;
    font-weight: 700;
    border: none;
}

div.stButton > button:hover {
    opacity: 0.9;
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
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ✅ FIXED DESKTOP BUTTON LAYOUT (ONLY CHANGE)
# =========================================================

# CENTER CONTAINER (keeps desktop clean, doesn't affect mobile)
left, center, right = st.columns([1, 4, 1])

with center:
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👨‍💼 Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    with col2:
        if st.button("📦 Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    with col3:
        if st.button("🤖 AI Assistant"):
            st.session_state.ai_open = not st.session_state.ai_open

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
# FOOTER (UNCHANGED)
# =========================================================
st.markdown("""
<div class="section">
    <h3>Our Experience</h3>
    <p>Premium café experience in Jeddah</p>
</div>

<div class="section">
    <h3>Visit Us</h3>
    <p>bart.sa • Jeddah Branches</p>
</div>
""", unsafe_allow_html=True)
