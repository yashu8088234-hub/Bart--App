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
# STYLES
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
    color: #C0392B;
}

/* FLOATING CHAT */
#chatBox {
    position: fixed;
    top: 100px;
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
    transition: all 0.25s ease;
}

/* HEADER */
#header {
    padding: 12px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color: white;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: move;
}

#toggleBtn {
    background: white;
    border: none;
    color: #C0392B;
    font-weight: bold;
    border-radius: 6px;
    cursor: pointer;
    padding: 3px 8px;
}

/* BODY */
#body {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
}

/* INPUT */
#inputArea {
    display: flex;
    padding: 8px;
    border-top: 1px solid #eee;
    gap: 5px;
}

#userInput {
    flex: 1;
    padding: 8px;
    border-radius: 10px;
    border: 1px solid #ddd;
}

#sendBtn {
    background: #C0392B;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 10px;
    cursor: pointer;
}

/* messages */
.msg {
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 12px;
    font-size: 14px;
}

.user {
    background: #f1f1f1;
    text-align: right;
}

.ai {
    background: #fff3f3;
    color: #C0392B;
}

/* COLLAPSE MODE */
.collapsed {
    width: 60px !important;
    height: 60px !important;
    border-radius: 50% !important;
}

.hidden {
    display: none;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <h3>Login Required</h3>
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

    # ================= HERO =================
    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <p>Coffee • French Toast • Fresh Bites</p>
    </div>
    """, unsafe_allow_html=True)

    # ================= DASHBOARD =================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("👨‍💼 Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    with col2:
        if st.button("📦 Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    # =====================================================
    # CHAT INPUT HANDLING (SAFE STREAMLIT WAY)
    # =====================================================
    user_input = st.text_input("💬 Ask BART (safe input bridge)")

    if user_input:
        response = run_ai(user_input, {})

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

    # =====================================================
    # FLOATING DRAGGABLE CHAT UI
    # =====================================================
    chat_html = """
    <div id="chatBox">

        <div id="header">
            💬 BART AI
            <button id="toggleBtn" onclick="toggleChat()">—</button>
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
            <input id="userInput" placeholder="Type message..." />
            <button id="sendBtn" onclick="alert('Use Streamlit input below')">Send</button>
        </div>

    </div>

    <script>

    let box = document.getElementById("chatBox");
    let header = document.getElementById("header");

    let isDown = false;
    let offsetX, offsetY;
    let collapsed = false;

    header.addEventListener('mousedown', function(e){
        if (collapsed) return;
        isDown = true;
        offsetX = box.offsetLeft - e.clientX;
        offsetY = box.offsetTop - e.clientY;
    });

    document.addEventListener('mouseup', function(){
        isDown = false;
    });

    document.addEventListener('mousemove', function(e){
        if (!isDown || collapsed) return;

        box.style.left = (e.clientX + offsetX) + 'px';
        box.style.top = (e.clientY + offsetY) + 'px';
        box.style.right = 'auto';
    });

    function toggleChat(){
        collapsed = !collapsed;

        if(collapsed){
            box.style.width = "60px";
            box.style.height = "60px";
            document.getElementById("body").style.display = "none";
            document.getElementById("inputArea").style.display = "none";
        } else {
            box.style.width = "360px";
            box.style.height = "520px";
            document.getElementById("body").style.display = "block";
            document.getElementById("inputArea").style.display = "flex";
        }
    }

    </script>
    """

    components.html(chat_html, height=600)
