import streamlit as st
from ai_core import run_ai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- SESSION ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- STYLES ----------------
st.markdown("""
<style>

/* hide streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}

/* background */
.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* HERO */
.hero {
    text-align: center;
    padding: 40px 20px;
    font-size: 48px;
    font-weight: 900;
    color: #C0392B;
}

/* CHAT AREA (KEY FIX) */
.chat-container {
    height: 65vh;
    overflow-y: auto;
    padding: 10px 20px;
    margin-bottom: 90px;
}

/* USER MESSAGE */
.user {
    text-align: right;
    background: #2C2A28;
    color: white;
    padding: 10px 14px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 70%;
    float: right;
    clear: both;
}

/* AI MESSAGE */
.ai {
    text-align: left;
    background: #F7F1EA;
    color: #222;
    padding: 10px 14px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 70%;
    float: left;
    clear: both;
}

/* FLOATING INPUT BAR */
.input-bar {
    position: fixed;
    bottom: 15px;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    max-width: 700px;
    display: flex;
    gap: 10px;
    z-index: 999;
}

/* input */
.input-bar input {
    flex: 1;
    height: 48px;
    border-radius: 14px;
    border: none;
    padding: 0 15px;
    font-size: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    outline: none;
}

/* SMALL AI BUTTON */
.input-bar button {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: none;
    background: #2C2A28;
    color: white;
    font-size: 18px;
    cursor: pointer;
}

.input-bar button:hover {
    background: #C0392B;
    transform: scale(1.05);
}

</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("<div class='hero'>BART</div>", unsafe_allow_html=True)

# ---------------- CHAT DISPLAY ----------------
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for sender, msg in st.session_state.chat[-30:]:
    if sender == "You":
        st.markdown(f"<div class='user'>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai'>{msg}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FLOATING INPUT ----------------
st.markdown("<div class='input-bar'>", unsafe_allow_html=True)

user_input = st.text_input("", placeholder="Message...", label_visibility="collapsed")
send = st.button("➤")

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- AI LOGIC ----------------
if send and user_input:
    st.session_state.chat.append(("You", user_input))

    context = {
        "revenue": 0,
        "items": 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    with st.spinner("BART is thinking..."):
        response = run_ai(user_input, context)

    st.session_state.chat.append(("AI", response))

    st.rerun()
