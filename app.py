import streamlit as st
import hashlib
from ai_core import run_ai

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
    layout="wide",
)

# =========================================================
# STATE
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================================================
# SIMPLE STYLE
# =========================================================
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.hero {
    padding:40px;
    text-align:center;
    background:#fff;
    border-radius:20px;
    box-shadow:0 10px 30px rgba(0,0,0,0.1);
}

.ai-panel {
    position: fixed;
    right: 20px;
    bottom: 20px;
    width: 350px;
    height: 500px;
    background: white;
    border-radius: 15px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    padding: 15px;
    overflow-y: auto;
    z-index: 999;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN (simple for demo)
# =========================================================
if not st.session_state.authenticated:

    st.title("BART LOGIN")

    u = st.text_input("User")
    p = st.text_input("Pass", type="password")

    if st.button("Login"):
        st.session_state.authenticated = True
        st.rerun()

    st.stop()

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <p>Coffee • French Toast • Fresh Bites</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# BUTTONS
# =========================================================
c1, c2, c3 = st.columns(3)

with c1:
    st.button("Staff Dashboard")

with c2:
    st.button("Management Dashboard")

with c3:
    if st.button("🤖 AI Assistant"):
        st.session_state.ai_open = True

# =========================================================
# 🤖 AI PANEL (THIS IS THE FIX)
# =========================================================
if st.session_state.ai_open:

    with st.container():

        st.markdown("## 🤖 BART AI")

        if st.button("❌ Close AI"):
            st.session_state.ai_open = False
            st.rerun()

        # chat history
        for sender, msg in st.session_state.chat[-10:]:
            st.write(f"**{sender}:** {msg}")

        user_input = st.text_input("Ask something", key="ai_input")

        if st.button("Send AI") and user_input:

            context = {}

            response = run_ai(user_input, context)

            st.session_state.chat.append(("You", user_input))
            st.session_state.chat.append(("AI", response))

            st.rerun()
