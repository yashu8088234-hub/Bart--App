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

/* LOGIN PAGE */

.login-container {
    max-width: 460px;
    margin: 80px auto;
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(12px);
    border-radius: 28px;
    padding: 45px 35px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.4);
}

.login-logo {
    text-align:center;
}

.login-logo h1 {
    font-size:70px;
    font-weight:900;
    letter-spacing:8px;
    color:#C0392B;
    margin-bottom:5px;
}

.login-logo p {
    color:#666;
    margin-top:0;
    font-size:15px;
}

.login-title {
    text-align:center;
    margin-top:25px;
    margin-bottom:30px;
}

.login-title h2 {
    color:#2C2A28;
    margin-bottom:6px;
}

.login-title span {
    color:#777;
    font-size:14px;
}

div[data-baseweb="input"] input {
    border-radius:14px;
    height:52px;
    border:1px solid #E4E4E4;
    background:white;
    font-size:15px;
}

div.stButton > button {
    width:100%;
    height:52px;
    border:none;
    border-radius:14px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color:white;
    font-size:16px;
    font-weight:700;
}

div.stButton > button:hover {
    opacity:0.92;
}

/* MAIN PAGE */

.block-container {
    padding: 1.2rem 2rem !important;
    max-width: 1100px;
    margin: auto;
}

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

.login-row {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 20px 0 35px;
}

.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}

.section h2 {
    color: #C0392B;
    text-align: center;
}

.section p {
    color: #555;
    text-align: center;
}

/* SIDEBAR CHAT STYLE */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff, #f7f1ea);
    padding: 20px;
}

.chat-box {
    max-height: 65vh;
    overflow-y: auto;
    padding-right: 5px;
}

.user-msg {
    background: #f1f1f1;
    padding: 8px;
    border-radius: 10px;
    margin-bottom: 6px;
    text-align: right;
}

.ai-msg {
    background: #fff3f3;
    color: #C0392B;
    padding: 8px;
    border-radius: 10px;
    margin-bottom: 6px;
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
        <p>Coffee • French Toast • Fresh Bites</p>
    </div>

    <div class="login-title">
        <h2>Control Center</h2>
        <span>Secure Internal Access</span>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="Enter username")
    password = st.text_input("Password", type="password", placeholder="Enter password")

    login = st.button("Login")

    if login:

        clean_username = username.strip().lower()

        if (
            clean_username == st.secrets["MANAGER_USERNAME"].lower()
            and password == st.secrets["MANAGER_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.rerun()

        elif (
            clean_username == st.secrets["STAFF_USERNAME"].lower()
            and password == st.secrets["STAFF_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.rerun()

        else:
            st.error("Invalid username or password")

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
        <p>
        A modern café experience built for speed,
        quality, and taste.
        📍 Jeddah • bart.sa
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-row">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col2:
        if st.button("📦 Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    with col1:
        if st.button("👨‍💼 Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # SESSION STORAGE
    # =====================================================
    if "all_data" not in st.session_state:
        st.session_state.all_data = []

    if "branches" not in st.session_state:
        st.session_state.branches = []

    if "DAILY_ITEMS" not in st.session_state:
        st.session_state.DAILY_ITEMS = {}

    if "WEEKLY_ITEMS" not in st.session_state:
        st.session_state.WEEKLY_ITEMS = {}

    # =====================================================
    # MODERN AI SIDEBAR CHAT (NEW)
    # =====================================================
    with st.sidebar:
        st.markdown("## 🤖 BART AI")

        st.markdown('<div class="chat-box">', unsafe_allow_html=True)

        for sender, msg in st.session_state.chat[-20:]:
            if sender == "You":
                st.markdown(f'<div class="user-msg"><b>You:</b> {msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-msg"><b>BART:</b> {msg}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        with st.form("ai_chat_form", clear_on_submit=True):
            user_input = st.text_input("Ask something...")
            send = st.form_submit_button("Send")

        if send and user_input:

            all_items = (
                list(st.session_state.DAILY_ITEMS.keys()) +
                list(st.session_state.WEEKLY_ITEMS.keys())
            )

            context = {
                "cache_data": st.session_state.all_data,
                "branch_list": [
                    b["BranchName"]
                    for b in st.session_state.branches
                ],
                "master_items": all_items
            }

            response = run_ai(user_input, context)

            st.session_state.chat.append(("You", user_input))
            st.session_state.chat.append(("AI", response))

            st.rerun()

    # =====================================================
    # FOOTER SECTIONS
    # =====================================================
    st.markdown("""
    <div class="section">
    <h2>Our Experience</h2>
    <p>
    Relax in a cozy café environment with
    fast service and premium coffee experience.
    </p>
    </div>

    <div class="section">
    <h2>Visit Us</h2>
    <p>
    Find us in Jeddah branches or visit bart.sa
    for more information.
    </p>
    </div>
    """, unsafe_allow_html=True)
