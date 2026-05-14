import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from pathlib import Path
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
import datetime

# ---------------- EMAIL CONFIG ----------------
ADMIN_EMAIL = "yash2002anitha@gmail.com"
SMTP_EMAIL = "yash2002anitha@gmail.com"
SMTP_PASSWORD = "lhzl fyvw aorj akzf"  # IMPORTANT
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_submission_email(name, email, branch, timestamp, details=""):
    subject = f"📦 Staff Submission - {branch}"

    body = f"""
NEW SUBMISSION

Name: {name}
Email: {email}
Branch: {branch}
Time: {timestamp}

Details:
{details}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = ADMIN_EMAIL

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, ADMIN_EMAIL, msg.as_string())
        server.quit()
    except Exception as e:
        st.error(f"Email failed: {e}")


# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="BART Staff Dashboard")

SESSION_TIMEOUT = 2 * 60

# ---------------- UI STYLE ----------------
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

# ---------------- SESSION ----------------
defaults = {
    "authenticated": False,
    "auth_branch": None,
    "reset_mode": False,
    "selected_branch": "-- Select Branch --",
    "last_activity": None,
    "submit_popup": False
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def refresh_activity():
    st.session_state.last_activity = time.time()


def check_timeout():
    if st.session_state.authenticated and st.session_state.last_activity:
        if time.time() - st.session_state.last_activity > SESSION_TIMEOUT:
            st.session_state.authenticated = False
            st.session_state.auth_branch = None
            st.session_state.last_activity = None
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

# ---------------- BRANCHES ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]
branch_options = ["-- Select Branch --"] + branches

st.subheader("Select Branch")

if st.session_state.selected_branch == "-- Select Branch --":
    with st.popover("Choose Branch"):
        selected_branch = st.radio("Branch List", branch_options, index=0)

        if selected_branch != "-- Select Branch --":
            st.session_state.selected_branch = selected_branch
            st.rerun()
else:
    st.success(f"Selected Branch: {st.session_state.selected_branch}")

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

                    st.session_state.sheet_id = branch_info["SheetID"]
                    st.session_state.branch_info = branch_info

                    st.rerun()
                else:
                    st.error("Incorrect password")

        with col2:
            if st.button("Reset Password"):
                st.session_state.reset_mode = True

    # ---------------- AFTER LOGIN ----------------
    if st.session_state.authenticated:

        st.success(f"Logged in: {st.session_state.selected_branch}")

        col1, col2, col3 = st.columns(3)

        # ---------------- STOCK VIEW ----------------
        if col3.button("🔍 Stock View"):
            refresh_activity()

            sheet = client.open_by_key(branch_info["SheetID"])
            ws = sheet.worksheet("Stocks")

            data = ws.get_all_values()

            headers = data[0]
            date_columns = headers[1:]

            daily = []
            weekly = []
            current_section = None

            for row in data:

                row_text = " ".join(row).lower()

                if "daily item" in row_text:
                    current_section = "daily"
                    continue

                if "weekly item" in row_text:
                    current_section = "weekly"
                    continue

                if current_section is None or not row or not row[0]:
                    continue

                item = row[0].strip()
                values = row[1:]
                values += [""] * (len(date_columns) - len(values))

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

                if current_section == "daily":
                    daily.append(row_dict)
                else:
                    weekly.append(row_dict)

            st.subheader("Daily Stock")
            st.dataframe(pd.DataFrame(daily), use_container_width=True)

            st.subheader("Weekly Stock")
            st.dataframe(pd.DataFrame(weekly), use_container_width=True)

        # ---------------- SUBMIT BUTTON ----------------
        if st.button("Submit Data"):
            st.session_state.submit_popup = True

# ---------------- POPUP ----------------
if st.session_state.submit_popup:

    st.subheader("Confirm Submission")

    with st.form("submit_form"):

        name = st.text_input("Name")
        email = st.text_input("Email")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        st.info(f"Time: {timestamp}")

        submit = st.form_submit_button("Confirm Submit")

        if submit:

            if name and email:

                send_submission_email(
                    name=name,
                    email=email,
                    branch=st.session_state.selected_branch,
                    timestamp=timestamp,
                    details="Stock submission from dashboard"
                )

                st.success("Submitted & Email Sent!")

                st.session_state.submit_popup = False
                st.rerun()

            else:
                st.error("Please enter name and email")

# ---------------- BACK ----------------
if st.button("⬅ Back"):
    st.switch_page("app.py")
