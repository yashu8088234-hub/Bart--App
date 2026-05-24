import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode
)

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Excel Scheduler")

if "branch_info" not in st.session_state:
    st.warning("Session expired")
    st.stop()

branch_info = st.session_state.branch_info

# =========================================================
# GOOGLE SHEETS
# =========================================================

@st.cache_resource
def connect():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["GOOGLE_CREDS_JSON"],
        ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

client = connect()
sheet = client.open_by_key(branch_info["SheetID"])

# =========================================================
# DATA
# =========================================================

st.title("📅 Excel Style Weekly Scheduler")

from_date = st.date_input("Week Start", datetime.date.today())
ws_name = f"Weekly_{from_date}"

days = ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"]

columns = ["EmployeeName","Role",*days,"Notes"]

ROLE_OPTIONS = [
    "Staff",
    "Supervisor",
    "Acting Supervisor",
    "Team Leader",
    "Acting Team Leader"
]

# =========================================================
# LOAD SHEET
# =========================================================

@st.cache_data(ttl=60)
def load():
    try:
        ws = sheet.worksheet(ws_name)
        df = pd.DataFrame(ws.get_all_records())
    except:
        df = pd.DataFrame(columns=columns)

    for c in columns:
        if c not in df.columns:
            df[c] = ""

    return df[columns]

df = load()

# =========================================================
# 🎨 PAINT MODE STATE
# =========================================================

st.subheader("🎨 Paint Tool")

paint_mode = st.toggle("Enable Paint Mode")

paint_color = None
if paint_mode:
    paint_color = st.color_picker("Pick Color")

if "cell_colors" not in st.session_state:
    st.session_state.cell_colors = {}

# =========================================================
# AG GRID (FIXED BUILD)
# =========================================================

gb = GridOptionsBuilder.from_dataframe(df)

gb.configure_default_column(editable=True, resizable=True)

# Role dropdown
gb.configure_column(
    "Role",
    editable=True,
    cellEditor="agSelectCellEditor",
    cellEditorParams={"values": ROLE_OPTIONS}
)

# IMPORTANT FIX: DO NOT add JS column overrides before build()
gridOptions = gb.build()

# =========================================================
# GRID RENDER
# =========================================================

grid_response = AgGrid(
    df,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    allow_unsafe_jscode=True,
    height=500
)

data = pd.DataFrame(grid_response["data"])

# =========================================================
# SIMPLE PAINT SYSTEM (NO JS BUGS)
# =========================================================

st.subheader("🖱️ Click-to-Paint Cell")

col1, col2 = st.columns(2)

with col1:
    row = st.number_input("Row", min_value=0, step=1)

with col2:
    col = st.selectbox("Column", columns)

if paint_mode and st.button("Apply Color"):

    key = f"{row}_{col}"
    st.session_state.cell_colors[key] = paint_color

    st.success("Cell colored")

# =========================================================
# APPLY COLORS (SAFE METHOD)
# =========================================================

def style_df(df):

    def style_row(row):

        styles = [""] * len(row)

        for i, c in enumerate(df.columns):

            key = f"{row.name}_{c}"

            if key in st.session_state.cell_colors:
                styles[i] = f"background-color: {st.session_state.cell_colors[key]}"

        return styles

    return df.style.apply(style_row, axis=1)

st.dataframe(style_df(data), use_container_width=True)

# =========================================================
# SAVE
# =========================================================

c1, c2 = st.columns(2)

with c1:

    if st.button("💾 SAVE", type="primary"):

        ws = sheet.worksheet(ws_name)

        final = [columns] + data.fillna("").values.tolist()

        ws.clear()
        ws.update(final)

        st.success("Saved successfully")

# =========================================================
# DOWNLOAD
# =========================================================

with c2:

    st.download_button(
        "⬇ DOWNLOAD",
        data.to_csv(index=False).encode("utf-8"),
        file_name=f"{branch_info['BranchCode']}_{from_date}.csv",
        mime="text/csv"
    )
