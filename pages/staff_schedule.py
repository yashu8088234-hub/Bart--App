import streamlit as st
import pandas as pd
import gspread
import time
import re
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from st_aggrid import AgGrid

# 1. SETUP PAGE SETTINGS
st.set_page_config(layout="wide", page_title="BART Master Schedule")

# 2. CHECK IF USER IS LOGGED IN
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    st.stop()

# 3. CONNECT TO GOOGLE SHEETS
if "gspread_client" not in st.session_state:
    creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    st.session_state.gspread_client = gspread.authorize(creds)

master_sheet = st.session_state.gspread_client.open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0")

# 4. CONFIGURATION OPTIONS
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SHIFT_OPTIONS = ["➕ Custom Time", "📴 Day Off"]
ROLE_OPTIONS = ["Team-Member", "Acting_Team_Leader", "Team_Leader", "Acting_Supervisor", "Supervisor", "Branch_Manager"]

# 5. DATA LOADING FUNCTION (ONLY RUNS WHEN CALLED)
def load_data(force_reload=False):
    # This keeps data in memory until the "Refresh" button is clicked
    if force_reload or st.session_state.get("cached_df") is None:
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            data = ws.get_all_records()
            df = pd.DataFrame(data) if data else pd.DataFrame()
            if not df.empty:
                # Rename columns from "Sunday (24 May)" to just "Sunday"
                new_cols = {col: day for col in df.columns for day in DAYS if day in col}
                df = df.rename(columns=new_cols)
            st.session_state.cached_df = df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.session_state.cached_df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS + ["Over-Time"])
    return st.session_state.cached_df

# 6. HELPER FUNCTIONS FOR CALCULATING TIME
def parse_hour(val):
    hour, ap = val.split()
    hour = int(hour)
    if ap == "PM" and hour != 12: hour += 12
    if ap == "AM" and hour == 12: hour = 0
    return hour

def format_shift(start, end):
    hrs = parse_hour(end) - parse_hour(start)
    if hrs < 0: hrs += 24
    if hrs < 9: return None, hrs
    ot = max(0, hrs - 9)
    return (f"{start} - {end} (OT {ot}h)", hrs) if ot > 0 else (f"{start} - {end}", hrs)

def calculate_row_ot(row):
    total = sum([float(re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", str(row.get(d, ""))).group(1)) 
                 for d in DAYS if re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", str(row.get(d, "")))])
    return f"{total} hrs" if total > 0 else "0 hrs"

# 7. POP-UP MODAL FOR CUSTOM SHIFTS
@st.dialog("⏰ Set Custom Time")
def custom_time_dialog(row_idx, row_name, day_name):
    st.write(f"Configure shift for **{row_name}** on **{day_name}**")
    c1, c2 = st.columns(2)
    with c1: 
        sh = st.selectbox("Start", list(range(1, 13)), index=8)
        sap = st.selectbox("AM/PM", ["AM", "PM"], key="s")
    with c2: 
        eh = st.selectbox("End", list(range(1, 13)), index=5)
        eap = st.selectbox("AM/PM", ["AM", "PM"], index=1, key="e")
    
    if st.button("Apply"):
        st.session_state.shift_buffer[f"{row_idx}_{day_name}"] = f"{sh} {sap} - {eh} {eap}"
        st.rerun()

# 8. MAIN UI LAYOUT
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")
sel_date = st.date_input("📅 Select Date", value=datetime.today())
week_start = sel_date - timedelta(days=(sel_date.weekday() + 1) % 7)
day_labels = {d: f"{d} ({(week_start + timedelta(days=i)).strftime('%d %b')})" for i, d in enumerate(DAYS)}

edit_mode = st.toggle("Edit Mode Only")
df = load_data()
df = df[df["Branch"] == st.session_state.selected_branch].copy()

# 9. EDIT MODE LOGIC
if edit_mode:
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    # Check for custom time triggers
    for i, row in edited_df.iterrows():
        for d in DAYS:
            if row.get(d) == "➕ Custom Time": custom_time_dialog(i, row['Name'], d)

    if st.button("🚀 Submit to Master Sheet"):
        ws = master_sheet.worksheet("StaffSchedule")
        others = st.session_state.cached_df[st.session_state.cached_df["Branch"] != st.session_state.selected_branch]
        final = pd.concat([others, edited_df], ignore_index=True)
        ws.update([final.columns.tolist()] + final.fillna("").values.tolist())
        
        # FULL SCREEN SUCCESS OVERLAY
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("""<div style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:9999; display:flex; justify-content:center; align-items:center; color:white;">
                <h1>✅ Submitted Successfully!</h1></div>""", unsafe_allow_html=True)
            time.sleep(2)
        placeholder.empty()
        st.session_state.cached_df = final
        st.rerun()

# 10. VIEW MODE LOGIC
else:
    if st.button("🔄 Refresh Data"):
        load_data(force_reload=True)
        st.rerun()
    AgGrid(df, use_container_width=True)

if st.button("⬅ Back"): st.switch_page("app.py")
