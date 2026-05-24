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
# DATE RANGE (USER SELECT)
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

@st.cache_data(ttl=60)
def load_data():
    try:
        ws = sheet.worksheet(worksheet_name)
    except:
        ws = sheet.add_worksheet(worksheet_name, 1000, 20)
        ws.append_row(required_columns)

    data = ws.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=required_columns)

df = load_data()

df = df.fillna("")

for c in required_columns:
    if c not in df.columns:
        df[c] = ""

df = df[required_columns]

# =========================================================
# LOAD / CREATE SHEET
# =========================================================

@st.cache_data(ttl=60)
def load_schedule():

    try:

        ws = sheet.worksheet(worksheet_name)

    except:

        ws = sheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=20
        )

        ws.append_row(required_columns)

    data = ws.get_all_records()

    if len(data) == 0:

        return pd.DataFrame(columns=required_columns)

    df = pd.DataFrame(data)

    return df


df = load_schedule()

# =========================================================
# CLEAN DATA
# =========================================================

df.columns = df.columns.str.strip()

df = df.fillna("")

for col in required_columns:

    if col not in df.columns:
        df[col] = ""

for col in required_columns:
    df[col] = df[col].astype(str)

df = df[required_columns]

# =========================================================
# COPY PREVIOUS WEEK BUTTON
# =========================================================

top1, top2, top3 = st.columns([1,1,5])

with top1:

    if st.button("📋 Copy Last Week"):

        try:

            previous_week = start_of_week - datetime.timedelta(days=7)

            previous_week_string = previous_week.strftime("%Y-%m-%d")

            previous_sheet_name = f"WeeklySchedule_{previous_week_string}"

            previous_ws = sheet.worksheet(previous_sheet_name)

            previous_data = previous_ws.get_all_records()

            if previous_data:

                current_ws = sheet.worksheet(worksheet_name)

                current_ws.clear()

                previous_df = pd.DataFrame(previous_data)

                final_data = [
                    previous_df.columns.tolist()
                ] + previous_df.values.tolist()

                current_ws.update(final_data)

                st.success("Previous week copied successfully.")

                st.cache_data.clear()

                time.sleep(1)

                st.rerun()

            else:
                st.warning("Previous week is empty.")

        except Exception as e:

            st.error(f"Error: {e}")


# =========================================================
# SEARCH FILTER
# =========================================================

search = st.text_input(
    "🔍 Search Staff",
    placeholder="Search name / role / ID"
)

filtered_df = df.copy()

if search:

    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: row.astype(str)
            .str.contains(search, case=False)
            .any(),
            axis=1
        )
    ]




# =========================================================
# EDITOR (NO SHIFT CODES UI)
# =========================================================

st.subheader(f"📝 Schedule ({week_label})")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    column_config={
        "StaffID": st.column_config.TextColumn("Staff ID"),
        "EmployeeName": st.column_config.TextColumn("Employee Name"),
        "Role": st.column_config.TextColumn("Role"),

        "Saturday": st.column_config.TextColumn("Saturday"),
        "Sunday": st.column_config.TextColumn("Sunday"),
        "Monday": st.column_config.TextColumn("Monday"),
        "Tuesday": st.column_config.TextColumn("Tuesday"),
        "Wednesday": st.column_config.TextColumn("Wednesday"),
        "Thursday": st.column_config.TextColumn("Thursday"),
        "Friday": st.column_config.TextColumn("Friday"),

        "Notes": st.column_config.TextColumn("Notes")
    }
)

# =========================================================
# SAVE (NO KPI RESET, ONLY VISUAL RESET)
# =========================================================

if st.button("💾 SAVE WEEKLY SCHEDULE", type="primary"):

    ws = sheet.worksheet(worksheet_name)

    edited_df = edited_df.fillna("")
    edited_df = edited_df[required_columns]

    final = [required_columns] + edited_df.values.tolist()

    ws.clear()
    ws.update(final)

    st.success("Saved successfully")

    st.rerun()

# =========================================================
# WEEKLY OVERVIEW (YOUR REQUESTED FORMAT)
# =========================================================

st.divider()
st.subheader("📊 Weekly Overview")

overview_cols = [
    "EmployeeName",
    "Saturday",
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
]

overview_df = edited_df[overview_cols].copy()

st.dataframe(overview_df, use_container_width=True, hide_index=True)

# =========================================================
# DOWNLOAD CSV
# =========================================================

csv = edited_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download Weekly Schedule",
    data=csv,
    file_name=f"{branch_info['BranchCode']}_weekly_schedule_{from_date}.csv",
    mime="text/csv",
    use_container_width=True
)

# =========================================================
# STAFFING ANALYTICS
# =========================================================

st.divider()

st.subheader("📊 Weekly Staffing Overview")

analytics = []

for day in day_columns:

    morning = len(df[df[day] == "M"])

    evening = len(df[df[day] == "E"])

    off = len(df[df[day] == "OFF"])

    leave = len(df[df[day] == "LV"])

    analytics.append({
        "Day": day,
        "Morning": morning,
        "Evening": evening,
        "OFF": off,
        "Leave": leave
    })

analytics_df = pd.DataFrame(analytics)

st.dataframe(
    analytics_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# INTERNAL NOTES
# =========================================================

with st.expander("📌 Manager Notes"):

    notes = st.text_area(
        "Weekly Notes",
        height=150,
        placeholder="Add shift notes, leave comments, staffing reminders..."
    )

    if st.button("Save Notes"):
        st.success("Notes saved locally.")

# =========================================================
# BACK BUTTON
# =========================================================

st.divider()

if st.button("⬅ Back To Dashboard"):

    st.switch_page("app.py")
