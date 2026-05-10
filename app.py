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

if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# =========================================================
# GLOBAL STYLES
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

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

/* HERO */
.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 60px 30px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
}

/* CHAT */
.ai-wrapper {
    background: rgba(255,255,255,0.92);
    border-radius: 22px;
    padding: 25px;
    margin-top: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
}

.chat-container {
    max-height: 420px;
    overflow-y: auto;
    padding: 10px;
}

.user-msg {
    background:#f4f4f4;
    padding:12px;
    border-radius:12px;
    margin-bottom:10px;
    text-align:right;
}

.ai-msg {
    background:#fff3f3;
    padding:12px;
    border-radius:12px;
    margin-bottom:12px;
    border-left:4px solid #C0392B;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <div class="login-logo">
            <h1>BART</h1>
        </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        clean_username = username.strip().lower()

        if (
            clean_username == st.secrets["MANAGER_USERNAME"].lower()
            and password == st.secrets["MANAGER_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "manager"
            st.session_state.data_loaded = False
            st.rerun()

        elif (
            clean_username == st.secrets["STAFF_USERNAME"].lower()
            and password == st.secrets["STAFF_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.session_state.role = "staff"
            st.session_state.data_loaded = False
            st.rerun()

        else:
            st.error("Invalid login")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN APP
# =========================================================
else:

    # AUTO LOAD DATA ONCE
    if not st.session_state.data_loaded:

        st.session_state.all_data = []
        st.session_state.branches = [{"BranchName": "Jeddah Main"}]

        st.session_state.DAILY_ITEMS = {
            "Latte": {},
            "Espresso": {}
        }

        st.session_state.WEEKLY_ITEMS = {
            "Croissant": {}
        }

        st.session_state.data_loaded = True

    # HERO
    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <h3>Coffee • French Toast • Fresh Bites</h3>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # AI SECTION (FIXED ORDER)
    # =====================================================

    st.markdown("""
    <div class="ai-wrapper">
        <h3 style="color:#C0392B;">💬 BART AI Assistant</h3>
    """, unsafe_allow_html=True)

    # =========================
    # CHAT DISPLAY (TOP)
    # =========================
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for chat in st.session_state.chat[-20:]:

        st.markdown(f"""
        <div class="user-msg">
            <b>You:</b><br>{chat['user']}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="ai-msg">
            <b>BART:</b><br>{chat['ai']}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # INPUT (BOTTOM)
    # =========================
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder="Ask something...")
        send = st.form_submit_button("Send")

    if send and user_input:

        context = {
            "cache_data": st.session_state.all_data,
            "branch_list": [b["BranchName"] for b in st.session_state.branches],
            "master_items": list(st.session_state.DAILY_ITEMS.keys()) +
                            list(st.session_state.WEEKLY_ITEMS.keys())
        }

        with st.spinner("Thinking..."):
            response = run_ai(user_input, context)

        st.session_state.chat.append({
            "user": user_input,
            "ai": response
        })

    st.markdown("</div>", unsafe_allow_html=True)

    # =====================================================
    # BUTTONS (UNCHANGED)
    # =====================================================
    col1, col2 = st.columns(2)

    with col1:
        st.button("👨‍💼 Staff Dashboard")

    with col2:
        st.button("📦 Management Dashboard")
