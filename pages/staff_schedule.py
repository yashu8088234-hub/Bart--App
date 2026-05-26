import streamlit as st
import pandas as pd
import gspread
import time
import re
import io
import matplotlib.pyplot as plt

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
            "https://www.googleapis.com/auth/drive"
        ]
    )

    st.session_state.gspread_client = gspread.authorize(creds)

master_sheet = st.session_state.gspread_client.open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

history_sheet = master_sheet.worksheet("SubmissionHistory")

# =========================
# CONFIG
# =========================
DAYS = [
    "Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"
]

SHIFT_OPTIONS = [
    "➕ Custom Time",
    "📴 Day Off"
]

ROLE_OPTIONS = [
    "Team-Member","Acting_Team_Leader","Team_Leader",
    "Acting_Supervisor","Supervisor","Branch_Manager"
]

# =========================
# LOAD DATA (YOUR ORIGINAL KEPT)
# =========================
def load_data(force_reload=False):

    if force_reload or st.session_state.get("cached_df") is None:

        try:

            ws = master_sheet.worksheet("StaffSchedule")
            data = ws.get_all_records()
            df = pd.DataFrame(data) if data else pd.DataFrame()

            if not df.empty:

                new_cols = {}

                for col in df.columns:
                    for day in DAYS:
                        if day in col:
                            new_cols[col] = day
                            break

                df = df.rename(columns=new_cols)

            if df.empty:
                df = pd.DataFrame(columns=["Branch","Name","Role"] + DAYS + ["Over-Time"])

            st.session_state.cached_df = df

        except Exception as e:

            st.error(f"Error loading data: {e}")

            if st.session_state.get("cached_df") is None:

                st.session_state.cached_df = pd.DataFrame(columns=["Branch","Name","Role"] + DAYS + ["Over-Time"])

    return st.session_state.cached_df

# =========================
# SESSION STATE (YOUR SYSTEM)
# =========================
if "shift_buffer" not in st.session_state:
    st.session_state.shift_buffer = {}

if "previous_week" not in st.session_state:
    st.session_state.previous_week = None

if "deleted_staff" not in st.session_state:
    st.session_state.deleted_staff = set()

# ===== NEW ADDITIONS ONLY =====
if "show_preview" not in st.session_state:
    st.session_state.show_preview = False

if "preview_df" not in st.session_state:
    st.session_state.preview_df = None

# =========================
# LOGIC FUNCTIONS (UNCHANGED)
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
    return (f"{start} - {end} (OT {ot}h)" if ot > 0 else f"{start} - {end}", hrs)

def calculate_row_ot(row):
    total_ot = 0
    for day in DAYS:
        val = str(row.get(day, ""))
        match = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if match:
            total_ot += float(match.group(1))
    return f"{total_ot} hrs" if total_ot > 0 else "0 hrs"

# =========================
# IMAGE GENERATOR (NEW ONLY)
# =========================
def generate_image(df):

    fig, ax = plt.subplots(figsize=(18, max(4, len(df)*0.6)))
    ax.axis("off")

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    buf.seek(0)
    plt.close(fig)

    return buf

# =========================
# DUPLICATE DIALOG (YOUR ORIGINAL)
# =========================
@st.dialog("🚫 Submission Blocked")
def duplicate_submission_dialog():

    st.error("""
This week's schedule has already been submitted for this branch.
Contact Branch Manager for approval before resubmitting.
""")

    if st.button("Close"):
        st.rerun()

# =========================
# NEW PREVIEW DIALOG (ADDED ONLY)
# =========================
@st.dialog("📸 Schedule Preview")
def preview_dialog():

    st.success("Schedule Submitted Successfully!")

    df = st.session_state.preview_df

    st.dataframe(df, use_container_width=True)

    img = generate_image(df)

    st.image(img)

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "💾 Save Screenshot",
            img,
            "schedule.png",
            "image/png"
        )

    with col2:
        if st.button("❌ Discard"):
            st.session_state.show_preview = False
            st.rerun()

# =========================
# HEADER (UNCHANGED YOUR STYLE)
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

selected_date = st.date_input("📅 Select Date", value=datetime.today())

week_start = selected_date - timedelta(days=(selected_date.weekday()+1)%7)
week_start_str = week_start.strftime('%d %b %Y')

st.caption(f"Week starting: {week_start_str}")

if st.session_state.previous_week != week_start_str:
    st.session_state.shift_buffer = {}
    st.session_state.deleted_staff = set()
    st.session_state.previous_week = week_start_str

edit_mode = st.toggle("Edit Mode Only")

# =========================
# LOAD DATA
# =========================
all_data_df = load_data()

df = all_data_df[
    all_data_df["Branch"] == st.session_state.selected_branch
].copy()

# =========================
# CHECK EXISTING WEEK DATA (UNCHANGED LOGIC)
# =========================
existing_week_data = pd.DataFrame()

if not st.session_state.cached_df.empty:

    temp_df = st.session_state.cached_df.copy()

    week_cols = [d for d in DAYS]

    branch_data = temp_df[temp_df["Branch"] == st.session_state.selected_branch]

    existing_rows = branch_data[
        branch_data[week_cols].fillna("").astype(str).apply(
            lambda row: any(v.strip() != "" for v in row),
            axis=1
        )
    ]

    existing_week_data = existing_rows

# =========================
# EDIT MODE (YOUR FULL LOGIC PRESERVED)
# =========================
if edit_mode:

    df_display = (
        df[["Name","Role"]]
        .dropna(subset=["Name"])
        .drop_duplicates()
        .reset_index(drop=True)
    )

    for d in DAYS:
        df_display[d] = ""

    # restore buffer
    for i, row in df_display.iterrows():
        for d in DAYS:
            key = f"{i}_{d}"
            if key in st.session_state.shift_buffer:
                df_display.loc[i, d] = st.session_state.shift_buffer[key]

    df_display["Over-Time"] = df_display.apply(calculate_row_ot, axis=1)

    edited_df = st.data_editor(df_display, use_container_width=True)

    # SHIFT ACTIONS (UNCHANGED)
    for i, row in edited_df.iterrows():

        for d in DAYS:

            if row.get(d) == "📴 Day Off":
                st.session_state.shift_buffer[f"{i}_{d}"] = "OFF"
                st.rerun()

            if row.get(d) == "➕ Custom Time":
                custom_time_dialog(i, row["Name"], d)

    # =========================
    # SUBMIT BUTTON (UPGRADED SAFELY)
    # =========================
    if st.button("✅ Submit"):

        if not existing_week_data.empty:
            duplicate_submission_dialog()
            st.stop()

        ws = master_sheet.worksheet("StaffSchedule")

        new_df = edited_df.copy()
        new_df["Branch"] = st.session_state.selected_branch

        final = pd.concat(
            [all_data_df[all_data_df["Branch"] != st.session_state.selected_branch], new_df],
            ignore_index=True
        )

        ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

        # HISTORY LOG (NEW)
        history_sheet.append_row([
            st.session_state.selected_branch,
            week_start_str,
            "User",
            str(datetime.now())
        ])

        # PREVIEW POPUP (NEW)
        st.session_state.preview_df = new_df
        st.session_state.show_preview = True

        st.rerun()

# =========================
# VIEW MODE (UNCHANGED)
# =========================
else:
    AgGrid(df, height=500)

# =========================
# PREVIEW POPUP TRIGGER
# =========================
if st.session_state.show_preview:
    preview_dialog()

# =========================
# BACK BUTTON
# =========================
if st.button("⬅ Back"):
    st.switch_page("app.py")
