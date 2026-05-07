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
# SESSION
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "role" not in st.session_state:
    st.session_state.role = None

if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================================================
# STYLES (YOUR ORIGINAL + CHAT FIX)
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* ================= LOGIN + UI (UNCHANGED) ================= */

.login-container {
    max-width: 460px;
    margin: 80px auto;
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(12px);
    border-radius: 28px;
    padding: 45px 35px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
}

/* HERO */
.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 60px 30px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
}

/* ================= FLOATING CHAT ================= */

#chatBox {
    position: fixed;
    top: 90px;
    right: 20px;
    width: 360px;
    height: 520px;
    background: rgba(255,255,255,0.97);
    backdrop-filter: blur(10px);
    border-radius: 18px;
    box-shadow: 0 12px 45px rgba(0,0,0,0.18);
    z-index: 999999;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* header */
#header {
    padding: 12px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color: white;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
}

/* body */
#body {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
}

/* messages */
.msg {
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 12px;
}

.user {background:#f1f1f1;text-align:right;}
.ai {background:#fff3f3;color:#C0392B;}

/* input */
#inputArea {
    display:flex;
    padding:8px;
    border-top:1px solid #eee;
}

#userInput {
    flex:1;
    padding:8px;
}

#sendBtn {
    background:#C0392B;
    color:white;
    border:none;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="hero">
        <h1>BART LOGIN</h1>
    </div>
    """, unsafe_allow_html=True)

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):

        if u == st.secrets["MANAGER_USERNAME"] and p == st.secrets["MANAGER_PASSWORD"]:
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.rerun()

        elif u == st.secrets["STAFF_USERNAME"] and p == st.secrets["STAFF_PASSWORD"]:
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.rerun()

        else:
            st.error("Wrong credentials")

# =========================================================
# MAIN APP (YOUR ORIGINAL STRUCTURE PRESERVED)
# =========================================================
else:

    # HERO (UNCHANGED)
    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <h2>Coffee • French Toast • Fresh Bites</h2>
        <p>Jeddah • bart.sa</p>
    </div>
    """, unsafe_allow_html=True)

    # DASHBOARD BUTTONS (UNCHANGED)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    with col2:
        if st.button("Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    # =====================================================
    # CHAT INPUT BRIDGE (SAFE STREAMLIT SIDE)
    # =====================================================
    user_input = st.text_input("Hidden Chat Input (backend bridge)")

    if user_input:
        response = run_ai(user_input, {})

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

    # =====================================================
    # FLOATING DRAGGABLE CHAT (FIXED + COLLAPSIBLE)
    # =====================================================

    chat_html = """
    <div id="chatBox">

        <div id="header">
            💬 BART AI
        </div>

        <div id="body">
    """

    for sender, msg in reversed(st.session_state.chat[-20:]):

        if sender == "You":
            chat_html += f'<div class="msg user"><b>You:</b> {msg}</div>'
        else:
            chat_html += f'<div class="msg ai"><b>BART:</b> {msg}</div>'

    chat_html += """
        </div>

        <div id="inputArea">
            <input id="userInput" placeholder="Type..." />
            <button id="sendBtn" onclick="alert('Use Streamlit input below')">Send</button>
        </div>

    </div>

    <script>

    let box = document.getElementById("chatBox");
    let header = document.getElementById("header");

    let drag = false;
    let ox, oy;

    header.addEventListener("mousedown", e=>{
        drag = true;
        ox = box.offsetLeft - e.clientX;
        oy = box.offsetTop - e.clientY;
    });

    document.addEventListener("mouseup", ()=>drag=false);

    document.addEventListener("mousemove", e=>{
        if(!drag) return;
        box.style.left = (e.clientX + ox) + "px";
        box.style.top = (e.clientY + oy) + "px";
        box.style.right = "auto";
    });

    </script>
    """

    components.html(chat_html, height=600)

    # INFO SECTION (UNCHANGED)
    st.markdown("""
    <div class="section">
        <h2>Visit Us</h2>
        <p>Jeddah branches & bart.sa</p>
    </div>
    """, unsafe_allow_html=True)
