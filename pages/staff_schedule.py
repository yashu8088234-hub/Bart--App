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
# 1. AUTH
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

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

start_date = st.date_input("Week Start Date")

shift_mode = st.toggle("Enable Shift-wise Mode")

day_dates = [
    (start_date + timedelta(days=i)).strftime("%a %d/%m")
    for i in range(7)
]

# =========================================
# 4. LOAD DATA (FIXED)
# =========================================

def get_filtered_data():

    ws = master_sheet.worksheet("StaffSchedule")
    all_data = ws.get_all_records()

    df = pd.DataFrame(all_data)

    if df.empty:
        return pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

    # ✅ SAFE CLEAN FILTER (THIS FIXES YOUR ISSUE)
    df["Branch"] = df["Branch"].astype(str).str.strip().str.lower()

    selected = str(st.session_state.selected_branch).strip().lower()

    filtered = df[df["Branch"] == selected].copy()

    return filtered.reset_index(drop=True)


df = get_filtered_data()

# =========================================
# 5. UI
# =========================================

st.subheader("Edit Roster")

if df.empty:
    st.warning("No data found for this branch.")
    st.stop()

config = {
    "Role": st.column_config.SelectboxColumn(
        "Role",
        options=ROLE_OPTIONS
    )
}

df_display = df.reset_index(drop=True).copy()

# =========================================
# SHIFT MODE
# =========================================

if shift_mode:

    for i, day in enumerate(DAYS):

        start_col = f"{day}: Start"
        end_col = f"{day}: End"

        cols_to_drop = []

        if start_col in df_display.columns:
            cols_to_drop.append(start_col)

        if end_col in df_display.columns:
            cols_to_drop.append(end_col)

        if cols_to_drop:
            df_display.drop(columns=cols_to_drop, inplace=True)

        if day not in df_display.columns:
            df_display[day] = ""

        config[day] = st.column_config.SelectboxColumn(
            f"({day_dates[i]})",
            options=SHIFT_OPTIONS
        )

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True
    )

# =========================================
# NORMAL MODE (AGGRID VIEW)
# =========================================

else:

    for day in DAYS:

        start_col = f"{day}: Start"
        end_col = f"{day}: End"
        alt_end_col = f"{day}: Finish"

        if start_col not in df_display.columns:
            df_display[start_col] = ""

        if end_col not in df_display.columns:
            if alt_end_col in df_display.columns:
                df_display.rename(
                    columns={alt_end_col: end_col},
                    inplace=True
                )
            else:
                df_display[end_col] = ""

        df_display[day] = (
            df_display[start_col].fillna("").astype(str)
            + " → " +
            df_display[end_col].fillna("").astype(str)
        )

    keep_cols = ["Name", "Role"] + DAYS

    df_display = df_display[
        [c for c in keep_cols if c in df_display.columns]
    ]

    column_defs = [
        {
            "headerName": "Name",
            "field": "Name",
            "pinned": "left",
            "editable": False,
            "width": 140
        },
        {
            "headerName": "Role",
            "field": "Role",
            "editable": False,
            "width": 150
        }
    ]

    for i, day in enumerate(DAYS):

        column_defs.append({
            "headerName": day_dates[i],
            "field": day,
            "editable": False,
            "width": 115
        })

    grid_options = {
        "columnDefs": column_defs,
        "defaultColDef": {
            "resizable": True,
            "sortable": False
        },
        "headerHeight": 36,
        "rowHeight": 32,
        "animateRows": True
    }

    custom_css = {
        ".ag-header-cell-label": {
            "justify-content": "center",
            "font-weight": "600",
            "font-size": "12px"
        },
        ".ag-cell": {
            "display": "flex",
            "align-items": "center",
            "font-size": "12px",
            "padding-left": "6px",
            "padding-right": "6px"
        },
        ".ag-root-wrapper": {
            "border-radius": "10px"
        }
    }

    AgGrid(
        df_display,
        gridOptions=grid_options,
        custom_css=custom_css,
        height=420,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        editable=False,
        theme="streamlit"
    )

    edited_df = df.copy()

# =========================================
# 6. SAVE
# =========================================

if st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")

    full_data = pd.DataFrame(ws.get_all_records())

    remaining_data = full_data[
        full_data["Branch"] != st.session_state.selected_branch
    ]

    new_data = edited_df.copy()

    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = str(start_date)

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.upper()

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
# 7. BACK
# =========================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
