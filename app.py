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
    "view": "home",   # ⭐ INTERNAL ROUTING SYSTEM
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
# STYLE (YOUR ORIGINAL DESIGN KEPT)
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
}

.hero h1 {
    font-size:70px;
    color:#C0392B;
    margin:0;
}

.section {
    background:white;
    padding:25px;
    margin-top:15px;
    border-radius:15px;
    box-shadow:0 5px 20px rgba(0,0,0,0.08);
    text-align:center;
}

div.stButton > button {
    width:100%;
    height:52px;
    border-radius:14px;
    background:linear-gradient(135deg,#2C2A28,#C0392B);
    color:white;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.title("BART Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.authenticated = True
        st.session_state.view = "home"
        st.rerun()

    st.stop()

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <p>Coffee • French Toast • Fresh Bites</p>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# NAVIGATION (NO switch_page → ZERO ERRORS)
# =========================================================
col1, col2 = st.columns(2)

with col1:
    if st.button("👨‍💼 Staff Dashboard"):
        st.session_state.view = "staff"

with col2:
    if st.button("📦 Management Dashboard"):
        st.session_state.view = "management"

# =========================================================
# RENDER VIEWS
# =========================================================

# -------------------------
# STAFF PAGE
# -------------------------
if st.session_state.view == "staff":
    st.subheader("👨‍💼 Staff Dashboard")

    st.markdown("""
    <div class="section">
        Staff dashboard content goes here.
    </div>
    """, unsafe_allow_html=True)

# -------------------------
# MANAGEMENT PAGE
# -------------------------
elif st.session_state.view == "management":
    st.subheader("📦 Management Dashboard")

    st.markdown("""
    <div class="section">
        Management dashboard content goes here.
    </div>
    """, unsafe_allow_html=True)

# -------------------------
# HOME PAGE
# -------------------------
else:

    # AI BUTTON (UNCHANGED LOGIC)
    st.markdown("---")

    col_ai = st.columns([1,2,1])[1]

    with col_ai:
        if st.button("🤖 AI Assistant"):
            st.session_state.ai_open = not st.session_state.ai_open

    # AI CHAT INLINE
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

    # FOOTER
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
