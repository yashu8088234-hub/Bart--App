import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from pathlib import Path
import pandas as pd
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="BART Staff Dashboard")

SESSION_TIMEOUT = 2 * 60

# ---------------- INIT SESSION STATE ----------------
def init_session():
    defaults = {
        "authenticated": False,
        "selected_branch": "-- Select Branch --",
        "auth_branch": None,
        "active_branch": None,
        "last_activity": None,
        "reset_mode": False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ---------------- ACTIVITY ----------------
def refresh_activity():
    st.session_state.last_activity = time.time()

def check_timeout():
    if st.session_state.authenticated and st.session_state.last_activity:
        if time.time() - st.session_state.last_activity > SESSION_TIMEOUT:
            st.session_state.authenticated = False
            st.session_state.auth_branch = None
            st.session_state.active_branch = None
            st.warning("⏱️ Session expired due to inactivity")
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

# ---------------- UI ----------------
st.title("BART Staff Dashboard")
st.subheader("Select Branch")

# ---------------- BRANCH SELECT ----------------
if st.session_state.selected_branch == "-- Select Branch --":

    selected = st.selectbox("Choose Branch", branch_options)

    if selected != "-- Select Branch --":

        st.session_state.selected_branch = selected

        st.session_state.active_branch = next(
            b for b in branch_data
            if f"{b['BranchCode']} - {b['BranchName']}" == selected
        )

        st.rerun()

else:
    st.success(f"Branch: {st.session_state.selected_branch}")

    if st.button("🔄 Change Branch"):
        st.session_state.selected_branch = "-- Select Branch --"
        st.session_state.authenticated = False
        st.session_state.auth_branch = None
        st.session_state.active_branch = None
        st.rerun()

branch_info = st.session_state.active_branch

# ---------------- PASSWORD ----------------
def load_admin():
    file = Path(__file__).parent / "passwords.json"
    return json.load(open(file))

def load_passwords():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    records = sheet.get_all_records()

    passwords = {"admin": load_admin()["admin"]}

    for row in records:
        key = f"{row['BranchCode']} - {row['BranchName']}"
        passwords[key] = row.get("Password", "")

    return passwords

passwords = load_passwords()

# ---------------- LOGIN ----------------
if st.session_state.selected_branch != "-- Select Branch --":

    if not st.session_state.authenticated:

        st.subheader("Branch Login")

        password = st.text_input("Password", type="password")

        if st.button("Login"):

            if passwords.get(st.session_state.selected_branch) == password:

                st.session_state.authenticated = True
                st.session_state.auth_branch = st.session_state.selected_branch
                st.session_state.active_branch = branch_info
                st.session_state.last_activity = time.time()

                st.success("Login successful")
                st.rerun()

            else:
                st.error("Incorrect password")

# ---------------- AFTER LOGIN ----------------
if st.session_state.authenticated:

    st.success(f"Logged in: {st.session_state.selected_branch}")

    col1, col2 = st.columns(2)

    if col1.button("📦 Stock Record"):
        refresh_activity()
        st.switch_page("pages/stock_consumption.py")

    if col2.button("🔍 Stock View"):
        refresh_activity()
        st.info("Stock view page here")
