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
    border: 1px solid rgba(255,255,255,0.4);
}

.login-logo h1 {
    font-size:70px;
    font-weight:900;
    letter-spacing:8px;
    color:#C0392B;
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

/* MAIN */
.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 60px 30px;
    border-radius: 28px;
    text-align: center;
}

.hero h1 {
    font-size: 70px;
    font-weight: 900;
    color: #C0392B;
}

.section {
    background: rgba(255,255,255,0.9);
    padding: 30px 20px;
    margin-top: 20px;
    border-radius: 16px;
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
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    login = st.button("Login")

    if login:

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
            st.error("Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN DASHBOARD
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

    st.markdown("## 💬 BART AI Chat")

    # CHAT INPUT
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder="🤖 Ask something...")
        send = st.form_submit_button("Send")

    if send and user_input:

        all_items = (
            list(st.session_state.DAILY_ITEMS.keys()) +
            list(st.session_state.WEEKLY_ITEMS.keys())
        )

        context = {
            "cache_data": st.session_state.all_data,
            "branch_list": [b["BranchName"] for b in st.session_state.branches],
            "master_items": all_items
        }

        response = run_ai(user_input, context)

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

    # =====================================================
    # FIXED CHAT DISPLAY (REVERSED)
    # =====================================================
    for sender, msg in reversed(st.session_state.chat[-20:]):

        if sender == "You":
            st.markdown(
                f"""
                <div style="
                    background:#f1f1f1;
                    padding:10px;
                    border-radius:12px;
                    margin-bottom:8px;
                    text-align:right;
                ">
                    <b>You:</b> {msg}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="
                    background:#fff3f3;
                    color:#C0392B;
                    padding:10px;
                    border-radius:12px;
                    margin-bottom:8px;
                ">
                    <b>BART:</b> {msg}
                </div>
                """,
                unsafe_allow_html=True
            )

    # =====================================================
    # INFO SECTION
    # =====================================================
    st.markdown("""
    <div class="section">
    <h2>Our Experience</h2>
    <p>Relax in a cozy café environment with fast service.</p>
    </div>

    <div class="section">
    <h2>Visit Us</h2>
    <p>Find us in Jeddah branches or visit bart.sa</p>
    </div>
    """, unsafe_allow_html=True)
