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

    col1, col2, col3 = st.columns([1,1,1])

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
DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

SHIFT_OPTIONS = ["➕ Custom Time", "📴 Day Off"]

ROLE_OPTIONS = [
    "Team-Member","Acting_Team_Leader","Team_Leader",
    "Acting_Supervisor","Supervisor","Branch_Manager"
]

# =========================
# SESSION STATE
# =========================
for k, v in {
    "shift_buffer": {},
    "deleted_staff": set(),
    "previous_week": None,
    "show_preview": False,
    "preview_df": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# LOAD DATA (YOUR ORIGINAL LOGIC KEPT SAFE)
# =========================
def load_data(force_reload=False):

    if force_reload or st.session_state.get("cached_df") is None:

        ws = master_sheet.worksheet("StaffSchedule")
        data = ws.get_all_records()
        df = pd.DataFrame(data) if data else pd.DataFrame()

        if df.empty:
            df = pd.DataFrame(columns=["Branch","Name","Role"] + DAYS + ["Over-Time"])

        st.session_state.cached_df = df

    return st.session_state.cached_df

# =========================
# YOUR LOGIC FUNCTIONS (UNCHANGED)
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
    for d in DAYS:
        v = str(row.get(d, ""))
        m = re.search(r"\(OT\s+(\d+\.?\d*)\s*h\)", v)
        if m:
            total_ot += float(m.group(1))
    return f"{total_ot} hrs" if total_ot else "0 hrs"

# =========================
# IMAGE GENERATOR (NEW)
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
# DUPLICATE CHECK (NEW SAFE VERSION)
# =========================
def already_submitted(branch, week):

    records = history_sheet.get_all_records()

    for r in records:
        if r["Branch"] == branch and r["WeekStart"] == week:
            return True

    return False

# =========================
# DIALOG: BLOCK
# =========================
@st.dialog("🚫 Submission Blocked")
def block_dialog():
    st.error("This week already submitted.")
    st.info("Contact Branch Manager for approval.")
    if st.button("Close"):
        st.rerun()

# =========================
# DIALOG: PREVIEW
# =========================
@st.dialog("📸 Schedule Preview")
def preview_dialog():

    st.success("Submitted successfully!")

    df = st.session_state.preview_df

    st.dataframe(df, use_container_width=True)

    img = generate_image(df)

    st.image(img)

    col1, col2 = st.columns(2)

    with col1:
        st.download_button("💾 Save Screenshot", img, "schedule.png", "image/png")

    with col2:
        if st.button("❌ Discard"):
            st.session_state.show_preview = False
            st.rerun()

# =========================
# HEADER (YOUR ORIGINAL STRUCTURE)
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

selected_date = st.date_input("📅 Select Date", datetime.today())

week_start = selected_date - timedelta(days=(selected_date.weekday()+1)%7)
week_key = week_start.strftime("%d %b %Y")

st.caption(f"Week starting: {week_key}")

if st.session_state.previous_week != week_key:
    st.session_state.shift_buffer = {}
    st.session_state.previous_week = week_key

edit_mode = st.toggle("Edit Mode Only")

# =========================
# DATA
# =========================
df_all = load_data()

df = df_all[df_all["Branch"] == st.session_state.selected_branch].copy()

existing = already_submitted(st.session_state.selected_branch, week_key)

# =========================
# EDIT MODE (YOUR SYSTEM PRESERVED)
# =========================
if edit_mode:

    df_display = df[["Name","Role"]].dropna().drop_duplicates()

    for d in DAYS:
        df_display[d] = ""

    edited = st.data_editor(df_display, use_container_width=True)

    # =========================
    # SUBMIT
    # =========================
    if st.button("✅ Submit"):

        if existing:
            block_dialog()
            st.stop()

        ws = master_sheet.worksheet("StaffSchedule")

        new_df = edited.copy()
        new_df["Branch"] = st.session_state.selected_branch

        final = pd.concat([df_all, new_df], ignore_index=True)

        ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

        # LOG HISTORY (NEW FEATURE)
        history_sheet.append_row([
            st.session_state.selected_branch,
            week_key,
            "User",
            str(datetime.now())
        ])

        st.session_state.preview_df = new_df
        st.session_state.show_preview = True

        st.rerun()

# =========================
# VIEW MODE
# =========================
else:
    AgGrid(df, height=500)

# =========================
# PREVIEW POPUP
# =========================
if st.session_state.show_preview:
    preview_dialog()

# =========================
# BACK BUTTON
# =========================
if st.button("⬅ Back"):
    st.switch_page("app.py")
