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

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# ERROR HANDLER
# =========================================================

def show_api_error(msg="API Error"):
    st.error(f"⚠️ {msg}")
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
# BRANCHES
# =========================================================

@st.cache_data(ttl=300)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()

    branches = []
    for b in data:
        if b.get("SheetID") and b.get("BranchName"):
            branches.append({
                "BranchName": str(b["BranchName"]).strip(),
                "SheetID": str(b["SheetID"]).strip()
            })

    return branches

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SHEET CACHE (SAFE VERSION)
# =========================================================

@st.cache_resource
def get_sheets(branches):
    cache = {}
    errors = {}

    for b in branches:
        sid = b["SheetID"]
        try:
            cache[sid] = client.open_by_key(sid)
        except Exception as e:
            errors[sid] = str(e)

    return cache, errors

sheet_cache, sheet_errors = get_sheets(branches)

if sheet_errors:
    st.warning("Some branches failed to connect to Google Sheets.")

# =========================================================
# FETCH DATA (NEVER DROP BRANCHES)
# =========================================================

def fetch_sheet_range(sheet_id):
    try:
        ws = sheet_cache[sheet_id].worksheet("Stocks")
        return ws.get("A1:ZZ1000"), None
    except Exception as e:
        return None, str(e)

def fetch_branch(branch):
    sid = branch["SheetID"]

    if sid not in sheet_cache:
        return branch["BranchName"], None, "SHEET_NOT_IN_CACHE"

    data, err = fetch_sheet_range(sid)

    if err:
        return branch["BranchName"], None, err

    return branch["BranchName"], data, None

@st.cache_data(ttl=200)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=20) as ex:
        return list(ex.map(fetch_branch, branches))

all_data = load_all_data(branches)

# =========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# PROCESS STOCK (ROBUST)
# =========================================================

@st.cache_data(ttl=300)
def process_stock(all_data, selected_date_str, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw, err in all_data:

        # IMPORTANT: branch is NEVER skipped
        if raw is None:
            continue

        if len(raw) < 2:
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
# DATAFRAME (FORCE ALL BRANCH COLUMNS)
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

    gb.configure_column("Item Name", pinned="left")
    gb.configure_column("SKU", pinned="left")
    gb.configure_column("UOM", pinned="left")

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )

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

    def write_section(title, df, start_row):

        rows = list(dataframe_to_rows(df, index=False, header=True))
        if not rows:
            return start_row

        ws.cell(row=start_row, column=1, value=title).font = Font(bold=True, size=14)

        for r_i, row in enumerate(rows):
            for c_i, val in enumerate(row, 1):
                ws.cell(row=start_row + 2 + r_i, column=c_i, value=val)

        return start_row + len(rows) + 4

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

# =========================================================
# BACK BUTTON
# =========================================================

if st.button("🔙 Back"):
    st.switch_page("app.py")
