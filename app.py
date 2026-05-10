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
# GLOBAL STYLES (YOUR ORIGINAL ONLY — SAFE)
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {
    visibility: hidden;
}

[data-testid="stToolbar"] {
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

# =========================================================
# SESSION STATE
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "role" not in st.session_state:
    st.session_state.role = None

if "chat" not in st.session_state:
    st.session_state.chat = []

if "all_data" not in st.session_state:
    st.session_state.all_data = []

if "branches" not in st.session_state:
    st.session_state.branches = []

if "DAILY_ITEMS" not in st.session_state:
    st.session_state.DAILY_ITEMS = {}

if "WEEKLY_ITEMS" not in st.session_state:
    st.session_state.WEEKLY_ITEMS = {}

# =========================================================
# LOGIN PAGE
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <div class="login-logo">
            <h1>BART</h1>
            <p>Coffee • French Toast • Fresh Bites</p>
        </div>
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
            st.error("Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN DASHBOARD
# =========================================================
else:

    # Logout
    top1, top2 = st.columns([9,1])

    with top2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.chat = []
            st.rerun()

    # HERO
    st.markdown("""
    <div class="hero">
        <h1>BART</h1>
        <h2>Coffee • French Toast • Fresh Bites</h2>
        <p>📍 Jeddah • bart.sa</p>
    </div>
    """, unsafe_allow_html=True)

    # NAV BUTTONS
    col1, col2 = st.columns(2)

    with col1:
        if st.button("👨‍💼 Staff Dashboard"):
            st.switch_page("pages/staff_dashboard.py")

    with col2:
        if st.button("📦 Management Dashboard"):
            st.switch_page("pages/management_dashboard.py")

    # =====================================================
    # 🤖 AI CHAT (CLEAN + ON PAGE)
    # =====================================================
    st.markdown("## 🤖 BART AI Assistant")

    # Chat display
    for sender, msg in st.session_state.chat[-20:]:
        if sender == "You":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 AI:** {msg}")

    st.divider()

    # Input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask something...")
        send = st.form_submit_button("Send")

    if send and user_input:

        context = {
            "cache_data": st.session_state.all_data,
            "branch_list": [b["BranchName"] for b in st.session_state.branches],
            "master_items": (
                list(st.session_state.DAILY_ITEMS.keys()) +
                list(st.session_state.WEEKLY_ITEMS.keys())
            )
        }

        response = run_ai(user_input, context)

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

        st.rerun()

    # =====================================================
    # FOOTER
    # =====================================================
    st.markdown("""
    <div class="section">
        <h2>Our Experience</h2>
        <p>Relax in a cozy café environment with fast service and premium coffee experience.</p>
    </div>

    <div class="section">
        <h2>Visit Us</h2>
        <p>Find us in Jeddah branches or visit bart.sa</p>
    </div>
    """, unsafe_allow_html=True)
