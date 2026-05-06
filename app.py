import streamlit as st
from ai_core import run_ai

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- MODERN BRAND UI ----------------
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
    max-width: 1200px;
}

.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 70px 35px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
    margin-top: 20px;
    position: relative;
    overflow: hidden;
}

.hero h1 {
    font-size: 74px;
    font-weight: 900;
    letter-spacing: 10px;
    color: #C0392B;
}

.hero h2 {
    font-size: 22px;
    color: #2C2A28;
}

.hero p {
    font-size: 16px;
    color: #555;
    max-width: 800px;
    margin: auto;
    line-height: 1.7;
}

.login-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 30px;
}

div.stButton > button {
    height: 55px;
    width: 220px;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    background: #2C2A28;
    color: white;
    border: none;
}

div.stButton > button:hover {
    background: #C0392B;
}

.section {
    background: rgba(255,255,255,0.85);
    padding: 40px 25px;
    margin-top: 25px;
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.06);
    text-align: center;
}

.section h2 {
    color: #C0392B;
}

.section p {
    color: #555;
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
        📍 Jeddah • bart.sa
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
st.markdown('<div class="login-buttons">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- CHAT ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# input row (embedded, not full width)
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.text_input("Message...", label_visibility="collapsed")

with col2:
    send = st.button("➤")

if send and user_input:
    context = {
        "revenue": 0,
        "items": 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))

for sender, msg in st.session_state.chat[-10:]:
    if sender == "You":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**AI:** {msg}")

# ---------------- INFO SECTIONS ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax
