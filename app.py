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

.hero {
    text-align: center;
    padding: 30px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h3>Stock AI System</h3>
</div>
""", unsafe_allow_html=True)

# ---------------- LOGIN BUTTONS ----------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")

# =========================================================
# ⚠️ ONLY FIX ADDED HERE (DO NOT TOUCH ANYTHING ELSE)
# =========================================================

if "branches" not in st.session_state:
    st.session_state.branches = branches

if "DAILY_ITEMS" not in st.session_state:
    st.session_state.DAILY_ITEMS = DAILY_ITEMS

if "WEEKLY_ITEMS" not in st.session_state:
    st.session_state.WEEKLY_ITEMS = WEEKLY_ITEMS

# 🔥 FIX: LOAD all_data (THIS WAS MISSING)
if "all_data" not in st.session_state:

    sheet_cache = {}

    for b in branches:

        sheet_id = b.get("SheetID")

        try:
            file = client.open_by_key(sheet_id)
            sheet = file.worksheet("Stocks").get_all_values()
            sheet_cache[b["BranchName"]] = sheet

        except Exception:
            sheet_cache[b["BranchName"]] = None

    st.session_state.all_data = list(sheet_cache.items())

# ---------------- CHAT INIT ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- CHAT INPUT ----------------
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("", placeholder="Ask: CRC Crunchy Cake yesterday Al Safa")
    send = st.form_submit_button("Send")

# ---------------- AI CALL ----------------
if send and user_input:

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
