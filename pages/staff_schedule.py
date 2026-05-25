import streamlit as st
import pandas as pd
import gspread
import time

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from st_aggrid import AgGrid

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# =========================================
# AUTH
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

client = gspread.authorize(creds)
master_sheet = client.open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

# =========================================
# CONFIG
# =========================================

DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

ROLE_OPTIONS = [
    "Team-Member","Acting_Team_Leader","Team_Leader","Acting_Supervisor","Supervisor","Branch_Manager"
]

# REMOVED STANDARD SHIFTS - KEEPING ONLY CUSTOM TIME
SHIFT_OPTIONS = [
    "➕ Custom Time"
]

# =========================================
# CACHE & STATE INITIALIZATION
# =========================================

CACHE_TTL = 60

if "cached_df" not in st.session_state:
    st.session_state.cached_df = None
    st.session_state.last_fetch = 0

if "pending_update" not in st.session_state:
    st.session_state.pending_update = None


def load_data():
    now = time.time()

    if (
        st.session_state.cached_df is None
        or now - st.session_state.last_fetch > CACHE_TTL
    ):
        ws = master_sheet.worksheet("StaffSchedule")
        data = ws.get_all_records()
        df = pd.DataFrame(data) if data else pd.DataFrame()

        if df.empty:
            df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

        st.session_state.cached_df = df
        st.session_state.last_fetch = now

    return st.session_state.cached_df


# =========================================
# UI
# =========================================

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

# =========================================
# WEEK SELECTOR
# =========================================

selected_date = st.date_input(
    "📅 Select Any Date In Week",
    value=datetime.today(),
    key="week_selector"
)

# =========================================
# AUTO CONVERT TO SUNDAY
# =========================================

days_from_sunday = (selected_date.weekday() + 1) % 7

week_start = selected_date - timedelta(days=days_from_sunday)

week_end = week_start + timedelta(days=6)

st.caption(
    f"Week: {week_start.strftime('%d %b %Y')} → {week_end.strftime('%d %b %Y')}"
)

edit_mode = st.toggle("Edit Mode Only")

# =========================================
# GENERATE DYNAMIC DAY LABELS
# =========================================

day_labels = {}
for idx, day_name in enumerate(DAYS):
    day_date = week_start + timedelta(days=idx)
    day_labels[day_name] = f"{day_name} ({day_date.strftime('%d %b')})"

# =========================================
# LOAD DATA
# =========================================

all_data_df = load_data()

if not all_data_df.empty and "Branch" in all_data_df.columns:
    df = all_data_df[
        all_data_df["Branch"] == st.session_state.selected_branch
    ].copy()
else:
    df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

# =========================================
# NAME LIST
# =========================================

branch_names = []

