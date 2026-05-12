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
# 🔥 PRODUCTION SESSION LAYER (ADDED - NO UI CHANGE)
# =========================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "session_store" not in st.session_state:
    st.session_state.session_store = {}

def save_session():
    st.session_state.session_store[st.session_state.session_id] = {
        "authenticated": st.session_state.get("authenticated", False),
        "auth_branch": st.session_state.get("auth_branch"),
        "selected_branch": st.session_state.get("selected_branch"),
        "active_branch": st.session_state.get("active_branch"),
        "last_activity": st.session_state.get("last_activity")
    }

def load_session():
    data = st.session_state.session_store.get(st.session_state.session_id)

    if data:
        st.session_state.authenticated = data["authenticated"]
        st.session_state.auth_branch = data["auth_branch"]
        st.session_state.selected_branch = data["selected_branch"]
        st.session_state.active_branch = data["active_branch"]
        st.session_state.last_activity = data["last_activity"]

# restore session on every refresh
load_session()

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

# ---------------- SESSION DEFAULTS ----------------
defaults = {
    "authenticated": False,
    "auth_branch": None,
    "reset_mode": False,
    "selected_branch": "-- Select Branch --",
    "last_activity": None,
    "active_branch": None
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- ACTIVITY ----------------
def refresh_activity():
    st.session_state.last_activity = time.time()
    save_session()

# ---------------- TIMEOUT ----------------
def check_timeout():
    if st.session_state.authenticated and st.session_state.last_activity:
        if time.time() - st.session_state.last_activity > SESSION_TIMEOUT:
            st.session_state.authenticated = False
            st.session_state.auth_branch = None
            st.session_state.active_branch = None
            st.session_state.last_activity = None
            save_session()
            st.warning("⏱️ Logged out due to inactivity.")
            st.rerun()

check_timeout()

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

# ---------------- BRANCH SELECT ----------------
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

            save_session()
            st.rerun()

else:
    st.success(f"Selected Branch: {st.session_state.selected_branch}")

    if st.button("🔄 REFRESH OR CHANGE BRANCH"):
        st.session_state.selected_branch = "-- Select Branch --"
        st.session_state.authenticated = False
        st.session_state.auth_branch = None
        st.session_state.active_branch = None
        st.session_state.last_activity = None
        save_session()
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

# ---------------- PIN STYLE (UNCHANGED) ----------------
st.markdown("""
<style>
div[data-testid="stDataFrame"] thead th:nth-child(1),
div[data-testid="stDataFrame"] tbody td:nth-child(1) {
    position: sticky;
    left: 0;
    background: white;
    z-index: 3;
}

div[data-testid="stDataFrame"] thead th:nth-child(2),
div[data-testid="stDataFrame"] tbody td:nth-child(2) {
    position: sticky;
    left: 150px;
    background: white;
    z-index: 2;
}

div[data-testid="stDataFrame"] thead th:nth-child(3),
div[data-testid="stDataFrame"] tbody td:nth-child(3) {
    position: sticky;
    left: 300px;
    background: white;
    z-index: 2;
}
</style>
""", unsafe_allow_html=True)

# ---------------- MAIN ----------------
if st.session_state.selected_branch != "-- Select Branch --":

    passwords = load_passwords()

    if not st.session_state.authenticated:

        st.subheader("Branch Login")

        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login"):
                if passwords.get(st.session_state.selected_branch, "") == password:

                    st.session_state.authenticated = True
                    st.session_state.auth_branch = st.session_state.selected_branch
                    st.session_state.last_activity = time.time()
                    st.session_state.active_branch = branch_info

                    save_session()
                    st.rerun()

                else:
                    st.error("Incorrect password")

        with col2:
            if st.button("Reset Password"):
                st.session_state.reset_mode = True

    # ---------------- RESET PASSWORD ----------------
    if st.session_state.reset_mode:
        st.subheader("Reset Password")

        admin_pass = st.text_input("Admin Password", type="password")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            if admin_pass == load_admin()["admin"]:
                sheet = client.open("MASTERBRANCHSHEET").sheet1
                records = sheet.get_all_records()

                for idx, row in enumerate(records, start=2):
                    key = f"{row['BranchCode']} - {row['BranchName']}"
                    if key == st.session_state.selected_branch:
                        col_index = list(row.keys()).index("Password") + 1
                        sheet.update_cell(idx, col_index, new_pass)
                        break

                st.success("Password updated successfully")
                st.session_state.reset_mode = False
                save_session()
            else:
                st.error("Wrong admin password")

    # ---------------- AFTER LOGIN ----------------
    if st.session_state.authenticated:

        st.success(f"Logged in: {st.session_state.selected_branch}")

        col1, col2, col3 = st.columns(3)

        if col1.button("📦 Stock Record"):
            refresh_activity()
            st.session_state.active_branch = branch_info
            save_session()
            st.switch_page("pages/stock_consumption.py")

        if col3.button("🔍 Stock View"):
            refresh_activity()
            save_session()
            st.switch_page("pages/stock_view.py")

# ---------------- BACK ----------------
if st.button("⬅ Back"):
    st.switch_page("staff_dashboard.py")
