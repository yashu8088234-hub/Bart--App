import streamlit as st
import streamlit.components.v1 as components
from ai_core import run_ai

# ---------------- SESSION ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "open_chat" not in st.session_state:
    st.session_state.open_chat = False

# ---------------- ROBOT BUTTON ----------------
if st.button("🤖"):
    st.session_state.open_chat = True

# ---------------- FLOATING CHAT UI ----------------
if st.session_state.open_chat:

    chat_html = f"""
    <style>
    #bot {{
        position: fixed;
        bottom: 90px;
        right: 30px;
        width: 340px;
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
            {"".join([f"<div><b>{s}:</b> {m}</div>" for s, m in st.session_state.chat[-12:]])}
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

# ---------------- AI INPUT (STREAMLIT SIDE) ----------------
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
