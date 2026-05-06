import streamlit as st
from ai_core import run_ai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- STYLES (UI ONLY) ----------------
st.markdown("""
<style>

#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1100px;
}

.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 60px 30px;
    border-radius: 26px;
    text-align: center;
    box-shadow: 0 18px 50px rgba(0,0,0,0.08);
    margin-top: 20px;
}

.hero h1 {
    font-size: 70px;
    font-weight: 900;
    letter-spacing: 8px;
    color: #C0392B;
    margin-bottom: 5px;
}

.hero h2 {
    font-size: 20px;
    color: #2C2A28;
    font-weight: 600;
}

.hero p {
    font-size: 15px;
    color: #555;
    max-width: 750px;
    margin: auto;
    line-height: 1.6;
}

.chat-box {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.06);
    margin-top: 20px;
}

div.stButton > button {
    height: 50px;
    width: 200px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    background: #2C2A28;
    color: white;
    border: none;
}

div.stButton > button:hover {
    background: #C0392B;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>
        A modern café experience built for speed, quality, and taste.<br>
        📍 Jeddah • 🌐 bart.sa
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- CHAT INPUT ----------------
st.markdown("## Talk to BART AI")
user_input = st.text_input("Type your message...")

# ---------------- AI CONNECTION (ONLY LOGIC BRIDGE) ----------------
if user_input:
    context = {
        "revenue": 0,
        "items": 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append({"role": "user", "msg": user_input})
    st.session_state.chat.append({"role": "ai", "msg": response})

# ---------------- CHAT DISPLAY (HUMAN STYLE UX) ----------------
st.markdown("---")
for c in st.session_state.chat[-12:]:
    if c["role"] == "user":
        st.markdown(f"**You:** {c['msg']}")
    else:
        st.markdown(f"**BART AI:** {c['msg']}")

# ---------------- SIMPLE LOGIN NAV ----------------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")
