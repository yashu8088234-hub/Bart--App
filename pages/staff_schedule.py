import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from st_aggrid import AgGrid

st.set_page_config(
    layout="wide",
    page_title="BART Master Schedule"
)

# =========================================
# 1. AUTH & CONNECTION
# =========================================

if (
    "authenticated" not in st.session_state
    or not st.session_state.authenticated
):
    st.error("Please login first.")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
)

master_sheet = gspread.authorize(creds).open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

# =========================================
# 2. CONFIG
# =========================================

DAYS = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]

ROLE_OPTIONS = [
    "Staff",
    "Supervisor",
    "Acting Supervisor",
    "Team Leader",
    "Acting Team Leader"
]

SHIFT_OPTIONS = [
    "Morning shift",
    "Mid shift",
    "Evening shift",
    "Night shift",
    "Day off "
]

# =========================================
# 3. UI
# =========================================

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

# kept ONLY for future use (not connected to data)
start_date = st.date_input("Week Start Date")

shift_mode = st.toggle("Enable Shift-wise Mode")

# =========================================
# 4. LOAD DATA (NO DATE USAGE)
# =========================================

def get_filtered_data():
    ws = master_sheet.worksheet("StaffSchedule")
    all_data = ws.get_all_records()

    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["Branch", "Name", "Role"])

    return df[df["Branch"] == st.session_state.selected_branch]


df = get_filtered_data()

# =========================================
# 5. BUILD UI
# =========================================

st.subheader("Roster View")

config = {
    "Role": st.column_config.SelectboxColumn(
        "Role",
        options=ROLE_OPTIONS
    )
}

df_display = df.copy()

# =========================================
# SHIFT PREPARATION
# =========================================

for day in DAYS:

    if shift_mode:

        if day not in df_display.columns:
            df_display[day] = ""

        config[day] = st.column_config.SelectboxColumn(
            day,
            options=SHIFT_OPTIONS
        )

    else:

        if day not in df_display.columns:
            df_display[day] = ""

# =========================================
# SHIFT MODE (EDITABLE)
# =========================================

if shift_mode:

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True
    )

# =========================================
# NORMAL MODE (VIEW ONLY)
# =========================================

else:

    ordered_cols = ["Name", "Role"] + DAYS

    existing_cols = [
        c for c in ordered_cols
        if c in df_display.columns
    ]

    df_display = df_display[existing_cols]

    column_defs = [
        {
            "headerName": "Name",
            "field": "Name",
            "pinned": "left",
            "width": 180
        },
        {
            "headerName": "Role",
            "field": "Role",
            "width": 180
        }
    ]

    for day in DAYS:

        column_defs.append({
            "headerName": day,
            "field": day,
            "width": 150
        })

    grid_options = {
        "columnDefs": column_defs,
        "defaultColDef": {
            "resizable": True,
            "sortable": False,
            "cellStyle": {"textAlign": "left"}
        },
        "headerHeight": 45,
        "rowHeight": 42,
        "animateRows": True
    }

    custom_css = {
        ".ag-header-group-cell-label": {
            "justify-content": "flex-start",
            "font-weight": "bold",
            "font-size": "15px"
        },
        ".ag-header-cell-label": {
            "justify-content": "flex-start",
            "font-size": "13px"
        },
        ".ag-cell": {
            "display": "flex",
            "justify-content": "flex-start",
            "align-items": "center",
            "text-align": "left"
        }
    }

    grid_response = AgGrid(
        df_display,
        gridOptions=grid_options,
        custom_css=custom_css,
        height=650,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        editable=False,
        theme="streamlit"
    )

    edited_df = pd.DataFrame(grid_response["data"])

# =========================================
# 6. SAVE LOGIC (NO DATE STORED)
# =========================================

if st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")

    full_data = pd.DataFrame(ws.get_all_records())

    remaining_data = full_data[
        full_data["Branch"] != st.session_state.selected_branch
    ]

    new_data = edited_df.copy()

    new_data["Branch"] = st.session_state.selected_branch

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.upper()

    final_df = pd.concat([remaining_data, new_data], ignore_index=True)

    ws.clear()

    ws.update(
        [final_df.columns.values.tolist()] +
        final_df.fillna("").values.tolist()
    )

    st.success("✅ Saved Successfully!")
    st.rerun()

# =========================================
# 7. BACK BUTTON
# =========================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
