import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from background import set_background
import json
import os
from pathlib import Path

# -----------------------------
# PASSWORD FILE SETUP (FIXED)
# -----------------------------
FILE_NAME = Path(__file__).parent / "passwords.json"

def init_file():
    if not FILE_NAME.exists():
        with open(FILE_NAME, "w") as f:
            json.dump({"admin": "admin123"}, f)

def load_passwords():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

def save_passwords(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=4)

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
# BACKGROUND & UI
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
</style>
""", unsafe_allow_html=True)

# -----------------------------
# GOOGLE SHEETS
# -----------------------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

@st.cache_data
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]

# -----------------------------
# BRANCH SELECT
# -----------------------------
if "selected_branch" not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

st.session_state.selected_branch = st.selectbox(
    "Select Branch",
    ["-- Select Branch --"] + branches,
    index=(branches.index(st.session_state.selected_branch) + 1)
    if st.session_state.selected_branch in branches else 0
)

selected_branch = st.session_state.selected_branch

# -----------------------------
# ACTION BUTTONS
# -----------------------------
if selected_branch != "-- Select Branch --":

    branch_info = next(
        b for b in branch_data
        if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch
    )

    st.write(f"### Selected Branch: {selected_branch}")

    col1, col2, col3, col4, col5 = st.columns(5)

    if col1.button("📦 Daily Stock Consumption", key="stock_btn"):
        st.session_state.pending_action = "stock"

    if col2.button("💰 Daily Sales Report", key="sales_btn"):
        st.session_state.pending_action = "sales"

    if col3.button("🆕 New Stock Report", key="newstock_btn"):
        st.session_state.pending_action = "newstock"

    if col4.button("🔍 Stock View", key="stock_view_btn"):
        st.session_state.pending_action = "stock_view"

    if col5.button("📊 Sales View", key="sales_view_btn"):
        st.session_state.pending_action = "sales_view"

    passwords = load_passwords()

    # -----------------------------
    # LOGIN
    # -----------------------------
    if st.session_state.pending_action and not st.session_state.authenticated and not st.session_state.reset_mode:

        st.subheader("Enter Branch Password")

        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", key="login_btn"):
            if passwords.get(selected_branch) == password:
                st.session_state.authenticated = True
                st.session_state.auth_branch = selected_branch
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Incorrect password")

        if st.button("Reset Password", key="reset_btn"):
            st.session_state.reset_mode = True
            st.rerun()

    # -----------------------------
    # RESET PASSWORD
    # -----------------------------
    if st.session_state.reset_mode:

        st.subheader("Reset Password (Admin Required)")

        admin_pass = st.text_input("Admin Password", type="password", key="admin_pass")
        new_pass = st.text_input("New Password", type="password", key="new_pass")

        if st.button("Update Password", key="update_pass_btn"):

            if admin_pass == passwords.get("admin"):
                passwords[selected_branch] = new_pass
                save_passwords(passwords)

                st.success("Password updated successfully")

                st.session_state.reset_mode = False
                st.rerun()

            else:
                st.error("Wrong admin password")

    # -----------------------------
    # EXECUTE ACTION
    # -----------------------------
    if st.session_state.authenticated and st.session_state.auth_branch == selected_branch:

        st.session_state.sheet_id = branch_info['SheetID']
        action = st.session_state.pending_action

        if action == "stock":
            st.switch_page("pages/stock_consumption.py")

        elif action == "sales":
            st.switch_page("pages/daily_sales.py")

        elif action == "newstock":
            st.switch_page("pages/new_stock.py")

        elif action == "stock_view":
            try:
                branch_file = client.open_by_key(branch_info['SheetID'])
                data = branch_file.worksheet("Stocks").get_all_records()
                st.dataframe(data, use_container_width=True, height=600)
            except Exception as e:
                st.error(e)

        elif action == "sales_view":
            try:
                branch_file = client.open_by_key(branch_info['SheetID'])
                data = branch_file.worksheet("Sales").get_all_records()
                st.dataframe(data, use_container_width=True, height=600)
            except Exception as e:
                st.error(e)

# -----------------------------
# BACK BUTTON
# -----------------------------
if st.button("⬅ Back", key="back_btn"):
    st.switch_page("app.py")
