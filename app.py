import streamlit as st
import streamlit.components.v1 as components
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

/* FLOATING BOT BUTTON */
.fab {
    position: fixed;
    bottom: 25px;
    right: 25px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: #2C2A28;
    color: white;
    font-size: 28px;
    border: none;
    cursor: pointer;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    z-index: 9999;
}

/* SECTION */
.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "open_chat" not in st.session_state:
    st.session_state.open_chat = False

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
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")

# ---------------- FLOATING BUTTON ----------------
if st.button("🤖"):
    st.session_state.open_chat = True

# ---------------- FLOATING CHAT WINDOW ----------------
if st.session_state.open_chat:

    chat_html = f"""
    <style>
    #bot {{
        position: fixed;
        bottom: 100px;
        right: 30px;
        width: 350px;
        height: 480px;
        background: white;
        border-radius: 18px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.25);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        font-family: Arial;
    }}

    #header {{
        background: #2C2A28;
        color: white;
        padding: 10px;
        cursor: move;
        font-weight: bold;
    }}

    #messages {{
        flex: 1;
        padding: 10px;
        overflow-y: auto;
        font-size: 13px;
    }}

    #input {{
        display: flex;
        border-top: 1px solid #eee;
    }}

    #text {{
        flex: 1;
        padding: 10px;
        border: none;
        outline: none;
    }}

    #btn {{
        width: 60px;
        background: #C0392B;
        color: white;
        border: none;
    }}

    #close {{
        float: right;
        cursor: pointer;
    }}
    </style>

    <div id="bot">
        <div id="header">
            🤖 BART AI
            <span id="close">✖</span>
        </div>

        <div id="messages">
            {"".join([f"<div><b>{s}:</b> {m}</div>" for s, m in st.session_state.chat[-15:]])}
        </div>

        <div id="input">
            <input id="text" placeholder="Ask something..." />
            <button id="btn">➤</button>
        </div>
    </div>

    <script>
    const bot = document.getElementById("bot");
    const header = document.getElementById("header");
    const close = document.getElementById("close");

    let dragging = false;
    let offsetX, offsetY;

    header.onmousedown = (e) => {{
        dragging = true;
        offsetX = e.clientX - bot.offsetLeft;
        offsetY = e.clientY - bot.offsetTop;
    }};

    document.onmouseup = () => dragging = false;

    document.onmousemove = (e) => {{
        if (dragging) {{
            bot.style.left = (e.clientX - offsetX) + "px";
            bot.style.top = (e.clientY - offsetY) + "px";
            bot.style.right = "auto";
            bot.style.bottom = "auto";
        }}
    }};

    close.onclick = () => {{
        bot.style.display = "none";
    }};
    </script>
    """

    components.html(chat_html, height=520)

# ---------------- AI INPUT ----------------
user_input = st.text_input("hidden_input", label_visibility="collapsed")
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
