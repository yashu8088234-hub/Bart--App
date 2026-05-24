import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import timedelta

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# 1. AUTH & CONNECTION
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
master_sheet = gspread.authorize(creds).open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0")

# 2. CONFIG
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
ROLE_OPTIONS = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]
SHIFT_OPTIONS = ["Morning shift", "Mid shift", "Evening shift", "Night shift"]
TIME_OPTIONS = [f"{h}:00 AM" for h in range(1, 13)] + [f"{h}:00 PM" for h in range(1, 13)] + ["OFF"]

# 3. UI: TOGGLE & DATE
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")
start_date = st.date_input("Week Start Date")
shift_mode = st.toggle("Enable Shift-wise Mode")

# Calculate dynamic headers with dates
day_dates = [(start_date + timedelta(days=i)).strftime("%a %d/%m") for i in range(7)]

# 4. LOAD & FILTER DATA
def get_filtered_data():
    ws = master_sheet.worksheet("StaffSchedule")
    all_data = ws.get_all_records()
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)
    # Filter for current branch only
    return df[df['Branch'] == st.session_state.selected_branch]

df = get_filtered_data()

# 5. DATA EDITOR (Multi-Index Simulation)
st.subheader("Edit Roster")
config = {"Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS)}

# Configure Columns dynamically
for i, day in enumerate(DAYS):
    if shift_mode:
        # ONLY ONE CELL PER DAY
        config[day] = st.column_config.SelectboxColumn(
            f"{day}\n({day_dates[i]})",
            options=SHIFT_OPTIONS
        )
    else:
        # TIME MODE (Start + End)
        config[f"{day}: Start"] = st.column_config.SelectboxColumn(
            f"{day}\nStart",
            options=TIME_OPTIONS
        )
        config[f"{day}: Finish"] = st.column_config.SelectboxColumn(
            f"{day}\nEnd",
            options=TIME_OPTIONS
        )
edited_df = st.data_editor(df, column_config=config, num_rows="dynamic", use_container_width=True)

# 6. SAVE LOGIC (Safe Update)
if st.button("💾 Save to Master Sheet", type="primary"):
    ws = master_sheet.worksheet("StaffSchedule")
    full_data = pd.DataFrame(ws.get_all_records())
    
    # Clean current branch data out of master
    remaining_data = full_data[full_data['Branch'] != st.session_state.selected_branch]
    
    # Process updated data
    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = str(start_date)
    new_data["Name"] = new_data["Name"].astype(str).str.upper()
    
    # Merge and Write
    final_df = pd.concat([remaining_data, new_data], ignore_index=True)
    ws.clear()
    ws.update([final_df.columns.values.tolist()] + final_df.fillna("").values.tolist())
    st.success("✅ Saved Successfully!")
    st.rerun()

if st.button("⬅ Back"): st.switch_page("app.py")
