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

# ---------------- UI ----------------
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}

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

# ---------------- HEADER ----------------
st.markdown("""
<div style="background: linear-gradient(90deg,#1f1f2e,#4b6cb7);
padding:20px;border-radius:12px;text-align:center;margin-bottom:20px;">
<h1 style='color:white;margin:0;'>BART Staff Dashboard</h1>
<p style='color:#e0e0e0;margin:0;'>Select Branch & Access Operations</p>
</div>
""", unsafe_allow_html=True)

# ---------------- INIT ----------------
FILE_NAME = Path(__file__).parent / "passwords.json"

if not FILE_NAME.exists():
    with open(FILE_NAME, "w") as f:
        json.dump({"admin": "admin123"}, f)

def load_admin():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

# ---------------- SESSION ----------------
defaults = {
    "stage": "select_branch",
    "authenticated": False,
    "selected_branch": "-- Select Branch --",
    "auth_branch": None,
    "sheet_id": None,
    "branch_info": None,
    "last_activity": None
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- GOOGLE SHEETS ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ---------------- BRANCHES ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branch_data = load_branches()

branch_options = ["-- Select Branch --"] + [
    f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data
]

def get_branch_info(name):
    return next(
        b for b in branch_data
        if f"{b['BranchCode']} - {b['BranchName']}" == name
    )

# ---------------- PASSWORDS ----------------
@st.cache_data(ttl=300)
def load_passwords():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    records = sheet.get_all_records()

    passwords = {"admin": load_admin()["admin"]}

    for row in records:
        key = f"{row['BranchCode']} - {row['BranchName']}"
        passwords[key] = str(row.get("Password", "")).strip()

    return passwords

passwords = load_passwords()

# ---------------- SAFE AUTH CHECK ----------------
def is_authenticated():
    return (
        st.session_state.get("authenticated", False)
        and st.session_state.get("sheet_id") is not None
        and st.session_state.get("auth_branch") is not None
    )

# ---------------- BACK BUTTON ----------------
def back():
    if st.button("⬅ Back"):
        if st.session_state.stage == "login":
            st.session_state.stage = "select_branch"
            st.session_state.selected_branch = "-- Select Branch --"
            st.rerun()

        elif st.session_state.stage == "dashboard":
            st.session_state.stage = "login"
            st.session_state.authenticated = False
            st.rerun()

# ---------------- STEP 1 ----------------
if st.session_state.stage == "select_branch":

    st.subheader("Select Branch")

    with st.popover("Choose Branch"):
        selected = st.radio("Branches", branch_options, index=0)

        if selected != "-- Select Branch --":
            st.session_state.selected_branch = selected
            st.session_state.branch_info = get_branch_info(selected)
            st.session_state.stage = "login"
            st.rerun()

# ---------------- STEP 2 ----------------
elif st.session_state.stage == "login":

    back()

    st.subheader(f"Login: {st.session_state.selected_branch}")

    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if password == passwords.get(st.session_state.selected_branch, ""):

            # 🔥 FULL SESSION SET BEFORE ANY NAVIGATION
            st.session_state.authenticated = True
            st.session_state.auth_branch = st.session_state.selected_branch
            st.session_state.sheet_id = st.session_state.branch_info["SheetID"]
            st.session_state.last_activity = time.time()

            st.session_state.stage = "dashboard"

            st.rerun()

        else:
            st.error("Incorrect password")

# ---------------- STEP 3 ----------------
elif st.session_state.stage == "dashboard":

    # 🔥 HARD SAFETY GATE
    if not is_authenticated():
        st.warning("Session expired. Please login again.")
        st.session_state.stage = "login"
        st.rerun()

    back()

    st.success(f"Logged in: {st.session_state.auth_branch}")

    col1, col2, col3 = st.columns(3)

    # ---------------- STOCK RECORD (FIXED) ----------------
    if col1.button("📦 Stock Record"):

        if is_authenticated():
            st.switch_page("pages/stock_consumption.py")
        else:
            st.warning("Session not ready. Please login again.")
            st.session_state.stage = "login"
            st.rerun()

    # ---------------- CHANGE BRANCH ----------------
    if col2.button("🔄 Change Branch"):
        st.session_state.stage = "select_branch"
        st.session_state.authenticated = False
        st.session_state.auth_branch = None
        st.session_state.sheet_id = None
        st.rerun()

    # ---------------- STOCK VIEW ----------------
    if col3.button("🔍 Stock View"):

        sheet = client.open_by_key(st.session_state.sheet_id)
        ws = sheet.worksheet("Stocks")

        data = ws.get_all_values()

        headers = data[0]
        date_columns = headers[1:]

        daily, weekly = [], []
        current = None

        for row in data:

            txt = " ".join(row).lower()

            if "daily item" in txt:
                current = "daily"
                continue

            if "weekly item" in txt:
                current = "weekly"
                continue

            if current is None or not row or not row[0]:
                continue

            item = row[0]
            values = row[1:] + [""] * (len(date_columns) - len(row[1:]))

            cleaned = []
            total = 0

            for i, v in enumerate(values):

                if i < 3:
                    cleaned.append(v)
                    continue

                try:
                    num = float(v) if v != "" else 0
                except:
                    num = 0

                cleaned.append(num)
                total += num

            row_dict = {"Item": item}

            for i, col in enumerate(date_columns):
                row_dict[col] = cleaned[i]

            row_dict["Total"] = total

            if current == "daily":
                daily.append(row_dict)
            else:
                weekly.append(row_dict)

        st.subheader("Daily Stock")
        st.dataframe(pd.DataFrame(daily), use_container_width=True)

        st.subheader("Weekly Stock")
        st.dataframe(pd.DataFrame(weekly), use_container_width=True)
