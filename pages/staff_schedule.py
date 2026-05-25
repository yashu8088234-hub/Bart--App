import streamlit as st
import pandas as pd
import gspread
import time

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

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
)

client = gspread.authorize(creds)
master_sheet = client.open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0")

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
# SESSION STATE
# =========================
if "cached_df" not in st.session_state:
    st.session_state.cached_df = None
    st.session_state.last_fetch = 0

if "shift_buffer" not in st.session_state:
    st.session_state.shift_buffer = {}

# =========================
# DATA LOAD
# =========================
def load_data():
    now = time.time()

    if st.session_state.cached_df is None or now - st.session_state.last_fetch > CACHE_TTL:
        ws = master_sheet.worksheet("StaffSchedule")
        data = ws.get_all_records()
        df = pd.DataFrame(data) if data else pd.DataFrame()

        if df.empty:
            df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS)

        st.session_state.cached_df = df
        st.session_state.last_fetch = now

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


# =========================
# UI HEADER
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

selected_date = st.date_input("📅 Select Any Date In Week", value=datetime.today())

days_from_sunday = (selected_date.weekday() + 1) % 7
week_start = selected_date - timedelta(days=days_from_sunday)

st.caption(f"Week: {week_start.strftime('%d %b %Y')}")

edit_mode = st.toggle("Edit Mode Only")

# =========================
# LOAD DATA
# =========================
all_data_df = load_data()

df = all_data_df[all_data_df["Branch"] == st.session_state.selected_branch].copy() \
    if not all_data_df.empty else pd.DataFrame(columns=["Branch","Name","Role"] + DAYS)


# =========================
# WEEK LABELS (RESTORED FIX)
# =========================
day_labels = {}

for idx, day_name in enumerate(DAYS):
    day_date = week_start + timedelta(days=idx)
    day_labels[day_name] = f"{day_name} ({day_date.strftime('%d %b %Y')})"
# =========================
# PREP DISPLAY
# =========================
if edit_mode:

    roster_df = df[["Name","Role"]].dropna().drop_duplicates() if not df.empty else pd.DataFrame(columns=["Name","Role"])

    df_display = pd.DataFrame(columns=["Name","Role"] + DAYS)

    if not roster_df.empty:
        df_display["Name"] = roster_df["Name"].values
        df_display["Role"] = roster_df["Role"].values

    # APPLY BUFFER TO DISPLAY
    for i, row in df_display.iterrows():
        for d in DAYS:
            key = f"{i}_{d}"
            if key in st.session_state.shift_buffer:
                df_display.loc[i, d] = st.session_state.shift_buffer[key]

    # =========================
    # EDITOR CONFIG
    # =========================
    config = {
        "Name": st.column_config.SelectboxColumn("Name", options=df["Name"].dropna().unique().tolist() if not df.empty else []),
        "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS)
    }

    for d in DAYS:
        config[d] = st.column_config.SelectboxColumn(d, options=SHIFT_OPTIONS)

    edited_df = st.data_editor(df_display, column_config=config, num_rows="dynamic", key="editor")

    # =========================
    # CUSTOM TIME UI
    # =========================
    for i, row in edited_df.iterrows():
        for d in DAYS:

            if row.get(d) == "➕ Custom Time":

                st.info(f"⏰ {row['Name']} - {d}")

                col1, col2 = st.columns(2)

                with col1:
                    sh = st.selectbox("Start Hour", list(range(1,13)), key=f"sh_{i}_{d}")
                    sap = st.selectbox("AM/PM", ["AM","PM"], key=f"sap_{i}_{d}")

                with col2:
                    eh = st.selectbox("End Hour", list(range(1,13)), key=f"eh_{i}_{d}")
                    eap = st.selectbox("AM/PM", ["AM","PM"], key=f"eap_{i}_{d}")

                apply_all = st.checkbox("Apply to all days", key=f"all_{i}_{d}")

                if st.button("Apply", key=f"apply_{i}_{d}"):

                    start = f"{sh} {sap}"
                    end = f"{eh} {eap}"

                    value, hrs = format_shift(start, end)

                    if value is None:
                        st.error("❌ Minimum 9 hours required")
                        st.stop()

                    if apply_all:
                        for day in DAYS:
                            st.session_state.shift_buffer[f"{i}_{day}"] = value
                    else:
                        st.session_state.shift_buffer[f"{i}_{d}"] = value

                    st.rerun()

            if row.get(d) == "📴 Day Off":
                st.session_state.shift_buffer[f"{i}_{d}"] = "OFF"




# =========================
# VIEW MODE
# =========================
else:
    df_display = df.copy()

    column_defs = [
        {"headerName":"Name","field":"Name","pinned":"left"},
        {"headerName":"Role","field":"Role"}
    ]

    for d in DAYS:
        column_defs.append({"headerName":day_labels[d],"field":d})

    AgGrid(df_display, gridOptions={
        "columnDefs": column_defs,
        "defaultColDef": {"resizable": True}
    }, height=500)

# =========================
# SAVE (NO SHEET CLEAR)
# =========================
if edit_mode and st.button("💾 Save to Master Sheet"):

    ws = master_sheet.worksheet("StaffSchedule")

    full_df = st.session_state.cached_df.copy()

    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch

    current = full_df[full_df["Branch"] == st.session_state.selected_branch].copy()
    others = full_df[full_df["Branch"] != st.session_state.selected_branch].copy()

    for _, row in new_data.iterrows():
        mask = (current["Name"] == row["Name"]) & (current["Role"] == row["Role"])

        if mask.any():
            for d in DAYS:
                current.loc[mask, d] = row.get(d, "")
        else:
            current = pd.concat([current, pd.DataFrame([row])], ignore_index=True)

    final = pd.concat([others, current], ignore_index=True)

    ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

    # RESET ONLY UI (NOT SHEET)
    st.session_state.shift_buffer = {}

    for d in DAYS:
        df_display[d] = ""

    st.success("✅ Saved successfully!")
    st.rerun()

# =========================
# BACK
# =========================
if st.button("⬅ Back"):
    st.switch_page("app.py")
