import streamlit as st
from ai_core import run_ai

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SESSION STATE
# =========================================================
# ALWAYS AUTHENTICATED (LOGIN DISABLED)
st.session_state.authenticated = True

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

if "show_mgmt_password" not in st.session_state:
    st.session_state.show_mgmt_password = False


# =========================================================
# DATA CHECK
# =========================================================
def data_missing():
    return (
        not st.session_state.all_data
        and not st.session_state.branches
        and not st.session_state.DAILY_ITEMS
        and not st.session_state.WEEKLY_ITEMS
    )


# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>

#MainMenu, footer, header {
    visibility: hidden;
}

/* App background */
.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    visibility: visible !important;
    display: block !important;
    width: 320px !important;
}

/* Hero */
.hero {
    background: white;
    padding: 60px;
    text-align: center;
    border-radius: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.hero h1 {
    font-size: 70px;
    color: #C0392B;
    margin: 0;
}

.hero h2 {
    color: #2C2A28;
}

/* Buttons */
div.stButton > button {
    width: 100%;
    height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg,#2C2A28,#C0392B);
    color: white;
    font-weight: 700;
    border: none;
}

div.stButton > button:hover {
    opacity: 0.9;
}

/* Sections */
.section {
    background: white;
    padding: 25px;
    margin-top: 15px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    text-align: center;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# MAIN BUTTONS
# =========================================================
col1, col3, col2 = st.columns(3, gap="large")

with col1:
    if st.button("👨‍💼 Staff Dashboard", use_container_width=True):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("📦 Management Dashboard", use_container_width=True):
        st.session_state.show_mgmt_password = True

with col3:
    st.empty()


# =========================================================
# MANAGEMENT PASSWORD
# =========================================================
if st.session_state.show_mgmt_password:

    st.markdown("### 🔐 Manager Access Required")

    password_input = st.text_input("Enter Manager Password", type="password")

    if st.button("Validate & Continue"):

        if password_input == st.secrets["MANAGER_PASSWORD"]:
            st.session_state.show_mgmt_password = False
            st.switch_page("pages/management_dashboard.py")
        else:
            st.error("❌ Incorrect password")


# =========================================================
# SIDE BAR AI
# =========================================================
with st.sidebar:

    st.markdown("## 🤖 BART AI Assistant")

    if data_missing():
        st.warning("⚠ Stock not loaded")
        st.info("Open Management Dashboard to load data")
        st.stop()

    for sender, msg in st.session_state.chat[-20:]:
        icon = "🧑" if sender == "You" else "🤖"
        st.markdown(f"**{icon} {sender}:** {msg}")

    user_input = st.text_input("Ask something...", key="ai_input")

    if st.button("Send AI") and user_input:

        context = {
            "cache_data": st.session_state.all_data,
            "branch_list": [b["BranchName"] for b in st.session_state.branches],
            "master_items": list(st.session_state.DAILY_ITEMS.keys()) +
                            list(st.session_state.WEEKLY_ITEMS.keys())
        }

        response = run_ai(user_input, context)

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

        st.rerun()


# =========================================================
# FOOTER
# =========================================================
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
