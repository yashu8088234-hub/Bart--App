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

/* CHAT WRAPPER (YOUR ORIGINAL STYLE IMPROVED) */
.chat-wrapper {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    max-width: 700px;
    display: flex;
    gap: 10px;
    z-index: 100;
}

.chat-wrapper input {
    flex: 1;
    height: 50px;
    border-radius: 12px;
    border: none;
    padding: 0 15px;
    font-size: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}

.chat-wrapper button {
    height: 50px;
    width: 50px;
    border-radius: 12px;
    border: none;
    background: #2C2A28;
    color: white;
    cursor: pointer;
}

.chat-wrapper button:hover {
    background: #C0392B;
}

/* CHAT DISPLAY */
.chat-box {
    max-height: 55vh;
    overflow-y: auto;
    padding-bottom: 80px;
}

.user-msg {
    text-align: right;
    background: #2C2A28;
    color: white;
    padding: 10px 14px;
    border-radius: 12px;
    margin: 6px 0;
    display: inline-block;
    float: right;
    clear: both;
    max-width: 70%;
}

.ai-msg {
    text-align: left;
    background: #F7F1EA;
    color: #222;
    padding: 10px 14px;
    border-radius: 12px;
    margin: 6px 0;
    display: inline-block;
    float: left;
    clear: both;
    max-width: 70%;
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
col1, col2 = st.columns(2)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard")

# ---------------- SESSION ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- CHAT DISPLAY ----------------
st.markdown("<div class='chat-box'>", unsafe_allow_html=True)

for sender, msg in st.session_state.chat[-10:]:
    if sender == "You":
        st.markdown(f"<div class='user-msg'>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-msg'>{msg}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- CHAT INPUT (NO JS HACK) ----------------
st.markdown("""
<form action="" method="post">
</form>
""", unsafe_allow_html=True)

# normal hidden-safe input (Streamlit controlled)
user_input = st.text_input("", placeholder="Message...", label_visibility="collapsed")

send = st.button("➤")

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
