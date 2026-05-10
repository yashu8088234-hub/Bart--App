import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from ai_core import run_ai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (AI Full Memory Mode)")

# ---------------- GOOGLE AUTH ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = get_client()

# ---------------- MASTER SHEET ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ---------------- SHEET CACHE ----------------
@st.cache_resource
def get_sheets(branches):
    cache = {}
    for b in branches:
        sheet_id = b.get("SheetID")
        if not sheet_id:
            continue
        try:
            cache[sheet_id] = client.open_by_key(sheet_id)
        except:
            pass
    return cache

sheet_cache = get_sheets(branches)

# ---------------- FETCH ----------------
def fetch_branch(branch):
    try:
        sheet_id = branch.get("SheetID")
        if not sheet_id or sheet_id not in sheet_cache:
            return branch["BranchName"], None

        file = sheet_cache[sheet_id]
        ws = file.worksheet("Stocks")
        return branch["BranchName"], ws.get_all_values()

    except:
        return branch["BranchName"], None

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=300)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=3) as executor:
        return list(executor.map(fetch_branch, branches))

all_data = load_all_data(branches)

st.session_state.all_data = all_data
st.session_state.branches = branches

# ---------------- PROCESS STOCK ----------------
daily_items = {}
weekly_items = {}

# (You already process this elsewhere — keeping simple here)

combined = {}
st.session_state.DAILY_ITEMS = daily_items
st.session_state.WEEKLY_ITEMS = weekly_items

# =========================================================
# 🧠 MEMORY SYSTEM (IMPORTANT FIX)
# =========================================================
if "memory" not in st.session_state:
    st.session_state.memory = {
        "last_item": None,
        "last_branch": None,
        "last_date": None
    }

# =========================================================
# 🤖 AI PANEL STATE
# =========================================================
if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if st.button("🤖 AI Assistant"):
    st.session_state.ai_open = not st.session_state.ai_open

# =========================================================
# 💬 AI CHAT UI
# =========================================================
if st.session_state.ai_open:

    st.markdown("## 🤖 Stock AI Assistant (Memory Enabled)")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    # Show chat
    for role, msg in st.session_state.chat:
        if role == "You":
            st.markdown(f"🧑 **You:** {msg}")
        else:
            st.markdown(f"🤖 **AI:** {msg}")

    # Input
    with st.form("ai_form", clear_on_submit=True):
        user_input = st.text_input("Ask anything about stock...")
        submitted = st.form_submit_button("Send")

    # Clear chat
    if st.button("🧹 Clear Chat"):
        st.session_state.chat = []
        st.session_state.memory = {
            "last_item": None,
            "last_branch": None,
            "last_date": None
        }
        st.rerun()

    # =========================================================
    # 🚀 AI EXECUTION (FULL CONTROL + MEMORY)
    # =========================================================
    if submitted and user_input.strip():

        context = {
            "cache_data": st.session_state.all_data,
            "branch_list": branch_names,
            "master_items": list(combined.keys()),
            "memory": st.session_state.memory
        }

        with st.spinner("AI analyzing inventory with memory... 🤖"):
            response = run_ai(user_input, context)

        # Save chat
        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

        st.rerun()

# ---------------- TABLES ----------------
st.subheader("📦 System Data Loaded")
st.write("AI now controls all stock reasoning. No pre-filtering is applied.")
