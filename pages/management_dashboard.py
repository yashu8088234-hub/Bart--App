import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
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
# GLOBAL COOLDOWN SYSTEM (ANTI API SPAM)
# =========================================================

if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = 0

if "data_cache" not in st.session_state:
    st.session_state.data_cache = None

COOLDOWN_SECONDS = 8  # prevent API spam

def can_refresh():
    return time.time() - st.session_state.last_refresh_time > COOLDOWN_SECONDS

def set_refresh_time():
    st.session_state.last_refresh_time = time.time()

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

client = get_client()

# =========================================================
# SAFE API CALL WRAPPER
# =========================================================

def safe_api(call_func):
    try:
        return call_func()
    except APIError:
        st.error("🚨 API limit reached. Please wait 2–3 minutes before retrying.")
        return None

# =========================================================
# BRANCHES
# =========================================================

@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = safe_api(load_branches) or []
branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SHEET CACHE
# =========================================================

@st.cache_resource
def get_sheets(branches):
    cache = {}
    for b in branches:
        sid = b.get("SheetID")
        if sid:
            try:
                cache[sid] = client.open_by_key(sid)
            except:
                pass
    return cache

sheet_cache = get_sheets(branches)

# =========================================================
# FETCH
# =========================================================

@st.cache_data(ttl=600)
def fetch_sheet_range(sheet_id):
    try:
        ws = sheet_cache[sheet_id].worksheet("Stocks")
        return ws.get("A1:Z500")
    except:
        return None

def fetch_branch(branch):
    sid = branch.get("SheetID")
    if not sid or sid not in sheet_cache:
        return branch["BranchName"], None
    return branch["BranchName"], fetch_sheet_range(sid)

# =========================================================
# LOAD ALL DATA (CONTROLLED)
# =========================================================

def load_all_data():
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(fetch_branch, branches))

# =========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# BUTTONS (CONTROLLED)
# =========================================================

col1, col2 = st.columns(2)

with col1:

    refresh_clicked = st.button(
        "🔄 Refresh Data (API CALL)",
        disabled=not can_refresh()
    )

with col2:
    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# AUTO LOAD LOGIC (CACHE FIRST)
# =========================================================

def get_data():

    # use cache if exists and no forced refresh
    if st.session_state.data_cache is not None and not refresh_clicked:
        return st.session_state.data_cache

    # block spam refresh
    if refresh_clicked and not can_refresh():
        st.warning("⏳ Please wait a few seconds before refreshing again.")
        return st.session_state.data_cache

    if refresh_clicked:
        set_refresh_time()

    data = safe_api(load_all_data)

    if data is None:
        return st.session_state.data_cache

    st.session_state.data_cache = data
    return data

all_data = get_data()

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
            if h == selected_date_str:
                date_index = i
                break

        current_section = None

        for row in raw:

            text = " ".join([str(x) for x in row]).lower()

            if "daily item" in text:
                current_section = "daily"
                continue

            if "weekly item" in text:
                current_section = "weekly"
                continue

            if current_section is None:
                continue

            item = str(row[0]).strip() if len(row) > 0 else ""
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
                    qty = float(row[date_index] or 0)
            except:
                qty = 0

            target[key][branch_name] = qty

    return daily, weekly

daily_items, weekly_items = process_stock(all_data, selected_date_str, branch_names)

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
# WIDTH
# =========================================================

def get_width(series, min_width):
    try:
        series = series.fillna("").astype(str)
        max_len = series.map(len).max()
        return max(int(max_len * 5 + 25), min_width)
    except:
        return min_width

# =========================================================
# GRID
# =========================================================

def render_grid(df, title):

    st.subheader(title)

    if df is None or df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item Name", pinned="left", minWidth=get_width(df["Item Name"], 90))
    gb.configure_column("SKU", pinned="left", minWidth=get_width(df["SKU"], 40))
    gb.configure_column("UOM", pinned="left", minWidth=get_width(df["UOM"], 40))

    for col in branch_names:
        if col in df.columns:
            gb.configure_column(col, minWidth=get_width(df[col], 120))

    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        fit_columns_on_grid_load=False,
        key=title
    )

render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# EXCEL DOWNLOAD
# =========================================================

def create_excel(daily_df, weekly_df):

    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock"

    def write(df, title, start):

        rows = list(dataframe_to_rows(df, index=False, header=True))
        ws.cell(row=start, column=1, value=title).font = Font(bold=True)

        for r_i, row in enumerate(rows):
            for c_i, val in enumerate(row, 1):
                ws.cell(row=start + 2 + r_i, column=c_i, value=val)

        return start + len(rows) + 4

    next_row = write(daily_df, "DAILY STOCK", 1)
    write(weekly_df, "WEEKLY STOCK", next_row)

    wb.save(output)
    output.seek(0)
    return output

excel_file = create_excel(daily_df, weekly_df)

st.download_button(
    "📥 Download Stock Report",
    excel_file,
    file_name="stock_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
