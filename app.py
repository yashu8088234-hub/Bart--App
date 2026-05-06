import streamlit as st
from ai_core import run_ai
import streamlit.components.v1 as components

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

# ---------------- CHAT BACKEND (your existing logic) ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

user_input = st.text_input("Message", label_visibility="collapsed")
send = bool(user_input)

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

# ---------------- INFO ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy café environment with fast service and premium coffee experience.</p>
</div>

<div class="section">
<h2>Visit Us</h2>
<p>Find us in Jeddah branches or visit bart.sa for more information.</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🤖 FLOATING AI CHATBOT (DO NOT TOUCH MAIN UI)
# =========================================================

chat_widget = """
<style>

/* Floating button */
#ai-bot-btn {
    position: fixed;
    bottom: 25px;
    right: 25px;
    width: 60px;
    height: 60px;
    background: #C0392B;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-size: 26px;
    cursor: pointer;
    z-index: 999999;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

/* Chat window */
#ai-chat-window {
    position: fixed;
    bottom: 100px;
    right: 25px;
    width: 340px;
    height: 450px;
    background: white;
    border-radius: 16px;
    display: none;
    flex-direction: column;
    z-index: 999999;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    overflow: hidden;
}

/* Header */
#ai-chat-header {
    background: #C0392B;
    color: white;
    padding: 10px;
    font-weight: bold;
}

/* Body */
#ai-chat-body {
    flex: 1;
    padding: 10px;
    overflow-y: auto;
    font-family: Arial;
    font-size: 14px;
}

/* Input */
#ai-chat-input {
    width: 100%;
    border: none;
    padding: 12px;
    outline: none;
    border-top: 1px solid #eee;
}

</style>

<div id="ai-bot-btn" onclick="toggleChat()">🤖</div>

<div id="ai-chat-window">
    <div id="ai-chat-header">BART AI Assistant</div>
    <div id="ai-chat-body">Hi 👋 I can help you with stock & café info.</div>
    <input id="ai-chat-input" placeholder="Type a message..." />
</div>

<script>

function toggleChat() {
    var win = document.getElementById("ai-chat-window");
    if (win.style.display === "flex") {
        win.style.display = "none";
    } else {
        win.style.display = "flex";
        win.style.flexDirection = "column";
    }
}

</script>
"""

components.html(chat_widget, height=0)
