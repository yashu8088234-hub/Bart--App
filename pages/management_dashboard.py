import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
from gspread.exceptions import APIError
import time

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# 🔥 LIVE TIMER
# =========================================================
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=10000, key="live_timer")

# =========================================================
# API ERROR SCREEN
# =========================================================
def show_api_error(e):
    st.error("API Error Occurred")
    st.error(str(e))
    st.stop()

# =========================================================
# GOOGLE AUTH
# =========================================================
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )
    return gspread.authorize(creds)

try:
    client = get_client()
except Exception as e:
    show_api_error(e)

# =========================================================
# MASTER SHEET ID
# =========================================================
MASTER_ID = "1KYNCls3HWWj_DFY2Q27JRDRJpolSVcxiSH7f4rNDOlM"

# =========================================================
# SAFE SHEET LOAD (FIXED)
# =========================================================
@st.cache_data(ttl=300)
def load_data():
    sheet = client.open_by_key(MASTER_ID).worksheet("STOCKS")

    # IMPORTANT FIX: use get_all_values (not get_all_records)
    data = sheet.get_all_values()

    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    # FIX DATE COLUMN
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    return df

# =========================================================
# LOAD DATA
# =========================================================
try:
    df = load_data()
except APIError as e:
    show_api_error(e)
except Exception as e:
    show_api_error(e)

if df.empty:
    st.warning("No Data Found")
    st.stop()

# =========================================================
# REFRESH CONTROL (UNCHANGED)
# =========================================================
if "last_force_refresh" not in st.session_state:
    st.session_state.last_force_refresh = 0

REFRESH_COOLDOWN = 40

now = time.time()
remaining = REFRESH_COOLDOWN - (
    now - st.session_state.last_force_refresh
)

remaining = max(0, int(remaining))
can_force_refresh = remaining <= 0

# =========================================================
# FILTERS (DATE FIXED)
# =========================================================
st.sidebar.header("🔎 Filters")

dates = sorted(df["Date"].dropna().unique())
selected_date = st.sidebar.selectbox("Select Date", dates)

items = ["All"] + sorted(df["Item"].dropna().unique().tolist())
selected_item = st.sidebar.selectbox("Select Item", items)

skus = ["All"] + sorted(df["SKU"].dropna().unique().tolist())
selected_sku = st.sidebar.selectbox("Select SKU", skus)

# =========================================================
# BUTTONS (UNCHANGED)
# =========================================================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Date Only"):
        st.rerun()

with col2:

    refresh_text = (
        "🔴 Refresh Data From Sheets"
        if can_force_refresh
        else f"⏳ Wait {remaining} sec"
    )

    if st.button(refresh_text, disabled=not can_force_refresh):

        with st.spinner("Refreshing..."):

            try:
                st.cache_data.clear()
                st.session_state.last_force_refresh = time.time()
                st.success("Updated")
                st.rerun()

            except Exception as e:
                st.error(e)
                st.stop()

with col3:
    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# TIMER DISPLAY
# =========================================================
st.info(f"⏳ Refresh available in: {remaining} seconds")

# =========================================================
# FILTER LOGIC (FIXED FOR MASTER FORMAT)
# =========================================================
filtered = df[df["Date"] == selected_date]

if selected_item != "All":
    filtered = filtered[filtered["Item"] == selected_item]

if selected_sku != "All":
    filtered = filtered[filtered["SKU"] == selected_sku]

# =========================================================
# PROCESS STOCK (UNCHANGED STRUCTURE)
# =========================================================
daily_df = filtered.copy()
weekly_df = pd.DataFrame()  # kept for compatibility with your UI

# =========================================================
# GRID FUNCTION (UNCHANGED)
# =========================================================
def get_width(series, min_width):

    try:
        series = series.fillna("").astype(str)
        max_len = series.map(len).max()
        return max(int(max_len * 5 + 25), min_width)

    except:
        return min_width

def render_grid(df, title):

    st.subheader(title)

    if df is None or df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item", pinned="left", minWidth=140)
    gb.configure_column("SKU", pinned="left", minWidth=80)
    gb.configure_column("UOM", pinned="left", minWidth=70)

    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_grid_options(domLayout='normal', suppressHorizontalScroll=False)

    AgGrid(df, gridOptions=gb.build(), theme="streamlit", key=title)

# =========================================================
# DISPLAY (UNCHANGED UI)
# =========================================================
render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# EXCEL EXPORT (UNCHANGED)
# =========================================================
def create_excel(daily_df, weekly_df):

    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Dashboard"

    def write_section(title, df, start_row):

        rows = list(dataframe_to_rows(df, index=False, header=True))

        if not rows:
            return start_row + 2

        total_cols = len(rows[0])

        ws.merge_cells(
            start_row=start_row,
            start_column=1,
            end_row=start_row,
            end_column=total_cols
        )

        ws.cell(row=start_row, column=1, value=title).font = Font(bold=True)

        r0 = start_row + 2

        for r_i, row in enumerate(rows):
            for c_i, val in enumerate(row, 1):
                ws.cell(row=r0 + r_i, column=c_i, value=val)

        return r0 + len(rows) + 3

    next_row = write_section("DAILY STOCK", daily_df, 1)
    write_section("WEEKLY STOCK", weekly_df, next_row)

    wb.save(output)
    output.seek(0)
    return output

excel_file = create_excel(daily_df, weekly_df)

st.download_button(
    "📥 Download Stock Report",
    excel_file,
    file_name="stock_report.xlsx"
)
