import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="Staff Schedule")

# ---------------- AUTH & SETUP ----------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open the branch-specific sheet
sheet = client.open_by_key(st.session_state.branch_info["SheetID"])

# ---------------- DATA HANDLING ----------------
def get_schedule():
    try:
        ws = sheet.worksheet("StaffSchedule")
    except gspread.exceptions.WorksheetNotFound:
        # Auto-create if missing
        ws = sheet.add_worksheet(title="StaffSchedule", rows="100", cols="9")
        headers = ["Name", "Role", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        ws.append_row(headers)
    
    data = ws.get_all_records()
    return pd.DataFrame(data)

# Load data into session state
if "df_schedule" not in st.session_state:
    st.session_state.df_schedule = get_schedule()

# ---------------- UI ----------------
st.title(f"Staff Schedule: {st.session_state.selected_branch}")

roles = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]
shifts = ["Morning", "Mid Shift", "Evening", "Night"]

# Date Selection
col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date")
end_date = col2.date_input("End Date")

st.subheader("Weekly Roster")

# Data Editor
edited_df = st.data_editor(
    st.session_state.df_schedule,
    column_config={
        "Role": st.column_config.SelectboxColumn("Role", options=roles, required=True),
        "Sunday": st.column_config.SelectboxColumn("Sunday", options=shifts),
        "Monday": st.column_config.SelectboxColumn("Monday", options=shifts),
        "Tuesday": st.column_config.SelectboxColumn("Tuesday", options=shifts),
        "Wednesday": st.column_config.SelectboxColumn("Wednesday", options=shifts),
        "Thursday": st.column_config.SelectboxColumn("Thursday", options=shifts),
        "Friday": st.column_config.SelectboxColumn("Friday", options=shifts),
        "Saturday": st.column_config.SelectboxColumn("Saturday", options=shifts),
    },
    num_rows="dynamic",
    use_container_width=True
)

# ---------------- SAVE ----------------
if st.button("💾 Save Schedule"):
    try:
        ws = sheet.worksheet("StaffSchedule")
        ws.clear()
        # Update with headers + data
        ws.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())
        st.success("Schedule saved successfully!")
        # Update session state to avoid stale data
        st.session_state.df_schedule = edited_df
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")

if st.button("⬅ Back"):
    st.switch_page("app.py")
