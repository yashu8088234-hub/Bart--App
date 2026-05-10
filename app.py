import streamlit as st
from ai_core import run_ai

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# SESSION STATE (UNCHANGED LOGIC)
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

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

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

# =========================================================
# THEME (STANDARD COLORS + YOUR BRAND RED)
# =========================================================
PRIMARY = "#C0392B"   # your brand red
DARK = "#2C2A28"
BG = "#F6F7FB"
CARD = "#FFFFFF"
TEXT = "#1F1F1F"

# =========================================================
# STYLE (SAAS NAVBAR UI)
# =========================================================
st.markdown(f"""
<style>

#MainMenu, footer, header {{
    visibility: hidden;
}}

.stApp {{
    background: {BG};
    font-family: 'Segoe UI', sans-serif;
}}

/* TOP NAV BAR */
.navbar {{
    position: sticky;
    top: 0;
    background: white;
    padding: 14px 25px;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}}

.brand {{
    font-size: 22px;
    font-weight: 800;
    color: {PRIMARY};
    letter-spacing: 2px;
}}

.nav-buttons button {{
    margin-left: 10px;
    background: {DARK};
    color: white;
    border-radius: 10px;
    height: 40px;
    padding: 0 14px;
    border: none;
    font-weight: 600;
}}

.nav-buttons button:hover {{
    background: {PRIMARY};
}}

/* HERO */
.hero {{
    background: {CARD};
    padding: 50px;
    text-align: center;
    border-radius: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    margin-bottom: 20px;
}}

.hero h1 {{
    font-size: 60px;
    color: {PRIMARY};
    margin: 0;
}}

/* SECTION */
.section {{
    background: {CARD};
    padding: 25px;
    margin-top: 15px;
    border-radius: 14px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.06);
    text-align: center;
}}

/* MAIN BUTTON STYLE (CONSISTENT) */
div.stButton > button {{
    width: 100%;
    height: 48px;
    border-radius: 12px;
    background: {DARK};
    color: white;
    font-weight: 700;
    border: none;
}}

div.stButton > button:hover {{
    background: {PRIMARY};
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.title("BART Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state.authenticated = True
        st.rerun()

    st.stop()

# =========================================================
# TOP NAV BAR (OPTION 1 IMPLEMENTATION)
# =========================================================
st.markdown(f"""
<div class="navbar">
    <div class="brand">BART</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2,2,2])

with col1:
    if st.button("👨‍💼 Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("📦 Management Dashboard"):
        st.switch_page("pages/management_dashboard.py")

with col3:
    if st.button("🤖 AI Assistant"):
        st.session_state.ai_open = not st.session_state.ai_open

# =========================================================
# HERO
# =========================================================
st.markdown(f"""
<div class="hero">
    <h1>BART</h1>
    <p style="color:{TEXT}">Coffee • French Toast • Fresh Bites</p>
    <p style="color:{TEXT}">📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# AI CHAT (UNCHANGED LOGIC)
# =========================================================
if st.session_state.ai_open:

    st.markdown("## 🤖 BART AI Assistant")

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
st.markdown(f"""
<div class="section">
    <h3>Our Experience</h3>
    <p>Premium café experience in Jeddah</p>
</div>

<div class="section">
    <h3>Visit Us</h3>
    <p>bart.sa • Jeddah Branches</p>
</div>
""", unsafe_allow_html=True)
