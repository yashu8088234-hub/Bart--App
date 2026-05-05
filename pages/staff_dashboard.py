import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from background import set_background
import json
import os
from pathlib import Path   # ✅ ONLY ADDITION

# -----------------------------
# PASSWORD FILE SETUP
# -----------------------------
FILE_NAME = Path(__file__).parent / "passwords.json"   # ✅ ONLY FIX

def init_file():
    if not FILE_NAME.exists():
        with open(FILE_NAME, "w") as f:
            json.dump({"admin": "admin123"}, f)

def load_passwords():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

def save_passwords(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f)

init_file()

# -----------------------------
# SESSION STATE
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "auth_branch" not in st.session_state:
    st.session_state.auth_branch = None

if "reset_mode" not in st.session_state:
    st.session_state.reset_mode = False

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

# -----------------------------
# Background & UI Setup
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(layout="wide")
st.title("BART")
st.markdown("## Staff Dashboard")
st.write("## Kindly choose your Branch Name")

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; margin:0 auto !important; max-width: 100% !important;}
body {
    background-size: cover !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# GOOGLE SHEETS SETUP (FIXED ONLY HERE)
# -----------------------------
creds_dict = json.loads(st.secrets["GOOGLE_CREDS_JSON"])  # ✅ FIX

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# -----------------------------
# LOAD BRANCH DATA
# -----------------------------
@st.cache_data
def load_branches():
    try:
        sheet = client.open("MASTERBRANCHSHEET").sheet1
        return sheet.get_all_records()
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("MASTERBRANCHSHEET not found.")
        st.stop()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]

# -----------------------------
# BRANCH SELECTION
# -----------------------------
if 'selected_branch' not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

st.session_state.selected_branch = st.selectbox(
    "Select Branch",
    ["-- Select Branch --"] + branches,
    index=branches.index(st.session_state.selected_branch) + 1
    if st.session_state.selected_branch != "-- Select Branch --" else 0
)

selected_branch = st.session_state.selected_branch

# -----------------------------
# BUTTONS + AUTH CONTROL
# -----------------------------
if selected_branch != "-- Select Branch --":
    branch_info = next(b for b in branch_data if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch)

    st.write(f"### Selected Branch: {selected_branch}")

    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")

    if col1.button("📦 Daily Stock Consumption"):
        st.session_state.pending_action = "stock"

    if col2.button("💰 Daily Sales Report"):
        st.session_state.pending_action = "sales"

    if col3.button("🆕 New Stock Report"):
        st.session_state.pending_action = "newstock"

    if col4.button("🔍 Stock View"):
        st.session_state.pending_action = "stock_view"

    if col5.button("📊 Daily Sales View"):
        st.session_state.pending_action = "sales_view"

    passwords = load_passwords()

    # -----------------------------
    # LOGIN
    # -----------------------------
    if st.session_state.pending_action and not st.session_state.authenticated and not st.session_state.reset_mode:
        st.subheader("Enter Branch Password")

        password = st.text_input("Password", type="password")

        branch_key = selected_branch

        if st.button("Login"):
            if passwords.get(branch_key, "") == password:
                st.session_state.authenticated = True
                st.session_state.auth_branch = branch_key
            else:
                st.error("Incorrect password")

        if st.button("Reset Password"):
            st.session_state.reset_mode = True

    # -----------------------------
    # RESET PASSWORD
    # -----------------------------
    if st.session_state.reset_mode:
        st.subheader("Reset Password (Admin Required)")

        admin_pass = st.text_input("Admin Password", type="password")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            if admin_pass == passwords.get("admin"):
                passwords[selected_branch] = new_pass
                save_passwords(passwords)
                st.success("Password updated")
                st.session_state.reset_mode = False
            else:
                st.error("Wrong admin password")

    # -----------------------------
    # EXECUTE ACTION AFTER LOGIN
    # -----------------------------
    if st.session_state.authenticated and st.session_state.auth_branch == selected_branch:

        st.session_state.sheet_id = branch_info['SheetID']
        st.session_state.selected_branch = selected_branch

        action = st.session_state.pending_action

        if action == "stock":
            st.session_state.tab_name = "Stocks"
            st.switch_page("pages/stock_consumption.py")

        elif action == "sales":
            st.session_state.tab_name = "Sales"
            st.switch_page("pages/daily_sales.py")

        elif action == "newstock":
            st.session_state.tab_name = "NewStocks"
            st.switch_page("pages/new_stock.py")

        elif action == "stock_view":
            try:
                branch_file = client.open_by_key(branch_info['SheetID'])
                data = branch_file.worksheet("Stocks").get_all_records()
                st.dataframe(data, use_container_width=True, height=600)
            except Exception as e:
                st.error(f"Error: {e}")

        elif action == "sales_view":
            try:
                branch_file = client.open_by_key(branch_info['SheetID'])
                data = branch_file.worksheet("Sales").get_all_records()
                st.dataframe(data, use_container_width=True, height=600)
            except Exception as e:
                st.error(f"Error: {e}")

# -----------------------------
# BACK BUTTON
# -----------------------------
if st.button("⬅ Back"):
    st.switch_page("app.py")
