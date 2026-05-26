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
        if st.button("⬅ Back to Staff Login"):
            st.switch_page("app.py")

    st.stop()

# =========================
# GOOGLE CLIENT
# =========================
if "gspread_client" not in st.session_state:

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["GOOGLE_CREDS_JSON"],
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    st.session_state.gspread_client = gspread.authorize(creds)

sheet = st.session_state.gspread_client.open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

history_sheet = sheet.worksheet("SubmissionHistory")

# =========================
# CONFIG
# =========================
DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

# =========================
# SESSION STATE
# =========================
for k, v in {
    "shift_buffer": {},
    "deleted_staff": set(),
    "show_preview": False,
    "preview_df": None,
    "previous_week": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# LOAD DATA
# =========================
def load_data():
    ws = sheet.worksheet("StaffSchedule")
    data = ws.get_all_records()
    return pd.DataFrame(data)

# =========================
# UTIL
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
# DUPLICATE CHECK (NEW)
# =========================
def is_already_submitted(branch, week):

    records = history_sheet.get_all_records()

    for r in records:
        if r["Branch"] == branch and r["WeekStart"] == week:
            return True

    return False

# =========================
# DIALOGS
# =========================
@st.dialog("🚫 Blocked")
def block_dialog():
    st.error("This week already submitted.")
    st.info("Contact Branch Manager for approval.")
    if st.button("Close"):
        st.rerun()

@st.dialog("📸 Preview")
def preview_dialog():

    st.success("Submitted successfully!")

    df = st.session_state.preview_df

    st.dataframe(df, use_container_width=True)

    img = generate_image(df)

    st.image(img)

    col1, col2 = st.columns(2)

    with col1:
        st.download_button("💾 Save", img, "schedule.png", "image/png")

    with col2:
        if st.button("Discard"):
            st.session_state.show_preview = False
            st.rerun()

# =========================
# HEADER
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

date = st.date_input("Select Date", datetime.today())

week_start = date - timedelta(days=(date.weekday()+1)%7)
week_key = week_start.strftime("%d-%b-%Y")

st.caption(f"Week: {week_key}")

# reset
if st.session_state.previous_week != week_key:
    st.session_state.shift_buffer = {}
    st.session_state.previous_week = week_key

edit_mode = st.toggle("Edit Mode")

# =========================
# DATA
# =========================
df_all = load_data()
df = df_all[df_all["Branch"] == st.session_state.selected_branch]

existing = is_already_submitted(st.session_state.selected_branch, week_key)

# =========================
# EDIT MODE
# =========================
if edit_mode:

    df_display = df[["Name","Role"]].dropna().drop_duplicates()

    for d in DAYS:
        df_display[d] = ""

    edited = st.data_editor(df_display, use_container_width=True)

    # =========================
    # SUBMIT
    # =========================
    if st.button("Submit"):

        if existing:
            block_dialog()
            st.stop()

        ws = sheet.worksheet("StaffSchedule")

        new_df = edited.copy()
        new_df["Branch"] = st.session_state.selected_branch

        final = pd.concat([df_all, new_df], ignore_index=True)

        ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

        # log history (NEW)
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
