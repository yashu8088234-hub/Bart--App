import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- PAGE SETUP ----------------
st.set_page_config(layout="wide", page_title="BART Staff Schedule")

# Authentication Check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

# ---------------- GOOGLE SHEETS SETUP ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.session_state.branch_info["SheetID"])

# ---------------- CONFIGURATION & HEADERS ----------------
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
ROLE_OPTIONS = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]

# Generate time slots 1-12 AM/PM
times = []
for h in range(1, 13):
    times.append(f"{h}:00 AM")
    times.append(f"{h}:00 PM")
times.append("OFF")

HEADERS = ["Name", "Role"]
for day in DAYS:
    HEADERS.append(f"{day}: Start")
    HEADERS.append(f"{day}: Finish")

# ---------------- DATA HANDLING ----------------
def get_or_create_sheet():
    try:
        ws = sheet.worksheet("StaffSchedule")
        data = ws.get_all_values()
        if len(data) < 1:
            ws.append_row(HEADERS)
            return pd.DataFrame(columns=HEADERS)
        # Convert list to DataFrame
        return pd.DataFrame(data[1:], columns=data[0])
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title="StaffSchedule", rows="100", cols=len(HEADERS))
        ws.append_row(HEADERS)
        return pd.DataFrame(columns=HEADERS)

if "df_schedule" not in st.session_state:
    st.session_state.df_schedule = get_or_create_sheet()

# ---------------- UI LAYOUT ----------------
st.title(f"🏢 Weekly Schedule: {st.session_state.selected_branch}")

# Date Selectors
col1, col2 = st.columns(2)
start_date = col1.date_input("Schedule Start Date")
end_date = col2.date_input("Schedule End Date")

st.markdown("---")
st.subheader("Edit Staff Roster")
st.markdown("Use the dropdowns to select shifts and roles. Names are converted to UPPERCASE upon saving.")

# Build Data Editor Configuration
column_config = {
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS, required=True),
}
for day in DAYS:
    column_config[f"{day}: Start"] = st.column_config.SelectboxColumn("Start", options=times)
    column_config[f"{day}: Finish"] = st.column_config.SelectboxColumn("Finish", options=times)

# Display Editor
edited_df = st.data_editor(
    st.session_state.df_schedule,
    column_config=column_config,
    num_rows="dynamic",
    use_container_width=True,
    key="main_editor"
)

# ---------------- SAVE OPERATIONS ----------------
if st.button("💾 Save Schedule to Database", type="primary"):
    # Enforce Uppercase on Names
    if "Name" in edited_df.columns:
        edited_df["Name"] = edited_df["Name"].astype(str).str.upper()
    
    with st.spinner("Updating Google Sheet..."):
        try:
            ws = sheet.worksheet("StaffSchedule")
            ws.clear()
            # Combine headers and data for writing
            data_to_write = [HEADERS] + edited_df.fillna("").values.tolist()
            ws.update(data_to_write)
            
            st.success("✅ Schedule saved successfully! Names updated to Uppercase.")
            st.session_state.df_schedule = edited_df
        except Exception as e:
            st.error(f"❌ Error saving data: {e}")

st.markdown("---")
if st.button("⬅ Back to Dashboard"):
    st.switch_page("app.py")
