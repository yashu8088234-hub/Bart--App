import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide", page_title="BART Staff Schedule")

# Authentication Check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

# Load Google Sheets
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.session_state.branch_info["SheetID"])

# ---------------- DATA HANDLING ----------------
def get_schedule():
    try:
        ws = sheet.worksheet("StaffSchedule")
    except gspread.exceptions.WorksheetNotFound:
        # Create tab if missing
        ws = sheet.add_worksheet(title="StaffSchedule", rows="100", cols="9")
        headers = ["Name", "Role", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        ws.append_row(headers)
    
    data = ws.get_all_records()
    return pd.DataFrame(data)

if "df_schedule" not in st.session_state:
    st.session_state.df_schedule = get_schedule()

# ---------------- UI ----------------
st.title(f"📅 Staff Schedule: {st.session_state.selected_branch}")

# Filters
col1, col2 = st.columns(2)
start_date = col1.date_input("Schedule Start Date")
end_date = col2.date_input("Schedule End Date")

# Roles and Shifts for Dropdowns
roles = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]
shifts = ["Morning", "Mid Shift", "Evening", "Night"]

st.subheader("Weekly Roster Editor")
st.markdown("Use the **+** button to add staff and select roles/shifts from the dropdown menus.")

# ---------------- SPREADSHEET EDITOR ----------------
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
    use_container_width=True,
    key="schedule_editor"
)

# ---------------- SAVE BUTTON ----------------
if st.button("💾 Save Changes to Sheets"):
    try:
        ws = sheet.worksheet("StaffSchedule")
        ws.clear()
        # Save headers + data
        updated_data = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
        ws.update(updated_data)
        st.success("Schedule saved successfully!")
        st.session_state.df_schedule = edited_df
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")

if st.button("⬅ Back"):
    st.switch_page("app.py")
