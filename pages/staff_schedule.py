import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- PAGE SETUP ----------------
st.set_page_config(layout="wide", page_title="BART Advanced Roster")

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login from the main portal first.")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.session_state.branch_info["SheetID"])

# ---------------- CONFIGURATION ----------------
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
ROLE_OPTIONS = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]

# Create Time Dropdown Options (1-12, AM/PM)
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
        return pd.DataFrame(data[1:], columns=data[0])
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title="StaffSchedule", rows="100", cols=len(HEADERS))
        ws.append_row(HEADERS)
        return pd.DataFrame(columns=HEADERS)

if "df_schedule" not in st.session_state:
    st.session_state.df_schedule = get_or_create_sheet()

# ---------------- UI ----------------
st.title(f"🏢 Weekly Schedule: {st.session_state.selected_branch}")

# Column config dictionary for the Data Editor
column_config = {
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS, required=True),
}
# Add time dropdowns to all 14 time columns
for day in DAYS:
    column_config[f"{day}: Start"] = st.column_config.SelectboxColumn("Start", options=times)
    column_config[f"{day}: Finish"] = st.column_config.SelectboxColumn("Finish", options=times)

edited_df = st.data_editor(
    st.session_state.df_schedule,
    column_config=column_config,
    num_rows="dynamic",
    use_container_width=True
)

# ---------------- SAVE OPERATIONS ----------------
if st.button("💾 Save Schedule", type="primary"):
    # Name Uppercase Conversion Logic
    if "Name" in edited_df.columns:
        edited_df["Name"] = edited_df["Name"].astype(str).str.upper()
    
    with st.spinner("Saving..."):
        try:
            ws = sheet.worksheet("StaffSchedule")
            ws.clear()
            data_to_write = [HEADERS] + edited_df.fillna("").values.tolist()
            ws.update(data_to_write)
            st.success("✅ Saved and Names converted to Uppercase!")
            st.session_state.df_schedule = edited_df
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")

if st.button("⬅ Back"):
    st.switch_page("app.py")
