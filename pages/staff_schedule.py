import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from datetime import timedelta

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
    "Night shift"
]

TIME_OPTIONS = (
    [f"{h}:00 AM" for h in range(1, 13)] +
    [f"{h}:00 PM" for h in range(1, 13)] +
    ["OFF"]
)

# =========================================
# 3. UI
# =========================================

st.title(
    f"🏢 Schedule: {st.session_state.selected_branch}"
)

start_date = st.date_input("Week Start Date")

shift_mode = st.toggle("Enable Shift-wise Mode")

# DATE FORMAT
day_dates = [
    (start_date + timedelta(days=i)).strftime("%a %d/%m")
    for i in range(7)
]

# =========================================
# 4. LOAD DATA
# =========================================

def get_filtered_data():

    ws = master_sheet.worksheet("StaffSchedule")

    all_data = ws.get_all_records()

    df = (
        pd.DataFrame(all_data)
        if all_data
        else pd.DataFrame()
    )

    if df.empty:

        df = pd.DataFrame(
            columns=[
                "Branch",
                "Date",
                "Name",
                "Role"
            ]
        )

    return df[
        df["Branch"] ==
        st.session_state.selected_branch
    ]


df = get_filtered_data()

# =========================================
# 5. BUILD UI
# =========================================

st.subheader("Edit Roster")

config = {
    "Role": st.column_config.SelectboxColumn(
        "Role",
        options=ROLE_OPTIONS
    )
}

df_display = df.copy()

# =========================================
# PREPARE COLUMNS
# =========================================

for i, day in enumerate(DAYS):

    if shift_mode:

        # REMOVE TIME COLUMNS
        start_col = f"{day}: Start"
        end_col = f"{day}: End"

        cols_to_drop = []

        if start_col in df_display.columns:
            cols_to_drop.append(start_col)

        if end_col in df_display.columns:
            cols_to_drop.append(end_col)

        if cols_to_drop:
            df_display.drop(
                columns=cols_to_drop,
                inplace=True
            )

        # CREATE SHIFT COLUMN
        if day not in df_display.columns:
            df_display[day] = ""

        config[day] = (
            st.column_config.SelectboxColumn(
                f"({day_dates[i]})",
                options=SHIFT_OPTIONS
            )
        )

    else:

        # REMOVE SHIFT COLUMN
        if day in df_display.columns:

            df_display.drop(
                columns=[day],
                inplace=True
            )

        start_col = f"{day}: Start"
        end_col = f"{day}: End"

        # SUPPORT OLD "Finish"
        alt_end_col = f"{day}: Finish"

        if start_col not in df_display.columns:
            df_display[start_col] = ""

        if end_col not in df_display.columns:

            if alt_end_col in df_display.columns:

                df_display.rename(
                    columns={
                        alt_end_col: end_col
                    },
                    inplace=True
                )

            else:
                df_display[end_col] = ""

# =========================================
# SHIFT MODE
# =========================================

if shift_mode:

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True
    )

# =========================================
# NORMAL MODE (AGGRID)
# =========================================

else:

    # ORDER COLUMNS
    ordered_cols = ["Name", "Role"]

    for day in DAYS:

        ordered_cols.append(
            f"{day}: Start"
        )

        ordered_cols.append(
            f"{day}: End"
        )

    existing_cols = [
        c for c in ordered_cols
        if c in df_display.columns
    ]

    df_display = df_display[existing_cols]

    # =====================================
    # COLUMN DEFINITIONS
    # =====================================

    column_defs = [

        {
            "headerName": "Name",
            "field": "Name",
            "pinned": "left",
            "editable": True,
            "width": 180
        },

        {
            "headerName": "Role",
            "field": "Role",
            "editable": True,
            "width": 180,
            "cellEditor": "agSelectCellEditor",
            "cellEditorParams": {
                "values": ROLE_OPTIONS
            }
        }
    ]

    # GROUPED DAY HEADERS
    for i, day in enumerate(DAYS):

        day_label = day_dates[i]

        column_defs.append({

            "headerName": day_label,

            "children": [

                {
                    "headerName": "Start",
                    "field": f"{day}: Start",
                    "editable": True,
                    "width": 120,

                    "cellEditor": "agSelectCellEditor",

                    "cellEditorParams": {
                        "values": TIME_OPTIONS
                    }
                },

                {
                    "headerName": "End",
                    "field": f"{day}: End",
                    "editable": True,
                    "width": 120,

                    "cellEditor": "agSelectCellEditor",

                    "cellEditorParams": {
                        "values": TIME_OPTIONS
                    }
                }
            ]
        })

    # =====================================
    # GRID OPTIONS
    # =====================================

    grid_options = {

        "columnDefs": column_defs,

        "defaultColDef": {
            "resizable": True,
            "sortable": False
        },

        "headerHeight": 45,

        "groupHeaderHeight": 50,

        "rowHeight": 42,

        "animateRows": True
    }

    # =====================================
    # CUSTOM CSS
    # =====================================

    custom_css = {

        ".ag-header-group-cell-label": {
            "justify-content": "center",
            "font-weight": "bold",
            "font-size": "15px"
        },

        ".ag-header-cell-label": {
            "justify-content": "center",
            "font-size": "13px"
        },

        ".ag-cell": {
            "display": "flex",
            "align-items": "center"
        }
    }

    # =====================================
    # SHOW GRID
    # =====================================

    grid_response = AgGrid(
        df_display,
        gridOptions=grid_options,
        custom_css=custom_css,
        height=650,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        editable=True,
        theme="streamlit"
    )

    edited_df = pd.DataFrame(
        grid_response["data"]
    )

# =========================================
# 6. SAVE LOGIC (UNCHANGED)
# =========================================

if st.button(
    "💾 Save to Master Sheet",
    type="primary"
):

    ws = master_sheet.worksheet(
        "StaffSchedule"
    )

    full_data = pd.DataFrame(
        ws.get_all_records()
    )

    remaining_data = full_data[
        full_data["Branch"] !=
        st.session_state.selected_branch
    ]

    new_data = edited_df.copy()

    new_data["Branch"] = (
        st.session_state.selected_branch
    )

    new_data["Date"] = str(start_date)

    if "Name" in new_data.columns:

        new_data["Name"] = (
            new_data["Name"]
            .astype(str)
            .str.upper()
        )

    final_df = pd.concat(
        [remaining_data, new_data],
        ignore_index=True
    )

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
