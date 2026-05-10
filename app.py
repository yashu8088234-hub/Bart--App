import streamlit as st
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
# SESSION
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "role" not in st.session_state:
    st.session_state.role = None

if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================================================
# STYLES
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {
    visibility: hidden;
}

[data-testid="stToolbar"] {
    display:none;
}

[data-testid="stSidebar"] {
    display:none;
}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* ================= CHAT BOX ================= */
.chat-box {
    height: 60vh;
    overflow-y: auto;
    padding: 18px;
    border-radius: 18px;
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    margin-top: 20px;
}

/* ================= ROWS ================= */
.msg-row {
    display: flex;
    margin: 8px 0;
}

.msg-user {
    justify-content: flex-end;
}

.msg-ai {
    justify-content: flex-start;
}

/* ================= BUBBLES ================= */
.bubble-user {
    background: #F2F2F2;
    color: #222;
    padding: 10px 14px;
    border-radius: 18px 18px 0 18px;
    max-width: 70%;
    font-size: 14px;
    line-height: 1.4;
}

.bubble-ai {
    background: #C0392B;
    color: white;
    padding: 10px 14px;
    border-radius: 18px 18px 18px 0;
    max-width: 70%;
    font-size: 14px;
    line-height: 1.4;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN / DEMO SKIP (KEEP YOUR LOGIC HERE IF NEEDED)
# =========================================================
st.session_state.authenticated = True  # REMOVE THIS IN YOUR REAL LOGIN

# =========================================================
# CHAT INPUT
# =========================================================
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("", placeholder="🤖 Ask something about BART...")
    send = st.form_submit_button("Send")

if send and user_input:

    context = {}  # keep your real context here
    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))

# =========================================================
# CHAT TITLE
# =========================================================
st.markdown("## 💬 BART AI Chat")

# =========================================================
# CHAT UI (FIXED CHATBOT DESIGN)
# =========================================================
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

for sender, msg in st.session_state.chat[-50:]:

    if sender == "You":
        st.markdown(f"""
        <div class="msg-row msg-user">
            <div class="bubble-user">{msg}</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div class="msg-row msg-ai">
            <div class="bubble-ai">{msg}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
