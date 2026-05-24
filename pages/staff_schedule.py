import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

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
    "Sunday","Monday","Tuesday","Wednesday",
    "Thursday","Friday","Saturday"
]

ROLE_OPTIONS = [
    "Staff","Supervisor","Acting Supervisor",
    "Team Leader","Acting Team Leader"
]

SHIFT_OPTIONS = [
    "Morning shift",
    "Mid shift",
    "Evening shift",
    "Night shift",
    "OFF",
    "Custom Time"
]

# =========================================
# 3. UI
# =========================================

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

edit_mode = st.toggle("Edit Mode Only")

# =========================================
# 4. LOAD DATA
# =========================================

def get_filtered_data():
    ws = master_sheet.worksheet("StaffSchedule")
    all_data = ws.get_all_records()

    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

    return df[df["Branch"] == st.session_state.selected_branch]


df = get_filtered_data()

# =========================================
# 5. EXISTING NAMES (AUTOCOMPLETE)
# =========================================

existing_names = df[
    df["Branch"] == st.session_state.selected_branch
]["Name"].dropna().unique().tolist()

# =========================================
# 6. CONFIG
# =========================================

config = {
    "Name": st.column_config.SelectboxColumn(
        "Name",
        options=existing_names,
        help="Select or type employee name"
    ),
    "Role": st.column_config.SelectboxColumn(
        "Role",
        options=ROLE_OPTIONS
    )
}

for day in DAYS:
    config[day] = st.column_config.SelectboxColumn(
        day,
        options=SHIFT_OPTIONS
    )

# =========================================
# 7. EDIT MODE (EMPTY INPUT TABLE)
# =========================================

if edit_mode:

    df_display = pd.DataFrame(
        columns=["Name", "Role"] + DAYS
    )

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True
    )

    # =========================================
    # CUSTOM TIME PICKER LOGIC
    # =========================================

    for i, row in edited_df.iterrows():
        for day in DAYS:

            if row[day] == "Custom Time":

                st.markdown(f"### ⏰ {row['Name']} - {day}")

                start = st.time_input(
                    f"Start Time ({row['Name']} - {day})",
                    key=f"{i}_{day}_start"
                )

                end = st.time_input(
                    f"End Time ({row['Name']} - {day})",
                    key=f"{i}_{day}_end"
                )

                edited_df.at[i, day] = (
                    f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
                )

# =========================================
# 8. VIEW MODE (AGGRID)
# =========================================

else:

    df_display = df.copy()

    ordered_cols = ["Name", "Role", "Date"] + DAYS
    df_display = df_display[[c for c in ordered_cols if c in df_display.columns]]

    column_defs = [
        {"headerName": "Name", "field": "Name", "pinned": "left", "width": 180},
        {"headerName": "Role", "field": "Role", "width": 150},
        {"headerName": "Date", "field": "Date", "width": 180},
    ]

    for day in DAYS:
        column_defs.append({
            "headerName": day,
            "field": day,
            "width": 140
        })

    grid_options = {
        "columnDefs": column_defs,
        "defaultColDef": {
            "resizable": True,
            "sortable": False,
            "cellStyle": {"textAlign": "left"}
        },
        "headerHeight": 35,
        "rowHeight": 32,
        "domLayout": "normal"
    }

    custom_css = {
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
        height=8 * 42 + 90,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        editable=False,
        theme="streamlit"
    )

    edited_df = pd.DataFrame(grid_response["data"])

# =========================================
# 9. SAVE TO SHEET
# =========================================

if edit_mode:

    if st.button("💾 Save to Master Sheet", type="primary"):

        ws = master_sheet.worksheet("StaffSchedule")

        full_data = pd.DataFrame(ws.get_all_records())

        remaining_data = full_data[
            full_data["Branch"] != st.session_state.selected_branch
        ]

        new_data = edited_df.copy()

        new_data["Branch"] = st.session_state.selected_branch
        new_data["Date"] = datetime.now().strftime("%A %d %B")

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
# 10. BACK
# =========================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
