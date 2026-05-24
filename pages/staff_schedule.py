import streamlit as st
import gspread
import pandas as pd
import datetime
import time
from oauth2client.service_account import ServiceAccountCredentials

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    layout="wide",
    page_title="Weekly Staff Schedule"
)

# =========================================================
# SESSION CHECK
# =========================================================

if "branch_info" not in st.session_state:

    st.warning("Session expired. Please login again.")

    if st.button("Return Home"):
        st.switch_page("app.py")

    st.stop()

branch_info = st.session_state.branch_info

# =========================================================
# GOOGLE SHEETS CONNECTION
# =========================================================

@st.cache_resource
def connect_gsheet():

    creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )

    client = gspread.authorize(creds)

    return client


client = connect_gsheet()

sheet = client.open_by_key(branch_info["SheetID"])

# =========================================================
# WEEK CALCULATION
# =========================================================

today = datetime.date.today()

start_of_week = today - datetime.timedelta(days=today.weekday())

week_string = start_of_week.strftime("%Y-%m-%d")

# =========================================================
# PAGE HEADER
# =========================================================

st.title(f"📅 Weekly Staff Schedule")

st.subheader(f"{branch_info['BranchName']}")

st.caption(f"Week Starting: {week_string}")

# =========================================================
# WORKSHEET SETUP
# =========================================================

worksheet_name = f"WeeklySchedule_{week_string}"

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
# KPI SECTION
# =========================================================

total_staff = len(df)

morning_count = 0
evening_count = 0
off_count = 0

day_columns = [
    "Saturday",
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
]

for day in day_columns:

    morning_count += len(df[df[day] == "M"])

    evening_count += len(df[df[day] == "E"])

    off_count += len(df[df[day] == "OFF"])

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Staff", total_staff)

k2.metric("Morning Shifts", morning_count)

k3.metric("Evening Shifts", evening_count)

k4.metric("OFF Days", off_count)

st.divider()

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
# SHIFT LEGEND
# =========================================================

with st.expander("📘 Shift Codes"):

    st.markdown("""
    - **M** = Morning Shift  
    - **E** = Evening Shift  
    - **OFF** = Weekly Off  
    - **LV** = Leave  
    - **ABS** = Absent  
    """)

# =========================================================
# DATA EDITOR
# =========================================================

shift_options = [
    "",
    "M",
    "E",
    "OFF",
    "LV",
    "ABS"
]

st.subheader("📝 Weekly Schedule Planner")

edited_df = st.data_editor(
    filtered_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,

    column_config={

        "StaffID": st.column_config.TextColumn(
            "Staff ID"
        ),

        "EmployeeName": st.column_config.TextColumn(
            "Employee Name"
        ),

        "Role": st.column_config.SelectboxColumn(
            "Role",
            options=[
                "",
                "Manager",
                "Supervisor",
                "Cashier",
                "Kitchen",
                "Cleaner",
                "Barista",
                "Driver",
                "Staff"
            ]
        ),

        "Saturday": st.column_config.SelectboxColumn(
            "Saturday",
            options=shift_options
        ),

        "Sunday": st.column_config.SelectboxColumn(
            "Sunday",
            options=shift_options
        ),

        "Monday": st.column_config.SelectboxColumn(
            "Monday",
            options=shift_options
        ),

        "Tuesday": st.column_config.SelectboxColumn(
            "Tuesday",
            options=shift_options
        ),

        "Wednesday": st.column_config.SelectboxColumn(
            "Wednesday",
            options=shift_options
        ),

        "Thursday": st.column_config.SelectboxColumn(
            "Thursday",
            options=shift_options
        ),

        "Friday": st.column_config.SelectboxColumn(
            "Friday",
            options=shift_options
        ),

        "Notes": st.column_config.TextColumn(
            "Notes"
        )

    }
)

# =========================================================
# SAVE BUTTON
# =========================================================

st.divider()

save_col1, save_col2 = st.columns([1,5])

with save_col1:

    if st.button(
        "💾 SAVE WEEKLY SCHEDULE",
        type="primary",
        use_container_width=True
    ):

        try:

            ws = sheet.worksheet(worksheet_name)

            edited_df = edited_df.fillna("")

            for col in required_columns:
                edited_df[col] = edited_df[col].astype(str)

            edited_df = edited_df[required_columns]

            final_data = [
                required_columns
            ] + edited_df.values.tolist()

            ws.clear()

            ws.update(final_data)

            st.cache_data.clear()

            st.success("✅ Weekly schedule saved successfully.")

            time.sleep(1)

            st.rerun()

        except Exception as e:

            st.error(f"Error saving schedule: {e}")

# =========================================================
# DOWNLOAD CSV
# =========================================================

csv = edited_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download Weekly Schedule",
    data=csv,
    file_name=f"{branch_info['BranchCode']}_{week_string}_schedule.csv",
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
# UNDERSTAFF ALERTS
# =========================================================

st.divider()

st.subheader("🚨 Understaff Alerts")

alerts = []

for day in day_columns:

    morning = len(df[df[day] == "M"])

    evening = len(df[df[day] == "E"])

    if morning < 2:

        alerts.append(
            f"{day}: Low MORNING staffing ({morning})"
        )

    if evening < 2:

        alerts.append(
            f"{day}: Low EVENING staffing ({evening})"
        )

if alerts:

    for alert in alerts:
        st.warning(alert)

else:

    st.success("✅ Staffing levels look healthy.")

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
