import streamlit as st
import pandas as pd
import gspread
import time
import re
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from st_aggrid import AgGrid

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# =========================
# AUTH CHECK
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠ Session expired. Please login again.")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("⬅ Back to Staff Login", use_container_width=True):
            st.switch_page("pages/staff_dashboard.py")
    st.stop()

# =========================
# GOOGLE CLIENT
# =========================
if "gspread_client" not in st.session_state:
    try:
        creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        st.session_state.gspread_client = gspread.authorize(creds)
    except Exception as e:
        st.error(f"Authentication setup error: {e}")
        st.stop()

master_sheet = st.session_state.gspread_client.open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0")

# =========================
# CONFIG
# =========================
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SHIFT_OPTIONS = ["➕ Custom Time", "📴 Day Off"]
ROLE_OPTIONS = ["Team-Member", "Acting_Team_Leader", "Team_Leader", "Acting_Supervisor", "Supervisor", "Branch_Manager"]

# =========================
# DIALOGS
# =========================
@st.dialog("✅ Submission Successful")
def success_dialog():
    st.success("Your schedule has been successfully submitted to the Master Schedule.")
    if st.button("Close", use_container_width=True):
        st.rerun()

@st.dialog("⏰ Set Custom Time")
def custom_time_dialog(row_idx, row_name, day_name):
    st.write(f"Configure shift for **{row_name}** on **{day_name}**")
    col1, col2 = st.columns(2)
    with col1:
        sh = st.selectbox("Start Hour", list(range(1, 13)), index=8)
        sap = st.selectbox("AM/PM", ["AM", "PM"], key=f"sap_{row_idx}_{day_name}")
    with col2:
        eh = st.selectbox("End Hour", list(range(1, 13)), index=5)
        eap = st.selectbox("AM/PM", ["AM", "PM"], key=f"eap_{row_idx}_{day_name}", index=1)
    apply_all = st.checkbox("Apply to all working days this week")
    if st.button("Apply Shift", use_container_width=True):
        value, hrs = format_shift(f"{sh} {sap}", f"{eh} {eap}")
        if value is None:
            st.error("❌ Minimum 9 hours required")
        else:
            if apply_all:
                for day in DAYS:
                    st.session_state.shift_buffer[f"{row_idx}_{day}"] = value
            else:
                st.session_state.shift_buffer[f"{row_idx}_{day_name}"] = value
            st.rerun()

@st.dialog("🚫 Submission Blocked")
def duplicate_submission_dialog():
    st.error("This week's schedule has already been submitted for this branch.")
    if st.button("Close", use_container_width=True):
        st.rerun()

# =========================
# FUNCTIONS
# =========================
def parse_hour(val):
    hour, ap = val.split()
    hour = int(hour)
    if ap == "PM" and hour != 12: hour += 12
    if ap == "AM" and hour == 12: hour = 0
    return hour

def calculate_hours(start, end):
    s = parse_hour(start)
    e = parse_hour(end)
    if e <= s: e += 24
    return e - s

def format_shift(start, end):
    hrs = calculate_hours(start, end)
    if hrs < 9: return None, hrs
    ot = max(0, hrs - 9)
    if ot > 0: return (f"{start} - {end} (OT {ot}h)", hrs)
    return (f"{start} - {end}", hrs)

def calculate_row_ot(row):
    total_ot = 0
    for col in row.index:
        val = str(row.get(col, ""))
        match = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if match: total_ot += float(match.group(1))
    return f"{total_ot} hrs" if total_ot > 0 else "0 hrs"

def load_data(force_reload=False):
    if force_reload or st.session_state.get("cached_df") is None:
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            data = ws.get_all_records()
            df = pd.DataFrame(data) if data else pd.DataFrame()
            if not df.empty:
                df["Over-Time"] = df.apply(calculate_row_ot, axis=1)
            else:
                df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS + ["Over-Time"])
            st.session_state.cached_df = df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.session_state.cached_df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS + ["Over-Time"])
    return st.session_state.cached_df

# =========================
# MAIN APP FLOW
# =========================
if "shift_buffer" not in st.session_state: st.session_state.shift_buffer = {}
if "previous_week" not in st.session_state: st.session_state.previous_week = None
if "deleted_staff" not in st.session_state: st.session_state.deleted_staff = set()

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")
selected_date = st.date_input("📅 Select Date", value=datetime.today())
week_start = selected_date - timedelta(days=(selected_date.weekday() + 1) % 7)
week_start_str = week_start.strftime('%d %b %Y')
st.caption(f"Week starting: {week_start_str}")

# Map standard Day names to specific dated headers
day_labels = {d: f"{d} ({(week_start + timedelta(days=i)).strftime('%d %b')})" for i, d in enumerate(DAYS)}

if st.session_state.previous_week != week_start_str:
    st.session_state.shift_buffer = {}
    st.session_state.deleted_staff = set()
    st.session_state.previous_week = week_start_str

edit_mode = st.toggle("Edit Mode Only")
all_data_df = load_data()
df = all_data_df[all_data_df["Branch"] == st.session_state.selected_branch].copy() if not all_data_df.empty else pd.DataFrame(columns=["Branch", "Name", "Role"] + list(day_labels.values()))

# =========================
# EDIT MODE
# =========================
if edit_mode:
    df_display = df[["Name", "Role"] + list(day_labels.values())].reset_index(drop=True) if not df.empty else pd.DataFrame(columns=["Name", "Role"] + list(day_labels.values()))
    
    config = {
        "Name": st.column_config.SelectboxColumn("Name", options=df["Name"].unique().tolist() if not df.empty else [], width=90),
        "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS, width=90)
    }
    for d in DAYS:
        config[day_labels[d]] = st.column_config.SelectboxColumn(label=day_labels[d], options=SHIFT_OPTIONS, width=100)

    edited_df = st.data_editor(df_display, column_config=config, num_rows="dynamic", use_container_width=True)

    if st.button("✅ Submit"):
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            all_current = pd.DataFrame(ws.get_all_records())
            others = all_current[all_current["Branch"] != st.session_state.selected_branch].copy()
            
            new_data = edited_df.copy()
            new_data["Branch"] = st.session_state.selected_branch
            new_data["Over-Time"] = new_data.apply(calculate_row_ot, axis=1)
            
            final = pd.concat([others, new_data], ignore_index=True).fillna("")
            
            # Update Sheet
            ws.update(range_name='A1', values=[final.columns.tolist()] + final.values.tolist())
            success_dialog()
        except Exception as e:
            st.error(f"❌ Submission Failed: {e}")
else:
    st.dataframe(df)
