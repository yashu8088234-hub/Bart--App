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
# GLOBAL UI HIDING
# =========================================================
st.markdown("""
<style>

#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

[data-testid="stToolbar"] {display: none;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stDeployButton"] {display: none;}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* LOGIN */
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
}

/* SECTION */
.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}

/* ===============================
   DRAGGABLE AI CHAT BOX
================================= */

#ai-chat-box {
    position: fixed;
    right: 30px;
    bottom: 30px;
    width: 340px;
    height: 420px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

#ai-header {
    background: linear-gradient(135deg, #C0392B, #2C2A28);
    color: white;
    padding: 10px;
    cursor: move;
    font-weight: bold;
    text-align: center;
}

#ai-body {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    font-size: 14px;
}

.ai-msg {
    background: #fff3f3;
    color: #C0392B;
    padding: 6px;
    border-radius: 10px;
    margin-bottom: 5px;
}

.user-msg {
    background: #f1f1f1;
    padding: 6px;
    border-radius: 10px;
    margin-bottom: 5px;
    text-align: right;
}

#ai-input {
    display: flex;
    padding: 8px;
    border-top: 1px solid #eee;
}

</style>

<script>
// Simple drag system (safe for Streamlit)
let box = null;
let isDown = false;
let offset = [0,0];

window.onload = function() {
    box = document.getElementById("ai-chat-box");

    if (!box) return;

    let header = document.getElementById("ai-header");

    header.addEventListener("mousedown", function(e) {
        isDown = true;
        offset = [
            box.offsetLeft - e.clientX,
            box.offsetTop - e.clientY
        ];
    });

    document.addEventListener("mouseup", function() {
        isDown = false;
    });

    document.addEventListener("mousemove", function(e) {
        if (isDown) {
            box.style.left = (e.clientX + offset[0]) + "px";
            box.style.top = (e.clientY + offset[1]) + "px";
            box.style.right = "auto";
            box.style.bottom = "auto";
        }
    });
};
</script>
""", unsafe_allow_html=True)

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
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <h1 style="text-align:center;color:#C0392B;">BART</h1>
        <p style="text-align:center;">Coffee • French Toast • Fresh Bites</p>
        <h3 style="text-align:center;">Control Center</h3>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if (
            username.lower() == st.secrets["MANAGER_USERNAME"].lower()
            and password == st.secrets["MANAGER_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.rerun()

        elif (
            username.lower() == st.secrets["STAFF_USERNAME"].lower()
            and password == st.secrets["STAFF_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.rerun()

        else:
            st.error("Invalid credentials")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN DASHBOARD
# =========================================================
else:

    top1, top2 = st.columns([9,1])

    with top2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.chat = []
            st.rerun()

    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <h2>Coffee • French Toast • Fresh Bites</h2>
        <p>📍 Jeddah • bart.sa</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👨‍💼 Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    with col2:
        if st.button("📦 Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    # =====================================================
    # DRAGGABLE AI CHAT (MAIN PAGE FLOATING)
    # =====================================================
    st.markdown("""
    <div id="ai-chat-box">

        <div id="ai-header">
            🤖 BART AI Assistant (Drag me)
        </div>

        <div id="ai-body">
    """, unsafe_allow_html=True)

    for sender, msg in st.session_state.chat[-20:]:
        if sender == "You":
            st.markdown(f'<div class="user-msg"><b>You:</b> {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-msg"><b>AI:</b> {msg}</div>', unsafe_allow_html=True)

    st.markdown("""
        </div>
    """, unsafe_allow_html=True)

    with st.form("ai_form", clear_on_submit=True):
        user_input = st.text_input("Ask AI...")
        send = st.form_submit_button("Send")

    if send and user_input:

        context = {
            "cache_data": st.session_state.get("all_data", []),
            "branch_list": [],
            "master_items": []
        }

        response = run_ai(user_input, context)

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # =====================================================
    # FOOTER
    # =====================================================
    st.markdown("""
    <div class="section">
        <h2>Our Experience</h2>
        <p>Premium café experience with fast service.</p>
    </div>

    <div class="section">
        <h2>Visit Us</h2>
        <p>Jeddah • bart.sa</p>
    </div>
    """, unsafe_allow_html=True)
