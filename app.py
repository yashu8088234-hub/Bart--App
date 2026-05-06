import streamlit as st
from ai_core import run_ai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- GLOBAL STYLES ----------------
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
    padding: 1.2rem 2rem !important;
    max-width: 1100px;
    margin: auto;
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
    letter-spacing: 8px;
    color: #C0392B;
    margin: 0;
}

.hero h2 {
    font-size: 22px;
    color: #2C2A28;
    margin-top: 10px;
}

.hero p {
    font-size: 15px;
    color: #555;
    max-width: 750px;
    margin: 10px auto 0;
    line-height: 1.6;
}

/* LOGIN */
.login-row {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 20px 0 35px;
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

/* FLOATING CHAT */
.chat-float {
    position: fixed;
    bottom: 25px;
    right: 25px;
    width: 360px;
    height: 520px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.25);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.chat-header {
    background: #2C2A28;
    color: white;
    padding: 12px;
    font-weight: bold;
    text-align: center;
}

.chat-body {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    font-size: 14px;
}

.chat-input {
    display: flex;
    border-top: 1px solid #eee;
}

.chat-input input {
    flex: 1;
    padding: 10px;
    border: none;
    outline: none;
}

.chat-input button {
    width: 60px;
    background: #C0392B;
    color: white;
    border: none;
    cursor: pointer;
}

/* SECTION */
.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}

.section h2 {
    color: #C0392B;
    text-align: center;
}

.section p {
    color: #555;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>A modern café experience built for speed, quality, and taste. 📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
st.markdown('<div class="login-row">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- FLOATING CHAT UI ----------------
st.markdown('<div class="chat-float">', unsafe_allow_html=True)

st.markdown('<div class="chat-header">BART AI Assistant</div>', unsafe_allow_html=True)

# CHAT HISTORY
st.markdown('<div class="chat-body">', unsafe_allow_html=True)

for sender, msg in st.session_state.chat[-15:]:
    if sender == "You":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**AI:** {msg}")

st.markdown('</div>', unsafe_allow_html=True)

# INPUT
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask something...")
    send = st.form_submit_button("➤")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- AI LOGIC ----------------
if send and user_input:
    context = {
        "revenue": 0,
        "items": 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))

# ---------------- INFO ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy café environment with fast service and premium coffee experience.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="section">
<h2>Visit Us</h2>
<p>Find us in Jeddah branches or visit bart.sa for more information.</p>
</div>
""", unsafe_allow_html=True)
