import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from background import set_background

# -----------------------------
# BACKGROUND & UI SETUP
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
# LOAD MASTER SHEET
# -----------------------------
@st.cache_data(ttl=60)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet

sheet = load_branches()
branch_data = sheet.get_all_records()

# -----------------------------
# HELPERS (PASSWORD SYSTEM)
# -----------------------------
def get_password(branch_key):
    for row in branch_data:
        if f"{row['BranchCode']} - {row['BranchName']}" == branch_key:
            return row.get("Password", "")
    return ""

def update_password(branch_key, new_password):
    records = sheet.get_all_records()

    for i, row in enumerate(records, start=2):  # sheet rows start at 1 + header
        key = f"{row['BranchCode']} - {row['BranchName']}"
        if key == branch_key:
            sheet.update_cell(i, 4, new_password)  # Column 4 = Password
            return True
    return False

def get_admin_password():
    records = sheet.get_all_records()
    for row in records:
        if row["BranchCode"] == "ADMIN":
            return row.get("Password", "")
    return ""

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

if "selected_branch" not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

# -----------------------------
# BRANCH LIST
# -----------------------------
branches = [
    f"{b['BranchCode']} - {b['BranchName']}"
    for b in branch_data
    if b["BranchCode"] != "ADMIN"
]

st.session_state.selected_branch = st.selectbox(
    "Select Branch",
    ["-- Select Branch --"] + branches,
    index=branches.index(st.session_state.selected_branch) + 1
    if st.session_state.selected_branch != "-- Select Branch --" else 0
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

    # -----------------------------
    # LOGIN
    # -----------------------------
    if st.session_state.pending_action and not st.session_state.authenticated and not st.session_state.reset_mode:

        st.subheader("Enter Branch Password")

        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if password == get_password(selected_branch):
                st.session_state.authenticated = True
                st.session_state.auth_branch = selected_branch
            else:
                st.error("Incorrect password")

        if st.button("Reset Password"):
            st.session_state.reset_mode = True

    # -----------------------------
    # RESET PASSWORD (ADMIN CONTROL)
    # -----------------------------
    if st.session_state.reset_mode:

        st.subheader("Reset Password (Admin Required)")

        admin_pass = st.text_input("Admin Password", type="password")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            if admin_pass == get_admin_password():
                if update_password(selected_branch, new_pass):
                    st.success("Password updated successfully in Google Sheets")
                    st.session_state.reset_mode = False
                else:
                    st.error("Failed to update password")
            else:
                st.error("Wrong admin password")

    # -----------------------------
    # AFTER LOGIN ACTIONS
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
if st.button("⬅ Back"):
    st.switch_page("app.py")
