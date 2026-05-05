import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Login System", layout="centered")

st.title("🔐 Login System")

# -----------------------------
# GOOGLE SHEETS AUTH
# -----------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds_dict = dict(st.secrets["GOOGLE_CREDS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"Google Auth Error: {e}")
    st.stop()

# -----------------------------
# USERS SHEET
# -----------------------------
sheet_id = st.secrets["SHEET_ID"]
users_sheet = client.open_by_key(sheet_id).worksheet("users")

# -----------------------------
# LOAD USERS
# -----------------------------
def load_users():
    data = users_sheet.get_all_values()
    users = {}

    for row in data[1:]:
        if len(row) >= 2:
            users[row[0].strip()] = row[1].strip()

    return users

# -----------------------------
# VALIDATE LOGIN
# -----------------------------
def validate_login(username, password):
    users = load_users()
    return username in users and users[username] == password

# -----------------------------
# CREATE / UPDATE PASSWORD
# -----------------------------
def set_password(username, password):
    data = users_sheet.get_all_values()

    # update if exists
    for i, row in enumerate(data[1:], start=2):
        if row[0].strip() == username:
            users_sheet.update_cell(i, 2, password)
            return "updated"

    # else create new user
    users_sheet.append_row([username, password])
    return "created"

# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -----------------------------
# LOGIN UI
# -----------------------------
if not st.session_state.logged_in:

    tab1, tab2 = st.tabs(["Login", "Create / Reset Password"])

    # ---------------- LOGIN ----------------
    with tab1:
        st.subheader("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            if validate_login(username, password):
                st.success("Login Successful")
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid username or password")

    # ---------------- CREATE / RESET ----------------
    with tab2:
        st.subheader("Create / Reset Password")

        new_user = st.text_input("Username (new or existing)")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Save Password"):

            if new_user.strip() == "" or new_pass.strip() == "":
                st.warning("Fill all fields")
            else:
                result = set_password(new_user, new_pass)

                if result == "updated":
                    st.success("Password updated successfully")
                else:
                    st.success("New user created successfully")

# -----------------------------
# AFTER LOGIN
# -----------------------------
else:
    st.success(f"Welcome {st.session_state.user} 🎉")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
