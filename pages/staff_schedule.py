import streamlit as st
import gspread
import pandas as pd
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Weekly Schedule")

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
# WEEK
# =========================================================

st.title("📅 Weekly Staff Schedule")

from_date = st.date_input("Week Start Date", datetime.date.today())

worksheet_name = f"Weekly_{from_date}"

days = ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"]

columns = ["StaffID","EmployeeName","Role",*days,"Notes"]

# =========================================================
# LOAD (ONLY ONCE)
# =========================================================

@st.cache_data(ttl=60)
def load_data():
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=columns)

df = load_data()

for c in columns:
    if c not in df.columns:
        df[c] = ""

df = df[columns]

# =========================================================
# SINGLE EXCEL EDITOR
# =========================================================

st.subheader("📊 Weekly Schedule (Excel View)")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True
)

# =========================================================
# SAVE BUTTON
# =========================================================

col1, col2 = st.columns([1,5])

with col1:

    if st.button("💾 SAVE", type="primary"):

        ws = sheet.worksheet(worksheet_name)

        edited_df = edited_df.fillna("")
        edited_df = edited_df[columns]

        final = [columns] + edited_df.values.tolist()

        ws.clear()
        ws.update(final)

        st.success("Saved successfully")
        st.rerun()

# =========================================================
# DOWNLOAD BUTTON
# =========================================================

with col2:

    csv = edited_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ DOWNLOAD",
        csv,
        file_name=f"{branch_info['BranchCode']}_weekly_{from_date}.csv",
        mime="text/csv"
    )

# =========================================================
# COLORED TABLE VIEW (VISUAL ONLY)
# =========================================================

st.divider()
st.subheader("🎨 Visual Weekly View")

def color_rows(row):
    if "OFF" in row.values:
        return ["background-color: #ffe5e5"] * len(row)
    elif "Morning" in row.values:
        return ["background-color: #e6f7ff"] * len(row)
    elif "Evening" in row.values:
        return ["background-color: #fff7e6"] * len(row)
    else:
        return [""] * len(row)

styled = edited_df.style.apply(color_rows, axis=1)

st.dataframe(styled, use_container_width=True)

# =========================================================
# BACK
# =========================================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
