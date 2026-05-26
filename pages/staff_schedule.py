import streamlit as st
import pandas as pd
import gspread
import time
import re
import matplotlib.pyplot as plt
import numpy as np
import io

from oauth2client.service_account import ServiceAccountCredentials
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
            st.switch_page("app.py")
    st.stop()

# =========================
# GOOGLE CLIENT
# =========================
if "gspread_client" not in st.session_state:
    creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        [
            "https://spreadsheets.google.com/feeds",
            "https://googleapis.com/auth/drive"
        ]
    )
    st.session_state.gspread_client = gspread.authorize(creds)

master_sheet = st.session_state.gspread_client.open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

# =========================
# CONFIG
# =========================
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SHIFT_OPTIONS = ["➕ Custom Time", "📴 Day Off"]
ROLE_OPTIONS = ["Team-Member", "Acting_Team_Leader", "Team_Leader", "Acting_Supervisor", "Supervisor", "Branch_Manager"]

# =========================
# 🔥 NEW: IMAGE GENERATOR
# =========================
def generate_schedule_image(df, title="BART Master Schedule"):
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis('off')

    if df.empty:
        ax.text(0.5, 0.5, "No Schedule Data", ha='center', va='center', fontsize=14)
    else:
        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='center',
            loc='center'
        )

        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)

        # Header styling
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor("#1f4e79")
            else:
                cell.set_facecolor("#f2f2f2" if row % 2 == 0 else "white")

    plt.title(title, fontsize=14, fontweight='bold')

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=200)
    buf.seek(0)
    plt.close(fig)

    return buf

# =========================
# DIALOGS
# =========================
@st.dialog("✅ Submission Successful")
def success_dialog():
    st.success("Schedule submitted successfully 🎉")

    if "submitted_img" in st.session_state:
        st.image(st.session_state.submitted_img, caption="Schedule Snapshot", use_container_width=True)

        st.download_button(
            "📥 Download Schedule Image",
            data=st.session_state.submitted_img,
            file_name="schedule_snapshot.png",
            mime="image/png",
            use_container_width=True
        )

    if st.button("Close", use_container_width=True):
        st.rerun()

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
# LOGIC FUNCTIONS
# =========================
def load_data(force_reload=False):
    if force_reload or st.session_state.get("cached_df") is None:
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            data = ws.get_all_records()
            df = pd.DataFrame(data) if data else pd.DataFrame()

            if df.empty:
                df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS + ["Over-Time"])

            st.session_state.cached_df = df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.session_state.cached_df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS + ["Over-Time"])
    return st.session_state.cached_df

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
    if ot > 0:
        return (f"{start} - {end} (OT {ot}h)", hrs)
    return (f"{start} - {end}", hrs)

def calculate_row_ot(row):
    total_ot = 0
    for day in DAYS:
        val = str(row.get(day, ""))
        match = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if match:
            total_ot += float(match.group(1))
    return f"{total_ot} hrs" if total_ot > 0 else "0 hrs"

# =========================
# INIT SESSION
# =========================
if "shift_buffer" not in st.session_state: st.session_state.shift_buffer = {}
if "previous_week" not in st.session_state: st.session_state.previous_week = None
if "deleted_staff" not in st.session_state: st.session_state.deleted_staff = set()

# =========================
# UI
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

selected_date = st.date_input("📅 Select Date", value=datetime.today())
week_start = selected_date - timedelta(days=(selected_date.weekday() + 1) % 7)

week_start_str = week_start.strftime('%d %b %Y')
st.caption(f"Week starting: {week_start_str}")

if st.session_state.previous_week != week_start_str:
    st.session_state.shift_buffer = {}
    st.session_state.deleted_staff = set()
    st.session_state.previous_week = week_start_str

# =========================
# LOAD
# =========================
all_data_df = load_data()
df = all_data_df[all_data_df["Branch"] == st.session_state.selected_branch].copy()

# =========================
# SUBMIT BLOCK (MODIFIED ONLY HERE)
# =========================
if st.button("✅ Submit"):

    try:
        # 🔥 CREATE IMAGE BEFORE SAVING
        preview_df = df.copy()
        preview_df["Over-Time"] = preview_df.apply(calculate_row_ot, axis=1)

        img_buffer = generate_schedule_image(preview_df)
        st.session_state.submitted_img = img_buffer.getvalue()

        # existing save logic (unchanged conceptually)
        ws = master_sheet.worksheet("StaffSchedule")

        new_data = df.copy()
        new_data["Branch"] = st.session_state.selected_branch

        ws.update([new_data.columns.tolist()] + new_data.fillna("").values.tolist())

        st.session_state.cached_df = new_data
        st.session_state.shift_buffer = {}
        st.session_state.deleted_staff = set()

        success_dialog()

    except Exception as e:
        st.error(f"❌ Submission Failed: {e}")

# =========================
# (rest of your code unchanged below)
# =========================
