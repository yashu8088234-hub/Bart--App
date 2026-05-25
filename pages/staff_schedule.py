import streamlit as st
import pandas as pd
import gspread
import time
import re

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from st_aggrid import AgGrid

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# =========================
# AUTH CHECK
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    st.stop()

# Initialize Google Credentials once
if "gspread_client" not in st.session_state:
    creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    st.session_state.gspread_client = gspread.authorize(creds)

master_sheet = st.session_state.gspread_client.open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0")

# =========================
# CONFIG
# =========================
DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

SHIFT_OPTIONS = [
    "➕ Custom Time",
    "📴 Day Off"
]

ROLE_OPTIONS = [
    "Team-Member","Acting_Team_Leader","Team_Leader",
    "Acting_Supervisor","Supervisor","Branch_Manager"
]

CACHE_TTL = 60 

# =========================
# SESSION STATE INITIALIZATION
# =========================
if "cached_df" not in st.session_state:
    st.session_state.cached_df = None
    st.session_state.last_fetch = 0

if "shift_buffer" not in st.session_state:
    st.session_state.shift_buffer = {}

if "previous_week" not in st.session_state:
    st.session_state.previous_week = None

if "deleted_staff" not in st.session_state:
    st.session_state.deleted_staff = set()

# =========================
# DATA LOAD (API PROTECTION LAYER)
# =========================
def load_data():
    now = time.time()
    if st.session_state.cached_df is None or (now - st.session_state.last_fetch > CACHE_TTL):
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            data = ws.get_all_records()
            df = pd.DataFrame(data) if data else pd.DataFrame()

            if df.empty:
                df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS)

            st.session_state.cached_df = df
            st.session_state.last_fetch = now
        except Exception as e:
            st.error(f"API Fetch Rate-Limit Warning. Using local cache fallback.")
            if st.session_state.cached_df is None:
                st.session_state.cached_df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS)

    return st.session_state.cached_df


# =========================
# TIME LOGIC
# =========================
def parse_hour(val):
    hour, ap = val.split()
    hour = int(hour)
    if ap == "PM" and hour != 12:
        hour += 12
    if ap == "AM" and hour == 12:
        hour = 0
    return hour


def calculate_hours(start, end):
    s = parse_hour(start)
    e = parse_hour(end)
    if e <= s:
        e += 24
    return e - s


def format_shift(start, end):
    hrs = calculate_hours(start, end)
    if hrs < 9:
        return None, hrs
    ot = max(0, hrs - 9)
    if ot > 0:
        return f"{start} - {end} (OT {ot}h)", hrs
    return f"{start} - {end}", hrs


def calculate_row_ot(row):
    total_ot = 0
    for day in DAYS:
        val = str(row.get(day, ""))
        match = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if match:
            total_ot += float(match.group(1))
    return f"{total_ot} hrs" if total_ot > 0 else "0 hrs"


# =========================
# MODAL DIALOG FOR CUSTOM TIME
# =========================
@st.dialog("⏰ Set Custom Time")
def custom_time_dialog(row_idx, row_name, day_name):
    st.write(f"Configure shift for **{row_name}** on **{day_name}**")
    
    col1, col2 = st.columns(2)
    with col1:
        sh = st.selectbox("Start Hour", list(range(1, 13)), index=8)
        sap = st.selectbox("AM/PM", ["AM", "PM"], key="sap_modal")
    with col2:
        eh = st.selectbox("End Hour", list(range(1, 13)), index=5)
        eap = st.selectbox("AM/PM", ["AM", "PM"], key="eap_modal", index=1)

    apply_all = st.checkbox("Apply to all working days this week")

    if st.button("Apply Shift", use_container_width=True):
        start = f"{sh} {sap}"
        end = f"{eh} {eap}"
        value, hrs = format_shift(start, end)

        if value is None:
            st.error("❌ Minimum 9 hours required")
        else:
            if apply_all:
                for day in DAYS:
                    st.session_state.shift_buffer[f"{row_idx}_{day}"] = value
            else:
                st.session_state.shift_buffer[f"{row_idx}_{day_name}"] = value
            
            st.rerun()


# =========================
# UI HEADER
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

selected_date = st.date_input("📅 Select Any Date In Week", value=datetime.today())

days_from_sunday = (selected_date.weekday() + 1) % 7
week_start = selected_date - timedelta(days=days_from_sunday)
week_start_str = week_start.strftime('%d %b %Y')

st.caption(f"Week: {week_start_str}")

if st.session_state.previous_week != week_start_str:
    st.session_state.shift_buffer = {}
    st.session_state.deleted_staff = set()
    st.session_state.previous_week = week_start_str

edit_mode = st.toggle("Edit Mode Only")

# =========================
# LOAD DATA FROM CACHE ONLY
# =========================
all_data_df = load_data()

df = all_data_df[all_data_df["Branch"] == st.session_state.selected_branch].copy() \
    if not all_data_df.empty else pd.DataFrame(columns=["Branch","Name","Role"] + DAYS)


