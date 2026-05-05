import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="BART Staff Dashboard")

# ---------------- CLEAN UI STYLE ----------------
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

/* ---------------- MOBILE CARD STYLE ---------------- */
.branch-card {
    padding: 16px;
    margin: 10px 0;
    border-radius: 14px;
    background: white;
    border: 1px solid #e0e0e0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    transition: 0.2s;
    cursor: pointer;
    text-align: left;
}

.branch-card:hover {
    transform: scale(1.01);
    border-color: #4b6cb7;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}

.selected {
    border: 2px solid #4b6cb7;
    background: #eef3ff;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
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

# ---------------- SESSION STATE ----------------
defaults = {
    "authenticated": False,
    "auth_branch": None,
    "reset_mode": False,
    "selected_branch": "-- Select Branch --"
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

# ---------------- LOAD BRANCHES ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]

# ---------------- 🔥 MOBILE APP STYLE BRANCH PICKER ----------------
st.subheader("Select Branch")

for b in branches:

    is_selected = st.session_state.selected_branch == b

    if st.button(
        f"🏢 {b}",
        key=b
    ):
        st.session_state.selected_branch = b
        st.rerun()

    # visual highlight (selected state)
    if is_selected:
        st.markdown("""
        <style>
        button[kind="secondary"] {
            border: 2px solid #4b6cb7 !important;
            background: #eef3ff !important;
        }
        </style>
        """, unsafe_allow_html=True)

selected_branch = st.session_state.selected_branch

# ---------------- BRANCH INFO ----------------
branch_info = None

if selected_branch != "-- Select Branch --":
    branch_info = next(
        b for b in branch_data
        if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch
    )
    st.session_state.sheet_id = branch_info["SheetID"]
    st.session_state.branch_info = branch_info

# ---------------- PASSWORD SYSTEM ----------------
FILE_NAME = Path(__file__).parent / "passwords.json"

def load_admin():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

def load_passwords():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    records = sheet.get_all_records()

    passwords = {"admin": load_admin()["admin"]}

    for row in records:
        key = f"{row['BranchCode']} - {row['BranchName']}"
        passwords[key] = row.get("Password", "")

    return passwords

def save_passwords(branch_key, new_password):
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    records = sheet.get_all_records()

    for idx, row in enumerate(records, start=2):
        key = f"{row['BranchCode']} - {row['BranchName']}"
        if key == branch_key:
            col_index = list(row.keys()).index("Password") + 1
            sheet.update_cell(idx, col_index, new_password)
            return

# ---------------- MAIN ----------------
if selected_branch != "-- Select Branch --":

    passwords = load_passwords()

    if st.session_state.reset_mode:
        st.subheader("Reset Password")

        admin_pass = st.text_input("Admin Password", type="password")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            if admin_pass == load_admin()["admin"]:
                save_passwords(selected_branch, new_pass)
                st.success("Password updated successfully")
                st.session_state.reset_mode = False
            else:
                st.error("Wrong admin password")

    if not st.session_state.authenticated:
        st.subheader("Branch Login")

        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login"):
                if passwords.get(selected_branch, "") == password:
                    st.session_state.authenticated = True
                    st.session_state.auth_branch = selected_branch
                    st.rerun()
                else:
                    st.error("Incorrect password")

        with col2:
            if st.button("Reset Password"):
                st.session_state.reset_mode = True

    if st.session_state.authenticated:

        st.success(f"Logged in: {selected_branch}")

        col1, col2, col3, col4, col5 = st.columns(5)

        if col1.button("📦 Stock Consumption"):
            st.switch_page("pages/stock_consumption.py")

        if col2.button("💰 Sales Report"):
            st.switch_page("pages/daily_sales.py")

        if col3.button("🆕 New Stock"):
            st.switch_page("pages/new_stock.py")

        if col4.button("🔍 Stock View"):
            sheet = client.open_by_key(branch_info["SheetID"])
            data = sheet.worksheet("Stocks").get_all_records()
            st.dataframe(data, use_container_width=True, height=500)

        if col5.button("📊 Sales View"):
            sheet = client.open_by_key(branch_info["SheetID"])
            data = sheet.worksheet("Sales").get_all_records()
            st.dataframe(data, use_container_width=True, height=500)

# ---------------- BACK ----------------
if st.button("⬅ Back"):
    st.switch_page("app.py")
