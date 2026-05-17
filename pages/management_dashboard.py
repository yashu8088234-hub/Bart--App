import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from gspread.exceptions import APIError
import time

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# ERROR SCREEN
# =========================================================

def show_api_error():
    st.error("❌ API Error - Please try again")
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
except:
    show_api_error()

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
except APIError:
    show_api_error()
except:
    show_api_error()

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
            except Exception as e:
                st.warning(f"⚠️ Cannot open sheet {sid}: {e}")

    return cache

try:
    sheet_cache = get_sheets(branches)
except:
    show_api_error()

# =========================================================
# FETCH SHEET WITH RETRY (FIXED)
# =========================================================

def fetch_branch(branch, retry_seconds=60, delay=3):

    sid = branch.get("SheetID")
    name = branch.get("BranchName")

    if not sid or sid not in sheet_cache:
        return name, None

    start_time = time.time()

    while True:
        try:
            ws = sheet_cache[sid].worksheet("Stocks")
            data = ws.get("A1:ZZ1000")
            return name, data

        except Exception as e:
            elapsed = time.time() - start_time

            if elapsed > retry_seconds:
                st.warning(f"❌ Failed after retry timeout: {name}")
                return name, None

            time.sleep(delay)

# =========================================================
# LOAD ALL DATA (THREADS + SAFE RETRY)
# =========================================================

@st.cache_data(ttl=600)
def load_all_data(branches):

    with ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(fetch_branch, branches))

    return results

# =========================================================
# SMART REFRESH CONTROL
# =========================================================

REFRESH_COOLDOWN = 90

if "last_force_refresh" not in st.session_state:
    st.session_state.last_force_refresh = 0

remaining = REFRESH_COOLDOWN - (
    time.time() - st.session_state.last_force_refresh
)

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

    refresh_text = "🔴 Refresh Now" if can_force_refresh else f"⏳ Wait {int(remaining)} sec"

    refresh_clicked = st.button(refresh_text, disabled=not can_force_refresh)

    if refresh_clicked:

        with st.spinner("Fetching latest stock data..."):

            try:
                st.cache_data.clear()
                st.cache_resource.clear()

                client = get_client()
                branches = load_branches()
                sheet_cache = get_sheets(branches)

                st.session_state.sheet_cache = sheet_cache

                all_data = load_all_data(branches)
                st.session_state.all_data = all_data

                st.session_state.last_force_refresh = time.time()

                st.success("✅ Data refreshed successfully")

                st.rerun()

            except:
                show_api_error()

with col3:
    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# FIRST LOAD
# =========================================================

all_data = st.session_state.get("all_data", load_all_data(branches))

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

    return pd.DataFrame(rows) if rows else pd.DataFrame()

daily_df = build_df(daily_items)
weekly_df = build_df(weekly_items)

# =========================================================
# GRID
# =========================================================

def render_grid(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item Name", pinned="left")
    gb.configure_column("SKU", pinned="left")
    gb.configure_column("UOM", pinned="left")

    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    AgGrid(df, gridOptions=gb.build(), theme="streamlit")

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

        ws.merge_cells(start_row=start_row, start_column=1,
                       end_row=start_row, end_column=len(rows[0]) if rows else 1)

        ws.cell(row=start_row, column=1, value=title)

        r = start_row + 2

        for i, row in enumerate(rows):
            for j, val in enumerate(row, 1):
                ws.cell(row=r + i, column=j, value=val)

        return r + len(rows) + 2

    next_row = write_section("DAILY STOCK", daily_df, 1)
    write_section("WEEKLY STOCK", weekly_df, next_row)

    wb.save(output)
    output.seek(0)
    return output

excel_file = create_excel(daily_df, weekly_df)

st.download_button(
    "📥 Download Excel",
    excel_file,
    file_name="stock_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
