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
# CACHE
# =========================================

# =========================================
# CACHE & STATE INITIALIZATION
# =========================================

CACHE_TTL = 60

if "cached_df" not in st.session_state:
    st.session_state.cached_df = None
    st.session_state.last_fetch = 0

# FIX: Initialize pending_update here so it always exists globally!
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
edit_mode = st.toggle("Edit Mode Only")

# 1. Load the raw data from Google Sheets
all_data_df = load_data()

# 2. Filter the main display dataframe for this branch
if not all_data_df.empty and "Branch" in all_data_df.columns:
    df = all_data_df[all_data_df["Branch"] == st.session_state.selected_branch].copy()
else:
    df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

# 3. Get ALL names from the entire column matching this branch (Case-Insensitive Fix!)
branch_names = []
if not all_data_df.empty and "Name" in all_data_df.columns:
    # Filter by branch safely
    branch_mask = all_data_df["Branch"].astype(str).str.strip() == str(st.session_state.selected_branch).strip()
    filtered_names = all_data_df[branch_mask]["Name"].dropna().astype(str).str.strip()
    
    # Keep names exactly as they are in the sheet (lowercase/mixed) but remove duplicates
    branch_names = sorted(filtered_names.unique().tolist())

# Fallback just in case the branch list is empty
if not branch_names and not all_data_df.empty and "Name" in all_data_df.columns:
    branch_names = sorted(all_data_df["Name"].dropna().astype(str).unique().tolist())

# =========================================
# CONFIG FOR EDITOR
# =========================================

config = {
    # This now contains the entire filtered column list regardless of casing!
    "Name": st.column_config.SelectboxColumn("Name", options=branch_names, required=True),
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS),
}

for d in DAYS:
    config[d] = st.column_config.SelectboxColumn(d, options=SHIFT_OPTIONS)
# =========================================
# EDIT MODE
# =========================================

if edit_mode:
    # 💡 FIX: Fetch unique combinations of BOTH Name and Role for this branch
    if not df.empty:
        # Extract unique Name + Role pairs and drop any empty rows
        roster_df = df[["Name", "Role"]].dropna(subset=["Name"]).drop_duplicates()
        
        # Format the strings to maintain neatness
        roster_df["Name"] = roster_df["Name"].astype(str).str.strip()
        roster_df["Role"] = roster_df["Role"].astype(str).str.strip()
        
        # Reconstruct the empty week columns side-by-side with your fixed positions
        df_display = pd.DataFrame(columns=["Name", "Role"] + DAYS)
        df_display["Name"] = roster_df["Name"].values
        df_display["Role"] = roster_df["Role"].values
    else:
        # Fallback template if no data exists at all yet
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

                st.info(f"⏰ Custom Time for {row.get('Name')} - {d}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Start Time")
                    sh = st.selectbox("Hour", list(range(1, 13)), key=f"sh_{i}_{d}")
                    sap = st.selectbox("AM/PM", ["AM", "PM"], key=f"sap_{i}_{d}")

                with col2:
                    st.markdown("### End Time")
                    eh = st.selectbox("Hour", list(range(1, 13)), key=f"eh_{i}_{d}")
                    eap = st.selectbox("AM/PM", ["AM", "PM"], key=f"eap_{i}_{d}")

                apply_all = st.checkbox("Apply to all days", key=f"all_{i}_{d}")

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
    
    # 1. Grab a fresh deep copy of the spreadsheet cache
    full_df = st.session_state.cached_df.copy()

    # 2. Prepare your newly edited data
    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = datetime.now().strftime("%A %d %B")

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.strip().str.upper()
    if "Role" in new_data.columns:
        new_data["Role"] = new_data["Role"].astype(str).str.strip()
    
    if "Name" in full_df.columns:
        full_df["Name"] = full_df["Name"].astype(str).str.strip().str.upper()
    if "Role" in full_df.columns:
        full_df["Role"] = full_df["Role"].astype(str).str.strip()

    # 3. Pull untouched branches and isolate current branch positions
    other_branches_df = full_df[full_df["Branch"] != st.session_state.selected_branch].copy()
    current_branch_original_df = full_df[full_df["Branch"] == st.session_state.selected_branch].copy()

    # 4. Merge changes cell-by-cell without modifying underlying structures
    for _, row in new_data.iterrows():
        emp_name = row["Name"]
        emp_role = row["Role"]
        
        # Match using BOTH fixed identifiers
        match_mask = (current_branch_original_df["Name"] == emp_name) & (current_branch_original_df["Role"] == emp_role)
        
        if match_mask.any():
            # Overwrite only the edited day schedules
            for col in DAYS:
                if col in row:
                    current_branch_original_df.loc[match_mask, col] = row[col]
        else:
            # Append as a fresh dynamic row if completely unique configuration
            current_branch_original_df = pd.concat([current_branch_original_df, pd.DataFrame([row])], ignore_index=True)

    # Recombine database pools
    final = pd.concat([other_branches_df, current_branch_original_df], ignore_index=True)

    # 5. Push up to cloud
    ws.clear()
    ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

    # 6. Clear local runtime memory to force columns 3+ to wipe out entirely in the UI
    st.session_state.cached_df = final
    st.session_state.last_fetch = time.time()
    
    # 💡 RESET WIDGET STATE: Wipes the internal Streamlit data editor memory for a pristine clean
    if "editor" in st.session_state:
        del st.session_state["editor"]

    st.success("✅ Saved and merged successfully! Input schedules cleared.")
    st.rerun()
# =========================================
# BACK BUTTON
# =========================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
