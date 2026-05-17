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
# ERROR HANDLER
# =========================================================

def show_api_error():
    st.error("API Error")
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

client = get_client()

# =========================================================
# GLOBAL STORE (ONE SOURCE OF TRUTH)
# =========================================================

@st.cache_resource
def get_store():
    return {
        "all_data": None,
        "branches": None,
        "sheet_cache": None,
        "last_refresh": 0
    }

store = get_store()

# =========================================================
# LOAD BRANCHES (ONLY WHEN EMPTY)
# =========================================================

def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

if store["branches"] is None:
    store["branches"] = load_branches()

branches = store["branches"]
branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SHEET CACHE (FIXED HERE)
# =========================================================

@st.cache_resource
def get_sheets(branches):
    cache = {}

    for b in branches:   # <-- FIX: expects dicts
        sid = b.get("SheetID")
        if sid:
            try:
                cache[sid] = client.open_by_key(sid)
            except:
                pass

    return cache

# ❌ FIXED: PASS branches NOT branch_names
if store["sheet_cache"] is None:
    store["sheet_cache"] = get_sheets(tuple(branches))

sheet_cache = store["sheet_cache"]

# =========================================================
# FETCH DATA
# =========================================================

def fetch_sheet_range(sheet_id):
    try:
        ws = sheet_cache[sheet_id].worksheet("Stocks")
        return ws.get("A1:ZZ1000")
    except:
        return None

def fetch_branch(branch):
    sid = branch.get("SheetID")
    if not sid or sid not in sheet_cache:
        return branch["BranchName"], None
    return branch["BranchName"], fetch_sheet_range(sid)

def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=5) as ex:
        return list(ex.map(fetch_branch, branches))

# =========================================================
# INITIAL LOAD (ONLY ONCE PER SERVER)
# =========================================================

if store["all_data"] is None:
    with st.spinner("Initial loading from Google Sheets..."):
        store["all_data"] = load_all_data(branches)

all_data = store["all_data"]

# =========================================================
# REFRESH CONTROL
# =========================================================

if "last_force_refresh" not in st.session_state:
    st.session_state.last_force_refresh = 0

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Date Only"):
        st.rerun()

with col2:

    if st.button("🔴 Refresh All Data"):

        with st.spinner("Refreshing from Google Sheets..."):

            store["branches"] = load_branches()
            branches = store["branches"]
            branch_names = [b["BranchName"] for b in branches]

            store["sheet_cache"] = get_sheets(tuple(branches))
            sheet_cache = store["sheet_cache"]

            store["all_data"] = load_all_data(branches)
            all_data = store["all_data"]

            st.session_state.last_force_refresh = time.time()

            st.success("✅ Data refreshed for ALL users")

            st.rerun()

with col3:
    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# PROCESS STOCK
# =========================================================

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

    return pd.DataFrame(rows)

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
    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    AgGrid(df, gridOptions=gb.build(), theme="streamlit", key=title)

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

    def write(df, title, start_row):

        ws.cell(row=start_row, column=1, value=title).font = Font(bold=True)

        rows = dataframe_to_rows(df, index=False, header=True)

        r = start_row + 2
        for row in rows:
            for c, v in enumerate(row, 1):
                ws.cell(row=r, column=c, value=v)
            r += 1

        return r + 2

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
