import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from pathlib import Path
import uuid

# -----------------------------
# UI SETUP (UNCHANGED)
# -----------------------------
st.set_page_config(layout="wide", page_title="Staff Dashboard")

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
.block-container {padding:1rem 2rem;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# PASSWORD FILE (UNCHANGED)
# -----------------------------
FILE_NAME = Path(__file__).parent / "passwords.json"

if not FILE_NAME.exists():
    with open(FILE_NAME, "w") as f:
        json.dump({"admin": "admin123"}, f)

def load_admin():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

# -----------------------------
# SESSION STATE (UNCHANGED)
# -----------------------------
if "selected_branch" not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

if "branch_info" not in st.session_state:
    st.session_state.branch_info = None

if "sheet_id" not in st.session_state:
    st.session_state.sheet_id = None

if "tab_name" not in st.session_state:
    st.session_state.tab_name = None

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None

# -----------------------------
# GOOGLE SHEETS (UNCHANGED)
# -----------------------------
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

# -----------------------------
# BRANCHES (UNCHANGED)
# -----------------------------
@st.cache_data(ttl=600)
def load_branches():
    return client.open("MASTERBRANCHSHEET").sheet1.get_all_records()

branch_data = load_branches()

branch_options = ["-- Select Branch --"] + [
    f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data
]

def get_branch(name):
    return next(
        b for b in branch_data
        if f"{b['BranchCode']} - {b['BranchName']}" == name
    )

# -----------------------------
# PASSWORDS (UNCHANGED)
# -----------------------------
@st.cache_data(ttl=300)
def load_passwords():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    records = sheet.get_all_records()

    pw = {"admin": load_admin()["admin"]}

    for r in records:
        key = f"{r['BranchCode']} - {r['BranchName']}"
        pw[key] = str(r.get("Password", "")).strip()

    return pw

passwords = load_passwords()

# -----------------------------
# UI FLOW (UNCHANGED)
# -----------------------------
st.title("Staff Dashboard")

if st.session_state.selected_branch == "-- Select Branch --":

    with st.popover("Select Branch"):
        choice = st.radio("Branches", branch_options)

        if choice != "-- Select Branch --":
            st.session_state.selected_branch = choice
            st.session_state.branch_info = get_branch(choice)

# -----------------------------
# LOGIN SECTION (UNCHANGED)
# -----------------------------
if st.session_state.selected_branch != "-- Select Branch --":

    st.success(f"Selected: {st.session_state.selected_branch}")

    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if password == passwords.get(st.session_state.selected_branch, ""):

            # 🔴 ONLY FIX HERE (CRITICAL)
            st.session_state.sheet_id = st.session_state.branch_info["SheetID"]
            st.session_state.tab_name = "Stocks"
            st.session_state.auth_token = str(uuid.uuid4())

            st.success("Login successful")

        else:
            st.error("Wrong password")

# -----------------------------
# NAVIGATION (ONLY FIX HERE)
# -----------------------------
if st.session_state.sheet_id and st.session_state.tab_name:

    col1, col2 = st.columns(2)

    if col1.button("📦 Stock Record"):

        # 🔴 FIX: ENSURE VALUES ARE READY BEFORE NAVIGATION
        if st.session_state.sheet_id and st.session_state.tab_name:
            st.switch_page("pages/stock_consumption.py")
        else:
            st.error("Session not ready. Try login again.")

    if col2.button("🔄 Change Branch"):

        st.session_state.selected_branch = "-- Select Branch --"
        st.session_state.sheet_id = None
        st.session_state.tab_name = None
        st.session_state.auth_token = None

        st.rerun()
