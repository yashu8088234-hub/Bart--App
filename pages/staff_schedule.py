import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- PAGE SETUP ----------------
st.set_page_config(layout="wide", page_title="BART Master Schedule")

# Authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login from the main portal first.")
    if st.button("Go to Login"): st.switch_page("app.py")
    st.stop()

# Credentials & Master Sheet
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
MASTER_SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
master_sheet = client.open_by_key(MASTER_SHEET_ID)

# ---------------- CONFIG ----------------
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
ROLE_OPTIONS = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]
TIMES = [f"{h}:00 AM" for h in range(1, 13)] + [f"{h}:00 PM" for h in range(1, 13)] + ["OFF"]

# Exact Headers
HEADERS = ["Branch", "Date", "Name", "Role"]
for day in DAYS:
    HEADERS.append(f"{day}: Start")
    HEADERS.append(f"{day}: Finish")

# ---------------- DATA HANDLING ----------------
def get_or_create_sheet():
    try:
        ws = master_sheet.worksheet("StaffSchedule")
        data = ws.get_all_values()
        if len(data) < 1:
            ws.append_row(HEADERS)
            return pd.DataFrame(columns=HEADERS)
        return pd.DataFrame(data[1:], columns=data[0])
    except gspread.exceptions.WorksheetNotFound:
        ws = master_sheet.add_worksheet(title="StaffSchedule", rows="100", cols=len(HEADERS))
        ws.append_row(HEADERS)
        return pd.DataFrame(columns=HEADERS)

if "df_schedule" not in st.session_state:
    st.session_state.df_schedule = get_or_create_sheet()

# ---------------- UI ----------------
st.title(f"🏢 Master Schedule: {st.session_state.selected_branch}")

col1, col2 = st.columns(2)
start_date = col1.date_input("Week Start Date")
end_date = col2.date_input("Week End Date")

# Configure Dropdowns
column_config = {
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS, required=True),
}
for day in DAYS:
    column_config[f"{day}: Start"] = st.column_config.SelectboxColumn("Start", options=TIMES)
    column_config[f"{day}: Finish"] = st.column_config.SelectboxColumn("Finish", options=TIMES)

edited_df = st.data_editor(
    st.session_state.df_schedule, 
    column_config=column_config, 
    num_rows="dynamic", 
    use_container_width=True
)

# ---------------- SAVE ----------------
if st.button("💾 Save to Master Sheet", type="primary"):
    df_to_save = edited_df.copy()
    
    # Auto-fill metadata
    df_to_save["Branch"] = st.session_state.selected_branch
    df_to_save["Date"] = str(start_date)
    
    # Uppercase Name
    df_to_save["Name"] = df_to_save["Name"].astype(str).str.upper()
    
    # Re-order to match exact headers
    df_to_save = df_to_save.reindex(columns=HEADERS)
    
    with st.spinner("Syncing to Master Sheet..."):
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            ws.clear()
            # Update A1 with list of list
            all_data = [HEADERS] + df_to_save.fillna("").values.tolist()
            ws.update(range_name='A1', values=all_data)
            
            st.success("✅ Data saved perfectly to Master Sheet!")
            st.session_state.df_schedule = df_to_save
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

if st.button("⬅ Back"): st.switch_page("app.py")
