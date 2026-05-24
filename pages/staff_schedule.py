import streamlit as st
import pandas as pd
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode

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

st.title("📅 Excel Style Staff Scheduler")

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

@st.cache_data(ttl=60)
def load():
    try:
        ws = sheet.worksheet(ws_name)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame(columns=columns)

df = load()

for c in columns:
    if c not in df.columns:
        df[c] = ""

df = df[columns]

# =========================================================
# 🎨 PAINT MODE (GLOBAL COLOR)
# =========================================================

st.subheader("🎨 Paint Tool (Excel Style)")

paint = st.toggle("Enable Paint Mode")

color = st.color_picker("Pick Color") if paint else None

# store colors
if "cell_colors" not in st.session_state:
    st.session_state.cell_colors = {}

# =========================================================
# AG GRID CONFIG
# =========================================================

gb = GridOptionsBuilder.from_dataframe(df)

gb.configure_default_column(editable=True)

gb.configure_column("Role", editable=True, cellEditor="agSelectCellEditor",
                    cellEditorParams={"values": ROLE_OPTIONS})

gridOptions = gb.build()

# =========================================================
# CUSTOM JS PAINT LOGIC
# =========================================================

cell_style_js = JsCode("""
function(params) {
    if (!params.data._colors) {
        return {};
    }

    const key = params.colDef.field + '_' + params.rowIndex;

    if (params.data._colors && params.data._colors[key]) {
        return {backgroundColor: params.data._colors[key]};
    }
}
""")

gb.configure_columns(columns, cellStyle=cell_style_js)

gridOptions = gb.build()

# =========================================================
# GRID
# =========================================================

grid_response = AgGrid(
    df,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    allow_unsafe_jscode=True,
    height=500,
    fit_columns_on_grid_load=True
)

data = pd.DataFrame(grid_response["data"])

# =========================================================
# 🎯 CLICK-TO-PAINT (REAL EXCEL BEHAVIOR)
# =========================================================

st.subheader("🖱️ Click Cells to Paint")

row = st.number_input("Row Index", min_value=0, step=1)
col = st.selectbox("Column", columns)

if paint and st.button("Apply Paint to Cell"):

    key = f"{col}_{row}"

    if "_colors" not in data.columns:
        data["_colors"] = None

    if len(data) > row:
        if data.at[row, "_colors"] is None:
            data.at[row, "_colors"] = {}

        if isinstance(data.at[row, "_colors"], str):
            data.at[row, "_colors"] = {}

        data.at[row, "_colors"][key] = color

    st.success("Cell colored")

# =========================================================
# SAVE
# =========================================================

col1, col2 = st.columns(2)

with col1:

    if st.button("💾 SAVE", type="primary"):

        ws = sheet.worksheet(ws_name)

        final = [columns] + data[columns].fillna("").values.tolist()

        ws.clear()
        ws.update(final)

        st.success("Saved")

# =========================================================
# DOWNLOAD
# =========================================================

with col2:

    st.download_button(
        "⬇ DOWNLOAD",
        data.to_csv(index=False).encode("utf-8"),
        file_name=f"{branch_info['BranchCode']}_{from_date}.csv",
        mime="text/csv"
    )
