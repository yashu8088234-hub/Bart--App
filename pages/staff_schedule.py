import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide", page_title="BART Master Schedule")
MASTER_SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"

# Authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    if st.button("Go to Login"): st.switch_page("app.py")
    st.stop()

# Connection
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
master_sheet = client.open_by_key(MASTER_SHEET_ID)

# ---------------- SETTINGS ----------------
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
ROLE_OPTIONS = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]
TIME_OPTIONS = [f"{h}:00 AM" for h in range(1, 13)] + [f"{h}:00 PM" for h in range(1, 13)] + ["OFF"]
SHIFT_OPTIONS = ["Morning shift", "Mid shift", "Evening shift", "Night shift"]

# ---------------- UI & TOGGLE ----------------
st.title(f"🏢 Weekly Schedule: {st.session_state.selected_branch}")
start_date = st.date_input("Week Start Date")
shift_mode = st.toggle("Enable Shift-wise Mode (Disable for Hourly Mode)")

# Define Headers based on mode
if shift_mode:
    HEADERS = ["Branch", "Date", "Name", "Role"] + DAYS
else:
    HEADERS = ["Branch", "Date", "Name", "Role"]
    for day in DAYS:
        HEADERS.append(f"{day}: Start")
        HEADERS.append(f"{day}: Finish")

# ---------------- DATA HANDLING ----------------
def get_data():
    try:
        ws = master_sheet.worksheet("StaffSchedule")
        data = ws.get_all_values()
        return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 0 else pd.DataFrame(columns=HEADERS)
    except:
        return pd.DataFrame(columns=HEADERS)

df = get_data()

# ---------------- EDITOR CONFIG ----------------
column_config = {"Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS)}

if shift_mode:
    for day in DAYS:
        column_config[day] = st.column_config.SelectboxColumn(day, options=SHIFT_OPTIONS)
else:
    for day in DAYS:
        column_config[f"{day}: Start"] = st.column_config.SelectboxColumn("Start", options=TIME_OPTIONS)
        column_config[f"{day}: Finish"] = st.column_config.SelectboxColumn("Finish", options=TIME_OPTIONS)

edited_df = st.data_editor(df, column_config=column_config, num_rows="dynamic", use_container_width=True)

# ---------------- SAVE ----------------
if st.button("💾 Save to Master Sheet", type="primary"):
    save_df = edited_df.copy()
    save_df["Branch"] = st.session_state.selected_branch
    save_df["Date"] = str(start_date)
    save_df["Name"] = save_df["Name"].astype(str).str.upper()
    
    # Reindex to match current headers
    save_df = save_df.reindex(columns=HEADERS)
    
    try:
        ws = master_sheet.worksheet("StaffSchedule")
        ws.clear()
        ws.update(range_name='A1', values=[HEADERS] + save_df.fillna("").values.tolist())
        st.success("✅ Saved Successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

if st.button("⬅ Back"): st.switch_page("app.py")
