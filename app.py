import streamlit as st
from ai_core import run_ai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- GLOBAL STYLES ----------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

.block-container {
    padding: 1.2rem 2rem !important;
    max-width: 1100px;
    margin: auto;
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

div.stButton > button {
    height: 50px;
    width: 200px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    background: #2C2A28;
    color: white;
    border: none;
}

div.stButton > button:hover {
    background: #C0392B;
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

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>A modern café experience built for speed, quality, and taste. 📍 Jeddah • bart.sa</p>
</div>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
st.markdown('<div class="login-row">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- INIT CHAT ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================================================
# 🧠 IMPORTANT: AI DATA PREPARATION (THIS WAS MISSING)
# =========================================================

# These must already exist in your project
# (from your Google Sheets logic)

# all_data → list of (branch_name, raw_sheet)
# branches → master branch sheet list
# DAILY_ITEMS + WEEKLY_ITEMS → your item lists

if "all_data" not in st.session_state:
    st.error("❌ all_data not loaded")
    st.stop()

if "branches" not in st.session_state:
    st.error("❌ branches not loaded")
    st.stop()

if "DAILY_ITEMS" not in st.session_state:
    st.error("❌ DAILY_ITEMS not loaded")
    st.stop()

if "WEEKLY_ITEMS" not in st.session_state:
    st.error("❌ WEEKLY_ITEMS not loaded")
    st.stop()


# ---------------- CHAT INPUT ----------------
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "",
        placeholder="🤖 Ask: CRC Crunchy Cake yesterday Al Safa"
    )
    send = st.form_submit_button("Send")


# ---------------- AI CALL (FIXED CORE PART) ----------------
if send and user_input:

    # 🔥 THIS IS THE FIX YOU NEEDED
    context = {
        "cache_data": st.session_state.all_data,
        "master_items": st.session_state.DAILY_ITEMS + st.session_state.WEEKLY_ITEMS,
        "branch_list": [b["BranchName"] for b in st.session_state.branches]
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))


# ---------------- CHAT DISPLAY ----------------
for sender, msg in st.session_state.chat[-10:]:
    if sender == "You":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**AI:** {msg}")


# ---------------- INFO SECTION ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy café environment with fast service and premium coffee experience.</p>
</div>

<div class="section">
<h2>Visit Us</h2>
<p>Find us in Jeddah branches or visit bart.sa for more information.</p>
</div>
""", unsafe_allow_html=True)
