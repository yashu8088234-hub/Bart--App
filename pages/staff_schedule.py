import streamlit as st
import pandas as pd
import gspread
import time

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
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
    "Staff","Supervisor","Acting Supervisor",
    "Team Leader","Acting Team Leader"
]

SHIFT_OPTIONS = [
    "Morning shift",
    "Mid shift",
    "Evening shift",
    "Night shift",
    "OFF",
    "➕ Custom Time"
]

# =========================================
# CACHE (NO API SPAM)
# =========================================

CACHE_TTL = 60

if "cached_df" not in st.session_state:
    st.session_state.cached_df = None
    st.session_state.last_fetch = 0


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
edit_mode = st.toggle("Edit Mode Only")

df = load_data()
df = df[df["Branch"] == st.session_state.selected_branch].copy()

existing_names = df["Name"].dropna().unique().tolist()

# =========================================
# CONFIG
# =========================================

config = {
    "Name": st.column_config.SelectboxColumn("Name", options=existing_names),
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS),
}

for d in DAYS:
    config[d] = st.column_config.SelectboxColumn(d, options=SHIFT_OPTIONS)

# =========================================
# EDIT MODE
# =========================================

if edit_mode:

    df_display = pd.DataFrame(columns=["Name", "Role"] + DAYS)

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True,
        key="editor"
    )

    # INLINE CUSTOM TIME (no popup)
    for i, row in edited_df.iterrows():
        for d in DAYS:

            if row.get(d) == "➕ Custom Time":

                st.info(f"⏰ Custom Time for {row.get('Name')} - {d}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    sh = st.selectbox("Start Hour", list(range(1, 13)), key=f"sh_{i}_{d}")
                    sm = st.selectbox("Min", ["00", "30"], key=f"sm_{i}_{d}")
                    sap = st.selectbox("AM/PM", ["AM", "PM"], key=f"sap_{i}_{d}")

                with col2:
                    eh = st.selectbox("End Hour", list(range(1, 13)), key=f"eh_{i}_{d}")
                    em = st.selectbox("Min", ["00", "30"], key=f"em_{i}_{d}")
                    eap = st.selectbox("AM/PM", ["AM", "PM"], key=f"eap_{i}_{d}")

                apply_all = st.checkbox("Apply to all days", key=f"all_{i}_{d}")

                if st.button("Apply", key=f"apply_{i}_{d}"):

                    value = f"{sh}:{sm} {sap} - {eh}:{em} {eap}"

                    idx = edited_df[
                        edited_df["Name"] == row["Name"]
                    ].index

                    if apply_all:
                        for day in DAYS:
                            edited_df.loc[idx, day] = value
                    else:
                        edited_df.loc[idx, d] = value

                    st.success("Applied!")
                    st.rerun()

# =========================================
# VIEW MODE (RESTORED AGGRID)
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

    for d in DAYS:
        column_defs.append({
            "headerName": d,
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
# SAVE
# =========================================

if edit_mode and st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")
    full = st.session_state.cached_df.copy()

    remaining = full[
        full["Branch"] != st.session_state.selected_branch
    ]

    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = datetime.now().strftime("%A %d %B")

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.upper()

    final = pd.concat([remaining, new_data], ignore_index=True)

    ws.clear()
    ws.update(
        [final.columns.tolist()] +
        final.fillna("").values.tolist()
    )

    st.session_state.cached_df = final
    st.session_state.last_fetch = time.time()

    st.success("✅ Saved Successfully!")
    st.rerun()

# =========================================
# BACK
# =================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
