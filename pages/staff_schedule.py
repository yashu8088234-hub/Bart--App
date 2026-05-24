import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- PAGE SETUP ----------------
st.set_page_config(layout="wide", page_title="BART Advanced Roster")

# ---------------- AUTH & CONNECTION ----------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

# Use the branch-specific sheet defined in your main portal
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Connect to the branch sheet
sheet = client.open_by_key(st.session_state.branch_info["SheetID"])

# ---------------- CONFIGURATION: HEADERS ----------------
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HEADERS = ["Name", "Role"]
for day in DAYS:
    HEADERS.append(f"{day} Start")
    HEADERS.append(f"{day} Finish")

ROLE_OPTIONS = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]

# ---------------- DATA INITIALIZATION ----------------
def get_or_create_sheet():
    try:
        ws = sheet.worksheet("StaffSchedule")
        data = ws.get_all_values()
        if len(data) < 1: # Empty
            ws.append_row(HEADERS)
            return pd.DataFrame(columns=HEADERS)
        else:
            return pd.DataFrame(data[1:], columns=data[0])
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title="StaffSchedule", rows="100", cols=len(HEADERS))
        ws.append_row(HEADERS)
        return pd.DataFrame(columns=HEADERS)

if "df_schedule" not in st.session_state:
    st.session_state.df_schedule = get_or_create_sheet()

# ---------------- UI LAYOUT ----------------
st.title(f"🏢 Weekly Schedule: {st.session_state.selected_branch}")
st.markdown("---")

# Date Selection
col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date of Week")
end_date = col2.date_input("End Date of Week")

st.markdown("### 📋 Staff Roster Management")
st.info("Use the 'Add row' button to create new entries. Select 'Role' from the dropdown. Fill in Start/Finish times manually.")

# Data Editor
edited_df = st.data_editor(
    st.session_state.df_schedule,
    column_config={
        "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS, required=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

# ---------------- SAVE OPERATIONS ----------------
if st.button("💾 Save Schedule to Database", type="primary"):
    with st.spinner("Saving data..."):
        try:
            ws = sheet.worksheet("StaffSchedule")
            ws.clear()
            # Prepare data: Headers + Values
            data_to_write = [HEADERS] + edited_df.fillna("").values.tolist()
            ws.update(data_to_write)
            st.success("✅ Schedule saved successfully!")
            st.session_state.df_schedule = edited_df
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

st.markdown("---")
if st.button("⬅ Back to Dashboard"):
    st.switch_page("app.py")
