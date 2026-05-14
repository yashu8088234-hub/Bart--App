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
from streamlit_autorefresh import st_autorefresh

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# UI AUTO REFRESH (10 seconds ONLY UI rerun)
# =========================================================

st_autorefresh(interval=10000, key="ui_refresh")

# =========================================================
# AUTO CACHE CLEAR (EVERY 2 MINUTES)
# =========================================================

if "last_cache_clear" not in st.session_state:
    st.session_state.last_cache_clear = time.time()

AUTO_CLEAR_INTERVAL = 120  # 2 minutes

if time.time() - st.session_state.last_cache_clear > AUTO_CLEAR_INTERVAL:
    st.cache_data.clear()
    st.session_state.last_cache_clear = time.time()

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
# BRANCHES
# =========================================================

@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

try:
    branches = load_branches()
except Exception as e:
    show_api_error(e)

branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SAFE SHEET FETCH
# =========================================================

@st.cache_resource
def get_spreadsheet(sheet_id):
    try:
        return client.open_by_key(sheet_id)
    except:
        return None

def fetch_sheet_range(sheet_id):
    try:
        ss = get_spreadsheet(sheet_id)
        if not ss:
            return None
        ws = ss.worksheet("Stocks")
        return ws.get_all_values()
    except:
        return None

def fetch_branch(branch):
    sid = branch.get("SheetID")
    if not sid:
        return branch["BranchName"], None

    return branch["BranchName"], fetch_sheet_range(sid)

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=600)
def load_all_data(branches):
    return [fetch_branch(b) for b in branches]

# =========================================================
# REFRESH CONTROL (1 MIN LOCK)
# =========================================================

if "last_force_refresh" not in st.session_state:
    st.session_state.last_force_refresh = 0

REFRESH_COOLDOWN = 60  # 1 minute

now = time.time()
remaining = REFRESH_COOLDOWN - (now - st.session_state.last_force_refresh)
remaining = max(0, int(remaining))
can_force_refresh = remaining <= 0

# =========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# BUTTONS
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

        with st.spinner("Fetching latest stock data from sheets..."):
            try:
                st.cache_data.clear()
                st.session_state.last_force_refresh = time.time()
                st.success("✅ Data refreshed successfully")
                st.rerun()

            except Exception as e:
                st.error(e)
                st.stop()

with col3:
    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# LIVE TIMER DISPLAY
# =========================================================

st.info(f"⏳ Manual refresh available in: {remaining} seconds")

# =========================================================
# LOAD DATA (CACHED OR FRESH)
# =========================================================

all_data = load_all_data(branches)

# =========================================================
# PROCESS STOCK
# =========================================================

@st.cache_data(ttl=300)
def process_stock(all_data, selected_date_str, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = [str(h).strip() for h in raw[0]]

        date_index = None
        for i, h in enumerate(headers):
            if str(h).strip() == selected_date_str:
                date_index = i
                break

        current_section = None

        for row in raw:

            if not row:
                continue

            text = " ".join([str(x) for x in row]).lower()

            if "daily item" in text:
                current_section = "daily"
                continue

            if "weekly item" in text:
                current_section = "weekly"
                continue

            if current_section is None:
                continue

            item = str(row[0]).strip()
            sku = str(row[1]).strip() if len(row) > 1 else ""
            uom = str(row[2]).strip() if len(row) > 2 else ""

            if not item:
                continue

            key = f"{item}_{sku}_{uom}"
            target = daily if current_section == "daily" else weekly

            if key not in target:
                target[key] = {
                    "Item Name": item,
                    "SKU": sku,
                    "UOM": uom
                }

                for bn in branch_names:
                    target[key][bn] = 0

            qty = 0
            try:
                if date_index is not None and len(row) > date_index:
                    val = row[date_index]
                    qty = float(val) if val not in ["", None] else 0
            except:
                qty = 0

            target[key][branch_name] = qty

    return daily, weekly

daily_items, weekly_items = process_stock(
    all_data,
    selected_date_str,
    branch_names
)

# =========================================================
# DATAFRAME
# =========================================================

def build_df(data_dict):

    rows = []

    for _, v in data_dict.items():

        row = {
            "Item Name": v["Item Name"],
            "SKU": v["SKU"],
            "UOM": v["UOM"]
        }

        for b in branch_names:
            row[b] = v.get(b, 0)

        rows.append(row)

    return pd.DataFrame(rows)

daily_df = build_df(daily_items)
weekly_df = build_df(weekly_items)

# =========================================================
# GRID
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

    gb.configure_column("Item Name", pinned="left", minWidth=140)
    gb.configure_column("SKU", pinned="left", minWidth=80)
    gb.configure_column("UOM", pinned="left", minWidth=70)

    for col in branch_names:
        if col in df.columns:
            gb.configure_column(col, minWidth=get_width(df[col], 120))

    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    AgGrid(df, gridOptions=gb.build(), theme="streamlit", key=title)

# =========================================================
# DISPLAY
# =========================================================

render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# EXCEL EXPORT
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

        ws.merge_cells(start_row=start_row, start_column=1,
                       end_row=start_row, end_column=total_cols)

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
