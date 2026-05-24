import streamlit as st
import gspread
import pandas as pd
import time
from oauth2client.service_account import ServiceAccountCredentials

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    layout="wide",
    page_title="Staff Schedule"
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

# =========================================================
# OPEN SHEET
# =========================================================

sheet = client.open_by_key(branch_info["SheetID"])

# =========================================================
# LOAD STAFF SCHEDULE
# =========================================================

@st.cache_data(ttl=60)
def load_staff_schedule(sheet_id):

    local_sheet = client.open_by_key(sheet_id)

    try:
        ws = local_sheet.worksheet("StaffSchedule")

    except:

        ws = local_sheet.add_worksheet(
            title="StaffSchedule",
            rows=1000,
            cols=20
        )

        headers = [
            "StaffID",
            "EmployeeName",
            "MobileNumber",
            "Role",
            "Shift",
            "OffDay",
            "Status",
            "Notes"
        ]

        ws.append_row(headers)

    data = ws.get_all_records()

    if len(data) == 0:

        return pd.DataFrame(columns=[
            "StaffID",
            "EmployeeName",
            "MobileNumber",
            "Role",
            "Shift",
            "OffDay",
            "Status",
            "Notes"
        ])

    df = pd.DataFrame(data)

    return df


df = load_staff_schedule(branch_info["SheetID"])

# =========================================================
# CLEAN DATAFRAME
# =========================================================

df.columns = df.columns.str.strip()

df = df.fillna("")

# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_columns = [
    "StaffID",
    "EmployeeName",
    "MobileNumber",
    "Role",
    "Shift",
    "OffDay",
    "Status",
    "Notes"
]

for col in required_columns:

    if col not in df.columns:
        df[col] = ""

# FORCE STRING TYPE

for col in required_columns:
    df[col] = df[col].astype(str)

# KEEP ONLY REQUIRED COLUMNS

df = df[required_columns]

# =========================================================
# PAGE TITLE
# =========================================================

st.title(f"📅 Staff Schedule - {branch_info['BranchName']}")

st.caption(f"Branch Code: {branch_info['BranchCode']}")

# =========================================================
# KPI SECTION
# =========================================================

total_staff = len(df)

morning_staff = len(df[df["Shift"] == "MORNING"])

evening_staff = len(df[df["Shift"] == "EVENING"])

active_staff = len(df[df["Status"] == "ACTIVE"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Staff", total_staff)

col2.metric("Morning Shift", morning_staff)

col3.metric("Evening Shift", evening_staff)

col4.metric("Active Staff", active_staff)

st.divider()

# =========================================================
# FILTERS
# =========================================================

st.subheader("🔍 Search & Filters")

f1, f2, f3 = st.columns(3)

with f1:

    search_query = st.text_input(
        "Search Staff",
        placeholder="Search name / mobile / role"
    )

with f2:

    shift_filter = st.selectbox(
        "Shift Filter",
        [
            "ALL",
            "MORNING",
            "EVENING"
        ]
    )

with f3:

    status_filter = st.selectbox(
        "Status Filter",
        [
            "ALL",
            "ACTIVE",
            "INACTIVE"
        ]
    )

filtered_df = df.copy()

# =========================================================
# SEARCH FILTER
# =========================================================

if search_query:

    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: row.astype(str)
            .str.contains(search_query, case=False)
            .any(),
            axis=1
        )
    ]

# =========================================================
# SHIFT FILTER
# =========================================================

if shift_filter != "ALL":

    filtered_df = filtered_df[
        filtered_df["Shift"] == shift_filter
    ]

# =========================================================
# STATUS FILTER
# =========================================================

if status_filter != "ALL":

    filtered_df = filtered_df[
        filtered_df["Status"] == status_filter
    ]

# =========================================================
# FINAL CLEAN BEFORE EDITOR
# =========================================================

filtered_df = filtered_df.fillna("")

for col in required_columns:
    filtered_df[col] = filtered_df[col].astype(str)

# =========================================================
# DATA EDITOR
# =========================================================

st.subheader("📝 Edit Staff Schedule")

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

        "MobileNumber": st.column_config.TextColumn(
            "Mobile Number"
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

        "Shift": st.column_config.SelectboxColumn(
            "Shift",
            options=[
                "",
                "MORNING",
                "EVENING"
            ]
        ),

        "OffDay": st.column_config.SelectboxColumn(
            "Off Day",
            options=[
                "",
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday"
            ]
        ),

        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=[
                "",
                "ACTIVE",
                "INACTIVE"
            ]
        ),

        "Notes": st.column_config.TextColumn(
            "Notes"
        )

    }
)

# =========================================================
# SAVE SECTION
# =========================================================

st.divider()

save_col1, save_col2 = st.columns([1, 5])

with save_col1:

    if st.button(
        "💾 SAVE",
        type="primary",
        use_container_width=True
    ):

        try:

            ws = sheet.worksheet("StaffSchedule")

            # CLEAN DATA
            edited_df = edited_df.fillna("")

            # FORCE STRING
            for col in required_columns:
                edited_df[col] = edited_df[col].astype(str)

            # KEEP COLUMN ORDER
            edited_df = edited_df[required_columns]

            # PREPARE FINAL DATA
            final_data = [
                required_columns
            ] + edited_df.values.tolist()

            # CLEAR SHEET
            ws.clear()

            # UPDATE SHEET
            ws.update(final_data)

            # CLEAR CACHE
            st.cache_data.clear()

            st.success("✅ Staff schedule updated successfully.")

            time.sleep(1)

            st.rerun()

        except Exception as e:

            st.error(f"Error saving data: {e}")

# =========================================================
# DOWNLOAD CSV
# =========================================================

st.divider()

csv = edited_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download Staff Schedule CSV",
    data=csv,
    file_name=f"{branch_info['BranchCode']}_staff_schedule.csv",
    mime="text/csv",
    use_container_width=True
)

# =========================================================
# INTERNAL NOTES
# =========================================================

with st.expander("📌 Internal Notes"):

    st.info(
        "Use this section for temporary branch notes."
    )

    notes = st.text_area(
        "Branch Notes",
        height=150
    )

    if st.button("Save Notes"):
        st.success("Notes saved locally.")

# =========================================================
# BACK BUTTON
# =========================================================

st.divider()

if st.button("⬅ Back To Dashboard"):
    st.switch_page("app.py")
