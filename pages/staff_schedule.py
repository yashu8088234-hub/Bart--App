import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide", page_title="BART Master Schedule")
MASTER_SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"

# Authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    if st.button("Go to Login"): st.switch_page("app.py")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
master_sheet = client.open_by_key(MASTER_SHEET_ID)

# ---------------- HEADERS ----------------
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
# Added Branch and Date columns
HEADERS = ["Branch", "Date", "Name", "Role"]
for day in DAYS:
    HEADERS.append(f"{day}: Start")
    HEADERS.append(f"{day}: Finish")

# ---------------- LOAD DATA ----------------
def get_master_data():
    try:
        ws = master_sheet.worksheet("StaffSchedule")
        data = ws.get_all_values()
        return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 0 else pd.DataFrame(columns=HEADERS)
    except gspread.exceptions.WorksheetNotFound:
        ws = master_sheet.add_worksheet(title="StaffSchedule", rows="100", cols=len(HEADERS))
        ws.append_row(HEADERS)
        return pd.DataFrame(columns=HEADERS)

if "df_schedule" not in st.session_state:
    st.session_state.df_schedule = get_master_data()

# ---------------- UI ----------------
st.title(f"🏢 Master Schedule - {st.session_state.selected_branch}")

col1, col2 = st.columns(2)
start_date = col1.date_input("Week Start Date")
end_date = col2.date_input("Week End Date")

# Configuration for Editor
column_config = {
    "Role": st.column_config.SelectboxColumn("Role", options=["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]),
    "Branch": st.column_config.TextColumn("Branch", disabled=True), # Auto-filled
    "Date": st.column_config.DateColumn("Date", disabled=True)       # Auto-filled
}
for day in DAYS:
    column_config[f"{day}: Start"] = st.column_config.SelectboxColumn("Start", options=[f"{h}:00 AM" for h in range(1,13)] + [f"{h}:00 PM" for h in range(1,13)] + ["OFF"])
    column_config[f"{day}: Finish"] = st.column_config.SelectboxColumn("Finish", options=[f"{h}:00 AM" for h in range(1,13)] + [f"{h}:00 PM" for h in range(1,13)] + ["OFF"])

edited_df = st.data_editor(st.session_state.df_schedule, column_config=column_config, num_rows="dynamic", use_container_width=True)

# ---------------- SAVE ----------------
if st.button("💾 Save to Master Sheet", type="primary"):
    # Apply Auto-Formatting
    df_to_save = edited_df.copy()
    df_to_save["Name"] = df_to_save["Name"].astype(str).str.upper()
    df_to_save["Branch"] = st.session_state.selected_branch
    df_to_save["Date"] = str(start_date)
    
    with st.spinner("Syncing to Master Sheet..."):
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            ws.clear()
            ws.update([HEADERS] + df_to_save.fillna("").values.tolist())
            st.success("✅ Data saved to Master Sheet!")
            st.session_state.df_schedule = df_to_save
        except Exception as e:
            st.error(f"Error: {e}")

if st.button("⬅ Back"): st.switch_page("app.py")
