import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

from st_aggrid import AgGrid

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# ==============================
# AUTH
# ==============================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
)

master_sheet = gspread.authorize(creds).open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

# ==============================
DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

SHIFT_OPTIONS = [
    "Morning shift",
    "Mid shift",
    "Evening shift",
    "Night shift",
    "OFF",
    "Custom Time"
]

ROLE_OPTIONS = [
    "Staff","Supervisor","Acting Supervisor","Team Leader","Acting Team Leader"
]

# ==============================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

edit_mode = st.toggle("Edit Mode Only")

# ==============================
def get_data():
    ws = master_sheet.worksheet("StaffSchedule")
    df = pd.DataFrame(ws.get_all_records())
    if df.empty:
        df = pd.DataFrame(columns=["Branch","Date","Name","Role"] + DAYS)
    return df[df["Branch"] == st.session_state.selected_branch]

df = get_data()

existing_names = df["Name"].dropna().unique().tolist()

# ==============================
# SESSION STATE FOR CELL EDIT
# ==============================
if "edit_cell" not in st.session_state:
    st.session_state.edit_cell = None

# ==============================
# EDIT MODE (WHATSAPP STYLE)
# ==============================
if edit_mode:

    df_display = pd.DataFrame(columns=["Name","Role"] + DAYS)

    edited_df = st.data_editor(
        df_display,
        num_rows="dynamic",
        use_container_width=True
    )

    # ==============================
    # CELL SELECTOR (SIMULATED CLICK)
    # ==============================
    st.markdown("### ✏️ Tap a Cell to Edit")

    row_idx = st.number_input("Row", min_value=0, step=1)
    day = st.selectbox("Day", DAYS)

    shift = st.selectbox("Shift Type", SHIFT_OPTIONS)

    start_time = None
    end_time = None

    if shift == "Custom Time":

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.time_input("Start Time")

        with col2:
            end_time = st.time_input("End Time")

    if st.button("Apply Change"):

        if row_idx < len(edited_df):

            if shift == "Custom Time":
                value = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            else:
                value = shift

            edited_df.at[row_idx, day] = value

            st.success("Updated instantly ✔️")

# ==============================
# VIEW MODE (UNCHANGED)
# ==============================
else:

    df_display = df.copy()

    column_defs = [
        {"headerName":"Name","field":"Name","pinned":"left"},
        {"headerName":"Role","field":"Role"},
        {"headerName":"Date","field":"Date"}
    ]

    for d in DAYS:
        column_defs.append({"headerName":d,"field":d})

    grid_response = AgGrid(
        df_display,
        gridOptions={
            "columnDefs": column_defs,
            "defaultColDef": {"resizable": True},
            "rowHeight": 32,
            "domLayout": "normal"
        },
        height=500,
        theme="streamlit"
    )

# ==============================
# SAVE
# ==============================
if edit_mode and st.button("💾 Save"):

    ws = master_sheet.worksheet("StaffSchedule")

    full = pd.DataFrame(ws.get_all_records())

    remaining = full[full["Branch"] != st.session_state.selected_branch]

    new = edited_df.copy()
    new["Branch"] = st.session_state.selected_branch
    new["Date"] = datetime.now().strftime("%A %d %B")

    final = pd.concat([remaining, new], ignore_index=True)

    ws.clear()
    ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

    st.success("Saved ✔️")
    st.rerun()
