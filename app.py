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
# GLOBAL STYLES
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

.login-logo h1 {
    font-size:70px;
    font-weight:900;
    letter-spacing:8px;
    color:#C0392B;
    text-align:center;
}

.login-title {
    text-align:center;
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

/* SECTIONS */

.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}

/* CHAT BUBBLES */

.chat-box {
    max-width: 900px;
    margin: auto;
}

.chat-user {
    background: #f1f1f1;
    padding: 10px;
    border-radius: 12px;
    margin-bottom: 8px;
    text-align: right;
}

.chat-ai {
    background: #fff3f3;
    color: #C0392B;
    padding: 10px;
    border-radius: 12px;
    margin-bottom: 8px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN SCREEN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <div class="login-logo">
            <h1>BART</h1>
        </div>
        <div class="login-title">
            <h2>Control Center</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if (
            username == st.secrets["MANAGER_USERNAME"]
            and password == st.secrets["MANAGER_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.rerun()

        elif (
            username == st.secrets["STAFF_USERNAME"]
            and password == st.secrets["STAFF_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.rerun()

        else:
            st.error("Invalid credentials")

# =========================================================
# MAIN APP
# =========================================================
else:

    col1, col2 = st.columns([9,1])

    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.chat = []
            st.rerun()

    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <h2>Coffee • French Toast • Fresh Bites</h2>
        <p>Jeddah • bart.sa</p>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # NAV BUTTONS
    # =====================================================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("👨‍💼 Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    with col2:
        if st.button("📦 Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    # =====================================================
    # CHAT INPUT
    # =====================================================
    st.markdown("## 💬 BART AI Chat")

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder="Ask something...")
        send = st.form_submit_button("Send")

    if send and user_input:

        context = {
            "cache_data": st.session_state.get("all_data", []),
            "branch_list": [b["BranchName"] for b in st.session_state.get("branches", [])],
            "master_items": list(st.session_state.get("DAILY_ITEMS", {}).keys()) +
                           list(st.session_state.get("WEEKLY_ITEMS", {}).keys())
        }

        response = run_ai(user_input, context)

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

    # =====================================================
    # CHAT DISPLAY (INLINE)
    # =====================================================
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)

    for sender, msg in st.session_state.chat[-20:]:

        if sender == "You":
            st.markdown(f"<div class='chat-user'><b>You:</b> {msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-ai'><b>BART:</b> {msg}</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # INFO SECTIONS
    # =====================================================
    st.markdown("""
    <div class="section">
        <h2>Our Experience</h2>
        <p>Relax in a premium café experience with fast service and quality food.</p>
    </div>

    <div class="section">
        <h2>Visit Us</h2>
        <p>Jeddah branches + bart.sa</p>
    </div>
    """, unsafe_allow_html=True)
