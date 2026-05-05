import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from background import set_background
import json
from pathlib import Path

# -----------------------------
# PAGE CONFIG (MUST BE FIRST)
# -----------------------------
st.set_page_config(layout="wide")

# -----------------------------
# BACKGROUND
# -----------------------------
set_background("barthomepage.jpg")

# -----------------------------
# ADMIN PASSWORD FILE SETUP
# -----------------------------
FILE_NAME = Path(__file__).parent / "passwords.json"

def init_file():
    if not FILE_NAME.exists():
        with open(FILE_NAME, "w") as f:
            json.dump({"admin": "admin123"}, f)

def load_admin():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

init_file()

# -----------------------------
# SESSION STATE
# -----------------------------
defaults = {
    "authenticated": False,
    "auth_branch": None,
    "reset_mode": False,
    "pending_action": None,
    "selected_branch": "-- Select Branch --"
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# UI
# -----------------------------
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
input {
    caret-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# GOOGLE SHEETS SETUP
# -----------------------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# -----------------------------
# CACHED BRANCH LOAD (FAST)
# -----------------------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]

# -----------------------------
# BRANCH SELECT
# -----------------------------
branch_options = ["-- Select Branch --"] + branches

if st.session_state.selected_branch in branch_options:
    default_index = branch_options.index(st.session_state.selected_branch)
else:
    default_index = 0

selected_branch = st.selectbox(
    "Select Branch",
    branch_options,
    index=default_index,
    key="branch_selectbox"
)

st.session_state.selected_branch = selected_branch

branch_info = None

if selected_branch != "-- Select Branch --":
    branch_info = next(
        b for b in branch_data
        if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch
    )

    st.session_state.sheet_id = branch_info["SheetID"]
    st.session_state.branch_info = branch_info

# -----------------------------
# PASSWORD SYSTEM (FAST CACHE FIX)
# -----------------------------
@st.cache_data(ttl=300)
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

# -----------------------------
# MAIN LOGIC
# -----------------------------
if selected_branch != "-- Select Branch --":

    passwords = load_passwords()

    if st.session_state.reset_mode:

        st.subheader("Reset Password (Admin Required)")

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

        st.subheader("Enter Branch Password")

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

        st.write(f"### Selected Branch: {selected_branch}")

        col1, col2, col3, col4, col5 = st.columns(5)

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

        action = st.session_state.pending_action

        if action:

            if action == "stock":
                st.switch_page("pages/stock_consumption.py")
                st.session_state.pending_action = None

            elif action == "sales":
                st.switch_page("pages/daily_sales.py")
                st.session_state.pending_action = None

            elif action == "newstock":
                st.switch_page("pages/new_stock.py")
                st.session_state.pending_action = None

            elif action == "stock_view":
                branch_file = client.open_by_key(branch_info["SheetID"])
                data = branch_file.worksheet("Stocks").get_all_records()
                st.dataframe(data, use_container_width=True, height=600)

            elif action == "sales_view":
                branch_file = client.open_by_key(branch_info["SheetID"])
                data = branch_file.worksheet("Sales").get_all_records()
                st.dataframe(data, use_container_width=True, height=600)

if st.button("⬅ Back"):
    st.switch_page("app.py")
