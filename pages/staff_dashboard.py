import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from pathlib import Path
import pandas as pd

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

# ---------------- ADMIN PASSWORD FILE ----------------
FILE_NAME = Path(__file__).parent / "passwords.json"

def init_file():
    if not FILE_NAME.exists():
        with open(FILE_NAME, "w") as f:
            json.dump({"admin": "admin123"}, f)

def load_admin():
    with open(FILE_NAME, "r") as f:
        return json.load(f)

init_file()

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
branch_options = ["-- Select Branch --"] + branches

# ---------------- BRANCH SELECT ----------------
st.subheader("Select Branch")

if st.session_state.selected_branch == "-- Select Branch --":

    with st.popover("Choose Branch"):
        selected_branch = st.radio("Branch List", branch_options, index=0)

        if selected_branch != "-- Select Branch --":
            st.session_state.selected_branch = selected_branch
            st.rerun()

else:
    st.success(f"Selected Branch: {st.session_state.selected_branch}")

    if st.button("🔄 Change Branch"):
        st.session_state.selected_branch = "-- Select Branch --"
        st.rerun()

# ---------------- BRANCH INFO ----------------
branch_info = None

if st.session_state.selected_branch != "-- Select Branch --":
    branch_info = next(
        b for b in branch_data
        if f"{b['BranchCode']} - {b['BranchName']}" == st.session_state.selected_branch
    )

# ---------------- PASSWORD SYSTEM ----------------
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
                    st.rerun()
                else:
                    st.error("Incorrect password")

        with col2:
            if st.button("Reset Password"):
                st.session_state.reset_mode = True

    if st.session_state.reset_mode:
        st.subheader("Reset Password")

        admin_pass = st.text_input("Admin Password", type="password")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            if admin_pass == load_admin()["admin"]:
                save_passwords(st.session_state.selected_branch, new_pass)
                st.success("Password updated successfully")
                st.session_state.reset_mode = False
            else:
                st.error("Wrong admin password")

    # ---------------- AFTER LOGIN ----------------
    if st.session_state.authenticated:

        st.success(f"Logged in: {st.session_state.selected_branch}")

        col1, col2, col3 = st.columns(3)

        if col1.button("📦 Stock Record"):
            st.switch_page("pages/stock_consumption.py")

        if col2.button("🆕 New Stock Record"):
            st.switch_page("pages/new_stock.py")

        # ---------------- STOCK VIEW (ONLY FIX HERE) ----------------
        if col3.button("🔍 Stock View"):

            sheet = client.open_by_key(branch_info["SheetID"])
            ws = sheet.worksheet("Stocks")

            data = ws.get_all_values()

            headers = data[0]
            date_columns = headers[1:]

            daily = []
            weekly = []

            current_section = None

            for row in data[1:]:

                if not row:
                    continue

                item = row[0].strip() if len(row) > 0 else ""

                # ✅ ONLY FIX (ROBUST SECTION DETECTION)
                clean_item = "".join(item.lower().split())

                if "daily" in clean_item:
                    current_section = "daily"
                    continue

                if "weekly" in clean_item:
                    current_section = "weekly"
                    continue

                if item == "":
                    continue

                values = row[1:]
                values = values + [""] * (len(date_columns) - len(values))

                cleaned = []
                total = 0

                for v in values:
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

                if current_section == "daily":
                    daily.append(row_dict)

                elif current_section == "weekly":
                    weekly.append(row_dict)

            df_daily = pd.DataFrame(daily)
            df_weekly = pd.DataFrame(weekly)

            st.subheader("📦 Daily Items Stock")
            st.dataframe(df_daily, use_container_width=True, height=400)

            st.subheader("📦 Weekly Items Stock")
            st.dataframe(df_weekly, use_container_width=True, height=400)

# ---------------- BACK ----------------
if st.button("⬅ Back"):
    st.switch_page("app.py")