if not all_data_df.empty and "Name" in all_data_df.columns:

    branch_mask = (
        all_data_df["Branch"].astype(str).str.strip()
        == str(st.session_state.selected_branch).strip()
    )

    filtered_names = (
        all_data_df[branch_mask]["Name"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    branch_names = sorted(filtered_names.unique().tolist())

if not branch_names and not all_data_df.empty and "Name" in all_data_df.columns:
    branch_names = sorted(
        all_data_df["Name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

# =========================================
# CONFIG FOR EDITOR
# =========================================

config = {
    "Name": st.column_config.SelectboxColumn(
        "Name",
        options=branch_names,
        required=True
    ),

    "Role": st.column_config.SelectboxColumn(
        "Role",
        options=ROLE_OPTIONS
    ),
}

for d in DAYS:
    config[d] = st.column_config.SelectboxColumn(
        day_labels[d],
        options=SHIFT_OPTIONS
    )

# =========================================
# EDIT MODE
# =========================================

if edit_mode:

    if not df.empty:

        roster_df = (
            df[["Name", "Role"]]
            .dropna(subset=["Name"])
            .drop_duplicates()
        )

        roster_df["Name"] = (
            roster_df["Name"]
            .astype(str)
            .str.strip()
        )

        roster_df["Role"] = (
            roster_df["Role"]
            .astype(str)
            .str.strip()
        )

        df_display = pd.DataFrame(columns=["Name", "Role"] + DAYS)

        df_display["Name"] = roster_df["Name"].values
        df_display["Role"] = roster_df["Role"].values

    else:
        df_display = pd.DataFrame(columns=["Name", "Role"] + DAYS)

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True,
        key="editor"
    )

    # =========================================
    # CUSTOM TIME UI
    # =========================================

    for i, row in edited_df.iterrows():

        for d in DAYS:

            if row.get(d) == "➕ Custom Time":

                st.info(f"⏰ Custom Time for {row.get('Name')} - {day_labels[d]}")

                col1, col2 = st.columns(2)

                with col1:

                    st.markdown("### Start Time")

                    sh = st.selectbox(
                        "Hour",
                        list(range(1, 13)),
                        key=f"sh_{i}_{d}"
                    )

                    sap = st.selectbox(
                        "AM/PM",
                        ["AM", "PM"],
                        key=f"sap_{i}_{d}"
                    )

                with col2:

                    st.markdown("### End Time")

                    eh = st.selectbox(
                        "Hour",
                        list(range(1, 13)),
                        key=f"eh_{i}_{d}"
                    )

                    eap = st.selectbox(
                        "AM/PM",
                        ["AM", "PM"],
                        key=f"eap_{i}_{d}"
                    )

                apply_all = st.checkbox(
                    "Apply to all days",
                    key=f"all_{i}_{d}"
                )

                if st.button("Apply", key=f"apply_{i}_{d}"):

                    value = f"{sh} {sap} - {eh} {eap}"

                    st.session_state.pending_update = {
                        "row": i,
                        "day": d,
                        "value": value,
                        "apply_all": apply_all
                    }

                    st.rerun()

    # =========================================
    # APPLY AFTER RERUN
    # =========================================

    if st.session_state.pending_update:

        upd = st.session_state.pending_update

        i = upd["row"]
        d = upd["day"]
        value = upd["value"]
        apply_all = upd["apply_all"]

        if apply_all:

            for day in DAYS:
                edited_df.loc[i, day] = value

        else:
            edited_df.loc[i, d] = value

        st.session_state.pending_update = None

        st.success("✅ Custom time applied successfully!")
        st.rerun()

# =========================================
# VIEW MODE
# =========================================

else:

    df_display = df.copy()

    ordered_cols = ["Name", "Role", "Date"] + DAYS

    df_display = df_display[
        [c for c in ordered_cols if c in df_display.columns]
    ]

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
            "width": 150
        },

        {
            "headerName": "Date",
            "field": "Date",
            "width": 180
        },
    ]

    for d in DAYS:

        column_defs.append({
            "headerName": day_labels[d],
            "field": d,
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
    }

    AgGrid(
        df_display,
        gridOptions=grid_options,
        height=500,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        theme="streamlit"
    )

# =========================================
# SAVE TO GOOGLE SHEETS
# =========================================

if edit_mode and st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")

    full_df = st.session_state.cached_df.copy()

    new_data = edited_df.copy()

    new_data["Branch"] = st.session_state.selected_branch

    new_data["Date"] = week_start.strftime("%d-%m-%Y")

    if "Name" in new_data.columns:
        new_data["Name"] = (
            new_data["Name"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    if "Role" in new_data.columns:
        new_data["Role"] = (
            new_data["Role"]
            .astype(str)
            .str.strip()
        )

    if "Name" in full_df.columns:
        full_df["Name"] = (
            full_df["Name"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    if "Role" in full_df.columns:
        full_df["Role"] = (
            full_df["Role"]
            .astype(str)
            .str.strip()
        )

    other_branches_df = full_df[
        full_df["Branch"] != st.session_state.selected_branch
    ].copy()

    current_branch_original_df = full_df[
        full_df["Branch"] == st.session_state.selected_branch
    ].copy()

    for _, row in new_data.iterrows():

        emp_name = row["Name"]
        emp_role = row["Role"]

        match_mask = (
            (current_branch_original_df["Name"] == emp_name)
            &
            (current_branch_original_df["Role"] == emp_role)
        )

        if match_mask.any():

            for col in DAYS:

                if col in row:
                    current_branch_original_df.loc[
                        match_mask,
                        col
                    ] = row[col]

        else:

            current_branch_original_df = pd.concat(
                [
                    current_branch_original_df,
                    pd.DataFrame([row])
                ],
                ignore_index=True
            )

    final = pd.concat(
        [other_branches_df, current_branch_original_df],
        ignore_index=True
    )

    ws.clear()

    ws.update(
        [final.columns.tolist()]
        + final.fillna("").values.tolist()
    )

    st.session_state.cached_df = final
    st.session_state.last_fetch = time.time()

    if "editor" in st.session_state:
        del st.session_state["editor"]

    st.success("✅ Saved and merged successfully! Input schedules cleared.")
    st.rerun()

# =========================================
# BACK BUTTON
# =========================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