# =========================
# WEEK LABELS
# =========================
day_labels = {}
for idx, day_name in enumerate(DAYS):
    day_date = week_start + timedelta(days=idx)
    day_labels[day_name] = f"{day_name} ({day_date.strftime('%d %b')})"

# =========================
# PREP DISPLAY
# =========================
if edit_mode:
    if not df.empty:
        df_display = df[["Name", "Role"]].dropna(subset=["Name"]).drop_duplicates().reset_index(drop=True)
        
        if st.session_state.deleted_staff:
            df_display = df_display[~df_display["Name"].isin(st.session_state.deleted_staff)].reset_index(drop=True)
            
        for d in DAYS:
            df_display[d] = ""
    else:
        df_display = pd.DataFrame(columns=["Name", "Role"] + DAYS)

    # APPLY ACTIVE INPUT BUFFERS
    for i, row in df_display.iterrows():
        for d in DAYS:
            key = f"{i}_{d}"
            if key in st.session_state.shift_buffer:
                df_display.loc[i, d] = st.session_state.shift_buffer[key]

    # Calculate real-time OT
    df_display["Over-Time"] = df_display.apply(calculate_row_ot, axis=1)

    # =========================
    # EDIT MODE WIDTH CONFIG (NAME COMPACTED)
    # =========================
    config = {
        "Name": st.column_config.SelectboxColumn(
            "Name", 
            options=df["Name"].dropna().unique().tolist() if not df.empty else [],
            width=120,  # Made extra compact to save maximum screen space
            required=True
        ),
        "Role": st.column_config.SelectboxColumn(
            "Role", 
            options=ROLE_OPTIONS,
            width=140
        ),
        "Over-Time": st.column_config.TextColumn(
            "Over-Time", 
            disabled=True,
            width=90
        )
    }

    for d in DAYS:
        existing_shifts = df_display[d].dropna().unique().tolist()
        dynamic_options = list(set(SHIFT_OPTIONS + existing_shifts))
        config[d] = st.column_config.SelectboxColumn(
            label=day_labels[d], 
            options=dynamic_options,
            width=135
        )

    col_order = ["Name", "Role"] + DAYS + ["Over-Time"]
    
    edited_df = st.data_editor(
        df_display[col_order], 
        column_config=config, 
        num_rows="dynamic", 
        use_container_width=True,
        key="editor"
    )

    # TRACK IN-SESSION DELETIONS FROM DATA EDITOR
    current_editor_names = set(edited_df["Name"].dropna().tolist())
    for original_name in df_display["Name"].tolist():
        if original_name not in current_editor_names:
            st.session_state.deleted_staff.add(original_name)

    # =========================
    # INTERCEPT SELECTBOX ACTIONS
    # =========================
    for i, row in edited_df.iterrows():
        for d in DAYS:
            if row.get(d) == "📴 Day Off":
                st.session_state.shift_buffer[f"{i}_{d}"] = "OFF"
                st.rerun()
                
            if row.get(d) == "➕ Custom Time":
                custom_time_dialog(row_idx=i, row_name=row['Name'], day_name=d)

# =========================
# VIEW MODE
# =========================
else:
    df_display = df.copy()
    if st.session_state.deleted_staff and not df_display.empty:
        df_display = df_display[~df_display["Name"].isin(st.session_state.deleted_staff)].reset_index(drop=True)

    if not df_display.empty:
        df_display["Over-Time"] = df_display.apply(calculate_row_ot, axis=1)
    else:
        df_display["Over-Time"] = []

    # VIEW MODE WIDTH CONFIG (NAME COMPACTED)
    column_defs = [
        {"headerName":"Name","field":"Name","pinned":"left", "width": 90}, # Matches editor compact view
        {"headerName":"Role","field":"Role", "width": 140}
    ]
    for d in DAYS:
        column_defs.append({"headerName":day_labels[d],"field":d, "width": 135})
    column_defs.append({"headerName":"Over-Time","field":"Over-Time", "width": 90})

    AgGrid(df_display, gridOptions={
        "columnDefs": column_defs,
        "defaultColDef": {"resizable": True}
    }, height=500)

# =========================
# SAVE (COMMIT TO CLOUD)
# =========================
if edit_mode and st.button("💾 Save to Master Sheet"):
    ws = master_sheet.worksheet("StaffSchedule")
    full_df = st.session_state.cached_df.copy()

    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    
    if "Over-Time" in new_data.columns:
        new_data = new_data.drop(columns=["Over-Time"])

    others = full_df[full_df["Branch"] != st.session_state.selected_branch].copy()

    final = pd.concat([others, new_data], ignore_index=True)
    storage_cols = ["Branch", "Name", "Role"] + DAYS
    final = final[storage_cols]

    ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

    st.session_state.cached_df = final 
    st.session_state.last_fetch = time.time()
    st.session_state.shift_buffer = {}
    st.session_state.deleted_staff = set() 

    st.success("✅ Saved successfully! Row updates synchronized.")
    st.rerun()

# =========================
# BACK
# =========================
if st.button("⬅ Back"):
    st.switch_page("app.py")
