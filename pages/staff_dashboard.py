import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from pathlib import Path
import pandas as pd
import time
import uuid

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="BART Staff Dashboard")

SESSION_TIMEOUT = 2 * 60

# ---------------- CLEAN UI STYLE (UNCHANGED) ----------------
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

.block-container {
    padding: 1rem 2rem;
    max-width: 1200px;
    margin: auto;
}

.stApp {
    background: linear-gradient(135deg,#eef2f7,#d6e4ff);
}

h1, h2, h3 {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER (UNCHANGED) ----------------
st.markdown("""
<div style="
    background: linear-gradient(90deg, #1f1f2e, #4b6cb7);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 20px;
">
<h1 style='color:white; margin:0;'>BART Staff Dashboard</h1>
<p style='color:#e0e0e0; margin:0;'>Select Branch & Access Operations</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🔥 SAFE SESSION SYSTEM (FIX ONLY - NO UI CHANGE)
# =========================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "active_branch" not in st.session_state:
    st.session_state.active_branch = None

if "selected_branch" not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

if "last_activity" not in st.session_state:
    st.session_state.last_activity = None

# ---------------- SESSION VALIDATION ----------------
def is_session_valid():
    if not st.session_state.authenticated:
        return False

    if not st.session_state.active_branch:
        return False

    if st.session_state.last_activity:
        if time.time() - st.session_state.last_activity > SESSION_TIMEOUT:
            return False

    return True

# auto logout if invalid
if not is_session_valid():
    st.session_state.authenticated = False

# ---------------- PASSWORD FILE ----------------
FILE_NAME = Path(__file__).parent / "passwords.json"

def init_file():
    if not FILE_NAME.exists():
        with open(FILE_NAME, "w") as f:
            json.dump({"admin": "admin123"}, f)

def load_admin():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

init_file()

# ---------------- GOOGLE SHEETS ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ---------------- LOAD BRANCHES ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]
branch_options = ["-- Select Branch --"] + branches

# ---------------- HEADER CONTROL ----------------
st.subheader("Select Branch")

if st.session_state.selected_branch == "-- Select Branch --":

    with st.popover("Choose Branch"):
        selected_branch = st.radio("Branch List", branch_options, index=0)

        if selected_branch != "-- Select Branch --":

            st.session_state.selected_branch = selected_branch

            st.session_state.active_branch = next(
                b for b in branch_data
                if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch
            )

            st.rerun()

else:
    st.success(f"Selected Branch: {st.session_state.selected_branch}")

    if st.button("🔄 REFRESH OR CHANGE BRANCH"):
        st.session_state.selected_branch = "-- Select Branch --"
        st.session_state.authenticated = False
        st.session_state.active_branch = None
        st.session_state.last_activity = None
        st.rerun()

branch_info = st.session_state.active_branch

# ---------------- PASSWORD SYSTEM ----------------
def load_passwords():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    records = sheet.get_all_records()

    passwords = {"admin": load_admin()["admin"]}

    for row in records:
        key = f"{row['BranchCode']} - {row['BranchName']}"
        passwords[key] = row.get("Password", "")

    return passwords

passwords = load_passwords()

# ---------------- LOGIN (FIXED GATE) ----------------

# 🔥 THIS FIX PREVENTS “AUTO LOGGED IN UI BUG”
show_login = (
    not st.session_state.authenticated
    or not st.session_state.active_branch
)

if st.session_state.selected_branch != "-- Select Branch --":

    if show_login:

        st.subheader("Branch Login")

        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login"):

                if passwords.get(st.session_state.selected_branch, "") == password:

                    st.session_state.authenticated = True
                    st.session_state.last_activity = time.time()
                    st.session_state.active_branch = branch_info

                    st.rerun()

                else:
                    st.error("Incorrect password")

        with col2:
            if st.button("Reset Password"):
                st.session_state.reset_mode = True

# ---------------- AFTER LOGIN ----------------
if st.session_state.authenticated and st.session_state.active_branch:

    st.success(f"Logged in: {st.session_state.selected_branch}")

    col1, col2, col3 = st.columns(3)

    if col1.button("📦 Stock Record"):
        st.session_state.last_activity = time.time()
        st.switch_page("pages/stock_consumption.py")

    if col3.button("🔍 Stock View"):
        st.session_state.last_activity = time.time()
        st.switch_page("pages/stock_view.py")

# ---------------- BACK ----------------
if st.button("⬅ Back"):
    st.switch_page("app.py")
