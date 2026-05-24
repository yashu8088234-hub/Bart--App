import streamlit as st
import gspread
import pandas as pd
import datetime
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
# WEEK SELECTION
# =========================================================

st.title("📅 Weekly Staff Scheduler (Excel Style)")

from_date = st.date_input("Week Start", datetime.date.today())
to_date = st.date_input("Week End", datetime.date.today() + datetime.timedelta(days=6))

worksheet_name = f"Weekly_{from_date}"

days = ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"]

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=60)
def load():
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=[
            "StaffID","EmployeeName","Role",
            *days,
            "Notes"
        ])

df = load()

# ensure columns exist
cols = ["StaffID","EmployeeName","Role",*days,"Notes"]

for c in cols:
    if c not in df.columns:
        df[c] = ""

df = df[cols]

# =========================================================
# MAIN EXCEL EDITOR (ONLY ONE PLACE)
# =========================================================

st.subheader("📝 Weekly Schedule (Excel Sheet Style)")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    column_config={
        "StaffID": st.column_config.TextColumn("Staff ID"),
        "EmployeeName": st.column_config.TextColumn("Employee Name"),
        "Role": st.column_config.TextColumn("Role"),

        "Saturday": st.column_config.TextColumn("Sat"),
        "Sunday": st.column_config.TextColumn("Sun"),
        "Monday": st.column_config.TextColumn("Mon"),
        "Tuesday": st.column_config.TextColumn("Tue"),
        "Wednesday": st.column_config.TextColumn("Wed"),
        "Thursday": st.column_config.TextColumn("Thu"),
        "Friday": st.column_config.TextColumn("Fri"),

        "Notes": st.column_config.TextColumn("Notes")
    }
)

# =========================================================
# SAVE
# =========================================================

if st.button("💾 SAVE WEEKLY SCHEDULE", type="primary"):

    ws = sheet.worksheet(worksheet_name)

    edited_df = edited_df.fillna("")
    edited_df = edited_df[cols]

    final = [cols] + edited_df.values.tolist()

    ws.clear()
    ws.update(final)

    st.success("✅ Saved successfully")

    st.rerun()

# =========================================================
# WEEKLY OVERVIEW (SAME DATAFRAME)
# =========================================================

st.divider()
st.subheader("📊 Weekly Overview")

st.dataframe(
    edited_df[["EmployeeName"] + days],
    use_container_width=True,
    hide_index=True
)

# =========================================================
# DOWNLOAD
# =========================================================

csv = edited_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download",
    csv,
    file_name=f"{branch_info['BranchCode']}_weekly_{from_date}.csv",
    mime="text/csv"
)

# =========================================================
# BACK
# =========================================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
