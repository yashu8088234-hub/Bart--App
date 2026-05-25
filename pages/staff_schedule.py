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

# Kept ONLY custom time configuration options
SHIFT_OPTIONS = [
    "", 
    "➕ Custom Time"
]

# =========================================
# CACHE
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
# DIALOG MODAL FOR CUSTOM TIME
# =========================================

@st.dialog("⏰ Set Custom Time")
def custom_time_modal(row_idx, day_name, current_name):
    st.write(f"Setting hours for **{current_name if current_name else f'Row {row_idx}'}** on **{day_name}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Start Time")
        sh = st.selectbox("Hour", list(range(1, 13)), index=8, key="start_hour")
        sm = st.selectbox("Minute", ["00", "15", "30", "45"], key="start_min")
        sap = st.selectbox("AM/PM", ["AM", "PM"], index=0, key="start_ap")
        
    with col2:
        st.subheader("End Time")
        eh = st.selectbox("Hour", list(range(1, 13)), index=4, key="end_hour")
        em = st.selectbox("Minute", ["00", "15", "30", "45"], key="end_min")
        eap = st.selectbox("AM/PM", ["AM", "PM"], index=1, key="end_ap")
        
    apply_all = st.checkbox("Apply this time to all days for this row", key="apply_all_days")
    
    if st.button("Apply Time", type="primary", use_container_width=True):
        formatted_value = f"{sh}:{sm} {sap} - {eh}:{em} {eap}"
        
        # Directly update the editor widget state session engine to bypass caching bugs
        if "editor_widget" in st.session_state:
            if "edited_rows" not in st.session_state["editor_widget"]:
                st.session_state["editor_widget"]["edited_rows"] = {}
            if row_idx not in st.session_state["editor_widget"]["edited_rows"]:
                st.session_state["editor_widget"]["edited_rows"][row_idx] = {}
                
            if apply_all:
                for day in DAYS:
                    st.session_state["editor_widget"]["edited_rows"][row_idx][day] = formatted_value
            else:
                st.session_state["editor_widget"]["edited_rows"][row_idx][day_name] = formatted_value
                
        st.rerun()


# =========================================
# UI
# =========================================

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")
edit_mode = st.toggle("Edit Mode Only")

# Fetch fresh copy of master schedule 
master_df = load_data()

# DYNAMIC NAME FINDER: Scans complete column matching current active branch context
if not master_df.empty and "Branch" in master_df.columns:
    branch_mask = master_df["Branch"].astype(str).str.strip() == str(st.session_state.selected_branch).strip()
    existing_names = master_df[branch_mask]["Name"].dropna().unique().tolist()
else:
    existing_names = []

# Filter static dataset for view-mode framework
df = master_df[master_df["Branch"] == st.session_state.selected_branch].copy()

# =========================================
# CONFIG FOR EDITOR
# =========================================

config = {
    "Name": st.column_config.SelectboxColumn("Name", options=existing_names, required=True),
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS),
}

for d in DAYS:
    config[d] = st.column_config.SelectboxColumn(d, options=SHIFT_OPTIONS)

# =========================================
# EDIT MODE
# =========================================

if edit_mode:
    # Build or hold draft tracking dataframe parameters
    if "editor_base_df" not in st.session_state:
        if not df.empty:
            st.session_state.editor_base_df = df[["Name", "Role"] + DAYS].copy().reset_index(drop=True)
        else:
            st.session_state.editor_base_df = pd.DataFrame(columns=["Name", "Role"] + DAYS)

    # Render data editor (Hiding index column 0, 1, 2 layout completely)
    edited_df = st.data_editor(
        st.session_state.editor_base_df,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_widget"
    )

    # Monitor interactive data flow triggers for "➕ Custom Time" selection
    trigger_modal = False
    target_row = None
    target_day = None
    target_name = None

    for i, row in edited_df.iterrows():
        for d in DAYS:
            if row.get(d) == "➕ Custom Time":
                # Instantly reset field cell assignment strings to clear running loop triggers
                if "editor_widget" in st.session_state and i in st.session_state["editor_widget"]["edited_rows"]:
                    st.session_state["editor_widget"]["edited_rows"][i][d] = ""
                
                trigger_modal = True
                target_row = i
                target_day = d
                target_name = row.get("Name")
                break
        if trigger_modal:
            break

    if trigger_modal:
        custom_time_modal(target_row, target_day, target_name)
        
    if st.button("🔄 Reset Editor Window"):
        if "editor_base_df" in st.session_state:
            del st.session_state.editor_base_df
        st.rerun()

# =========================================
# VIEW MODE
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
# SAVE TO GOOGLE SHEETS
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
    ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

    st.session_state.cached_df = final
    st.session_state.last_fetch = time.time()
    
    # Destruct current base cache definitions to force fresh pull updates
    if "editor_base_df" in st.session_state:
        del st.session_state.editor_base_df

    st.success("✅ Saved Successfully!")
    st.rerun()

# =========================================
# BACK BUTTON
# =========================================

if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")
