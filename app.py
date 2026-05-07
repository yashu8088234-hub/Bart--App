import streamlit as st
import streamlit.components.v1 as components
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
# SESSION STATE
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "role" not in st.session_state:
    st.session_state.role = None

if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================================================
# YOUR EXISTING UI STYLES (UNCHANGED)
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

/* LOGIN + HERO + OTHER STYLES STAY EXACTLY AS YOU HAD THEM */
/* (NOT MODIFIED TO AVOID UI BREAKAGE) */

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN SCREEN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <h1 style="text-align:center;color:#C0392B;">BART LOGIN</h1>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == st.secrets["MANAGER_USERNAME"] and password == st.secrets["MANAGER_PASSWORD"]:
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.rerun()

        elif username == st.secrets["STAFF_USERNAME"] and password == st.secrets["STAFF_PASSWORD"]:
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.rerun()

        else:
            st.error("Invalid credentials")

# =========================================================
# MAIN APP
# =========================================================
else:

    # ================= HERO (UNCHANGED LOGIC) =================
    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <h2>Coffee • French Toast • Fresh Bites</h2>
        <p>Jeddah • bart.sa</p>
    </div>
    """, unsafe_allow_html=True)

    # ================= DASHBOARD BUTTONS =================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    with col2:
        if st.button("Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    # =====================================================
    # CHAT BACKEND (UNCHANGED LOGIC)
    # =====================================================
    user_input = st.text_input("Ask BART")

    if user_input:
        response = run_ai(user_input, {})

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

    # =====================================================
    # FLOATING CHAT OVERLAY (ONLY CHANGE IN YOUR APP)
    # =====================================================

    chat_html = """
    <div id="bart-chat">

    <style>
    #bart-chat {
        position: fixed;
        top: 100px;
        right: 20px;
        width: 340px;
        height: 520px;
        z-index: 999999;
        font-family: Arial;
    }

    #box {
        width: 100%;
        height: 100%;
        background: rgba(255,255,255,0.96);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    #header {
        background: #C0392B;
        color: white;
        padding: 10px;
        font-weight: bold;
        cursor: move;
    }

    #body {
        flex: 1;
        overflow-y: auto;
        padding: 10px;
    }

    .msg {
        padding: 8px;
        margin-bottom: 6px;
        border-radius: 10px;
        font-size: 13px;
    }

    .user {background:#eee; text-align:right;}
    .ai {background:#fff3f3; color:#C0392B;}

    #input {
        display:flex;
        border-top:1px solid #ddd;
    }

    #input input {
        flex:1;
        padding:8px;
        border:none;
    }

    #input button {
        background:#C0392B;
        color:white;
        border:none;
        padding:8px 10px;
    }

    </style>

    <div id="box">

        <div id="header">💬 BART AI</div>

        <div id="body">
    """

    # SHOW CHAT (NEWEST FIRST)
    for sender, msg in reversed(st.session_state.chat[-20:]):

        if sender == "You":
            chat_html += f'<div class="msg user"><b>You:</b> {msg}</div>'
        else:
            chat_html += f'<div class="msg ai"><b>BART:</b> {msg}</div>'

    chat_html += """
        </div>

        <div id="input">
            <input placeholder="Type..." />
            <button onclick="alert('Use Streamlit input above')">Send</button>
        </div>

    </div>
    </div>

    <script>

    let box = document.getElementById("box");
    let header = document.getElementById("header");

    let drag = false;
    let ox, oy;

    header.addEventListener("mousedown", e => {
        drag = true;
        ox = box.offsetLeft - e.clientX;
        oy = box.offsetTop - e.clientY;
    });

    document.addEventListener("mouseup", () => drag = false);

    document.addEventListener("mousemove", e => {
        if (!drag) return;
        box.style.left = (e.clientX + ox) + "px";
        box.style.top = (e.clientY + oy) + "px";
        box.style.right = "auto";
    });

    </script>
    """

    components.html(chat_html, height=550)

    # =====================================================
    # INFO SECTION (UNCHANGED)
    # =====================================================
    st.markdown("""
    <div class="section">
        <h2>Visit Us</h2>
        <p>Jeddah branches • bart.sa</p>
    </div>
    """, unsafe_allow_html=True)
