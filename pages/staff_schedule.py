import streamlit as st
import gspread
import pandas as pd
import datetime
import time
from oauth2client.service_account import ServiceAccountCredentials

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Weekly Staff Schedule")

if "branch_info" not in st.session_state:
    st.warning("Session expired")
    st.stop()

branch_info = st.session_state.branch_info

# =========================================================
# GOOGLE SHEETS
# =========================================================

@st.cache_resource
def connect():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["GOOGLE_CREDS_JSON"],
        ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

client = connect()
sheet = client.open_by_key(branch_info["SheetID"])

# =========================================================
# DATE RANGE
# =========================================================

st.title("📅 Weekly Staff Scheduler")

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input("From Date", datetime.date.today())

with col2:
    to_date = st.date_input("To Date", datetime.date.today() + datetime.timedelta(days=6))

week_label = f"{from_date} to {to_date}"

# =========================================================
# WORKSHEET
# =========================================================

worksheet_name = f"Weekly_{from_date}"

required_columns = [
    "StaffID",
    "EmployeeName",
    "Role",
    "Saturday",
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Notes"
]

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=60)
def load_schedule():
    try:
        ws = sheet.worksheet(worksheet_name)
    except:
        ws = sheet.add_worksheet(worksheet_name, 1000, 20)
        ws.append_row(required_columns)

    data = ws.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=required_columns)

df = load_schedule()

df = df.fillna("")

for c in required_columns:
    if c not in df.columns:
        df[c] = ""

df = df[required_columns]

# =========================================================
# COPY LAST WEEK
# =========================================================

if st.button("📋 Copy Last Week"):

    try:
        prev = from_date - datetime.timedelta(days=7)
        prev_sheet = f"Weekly_{prev}"

        ws_prev = sheet.worksheet(prev_sheet)
        ws_curr = sheet.worksheet(worksheet_name)

        data = ws_prev.get_all_values()

        if data:
            ws_curr.clear()
            ws_curr.update(data)
            st.success("Copied last week")
            st.rerun()

    except Exception as e:
        st.warning("No previous week found")

# =========================================================
# SEARCH
# =========================================================

search = st.text_input("🔍 Search Staff")

filtered_df = df.copy()

if search:
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda r: r.astype(str).str.contains(search, case=False).any(),
            axis=1
        )
    ]

# =========================================================
# DRAG-STYLE SHIFT TOOL
# =========================================================

st.subheader("🎯 Shift Selector")

shift = st.selectbox(
    "Choose Shift",
    ["", "Morning", "Evening", "OFF", "Leave"]
)

days = ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"]

# =========================================================
# INIT STATE
# =========================================================

if "grid" not in st.session_state:
    st.session_state.grid = {}

for staff in filtered_df["EmployeeName"]:
    if staff not in st.session_state.grid:
        st.session_state.grid[staff] = {d: "" for d in days}

# =========================================================
# CLICK-TO-ASSIGN GRID (DRAG REPLACEMENT)
# =========================================================

st.subheader("📅 Weekly Grid (Click to Assign)")

for staff in filtered_df["EmployeeName"]:

    st.markdown(f"### 👤 {staff}")

    cols = st.columns(len(days))

    for i, day in enumerate(days):

        val = st.session_state.grid[staff][day]

        if cols[i].button(val if val else "➕", key=f"{staff}_{day}"):

            st.session_state.grid[staff][day] = shift

# =========================================================
# SAVE
# =========================================================

if st.button("💾 SAVE WEEKLY SCHEDULE", type="primary"):

    ws = sheet.worksheet(worksheet_name)

    final = [required_columns]

    for idx, row in filtered_df.iterrows():

        staff = row["EmployeeName"]

        new_row = [
            row["StaffID"],
            staff,
            row["Role"]
        ]

        for d in days:
            new_row.append(st.session_state.grid[staff][d])

        new_row.append("")

        final.append(new_row)

    ws.clear()
    ws.update(final)

    st.success("✅ Schedule saved")

    st.rerun()

# =========================================================
# WEEKLY OVERVIEW
# =========================================================

st.divider()
st.subheader("📊 Weekly Overview")

overview = pd.DataFrame()

try:
    ws = sheet.worksheet(worksheet_name)
    overview = pd.DataFrame(ws.get_all_records())
except:
    pass

if not overview.empty:

    st.dataframe(
        overview[["EmployeeName"] + days],
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No schedule yet")

# =========================================================
# DOWNLOAD
# =========================================================

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Schedule",
    csv,
    file_name=f"{branch_info['BranchCode']}_weekly_{from_date}.csv",
    mime="text/csv"
)

# =========================================================
# BACK
# =========================================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
