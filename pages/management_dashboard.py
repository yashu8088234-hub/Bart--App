import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
import time

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

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

@st.cache_data(ttl=21600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SAFE SHEET ACCESS (CACHE FIX)
# =========================================================

@st.cache_resource
def get_sheet(sheet_id):
    try:
        return client.open_by_key(sheet_id)
    except:
        return None

@st.cache_resource
def get_worksheet(sheet_id):
    try:
        sheet = get_sheet(sheet_id)
        if not sheet:
            return None
        return sheet.worksheet("Stocks")
    except:
        return None

# =========================================================
# SAFE FETCH WITH RETRY (🔥 FIX FOR API ERRORS)
# =========================================================

@st.cache_data(ttl=600)
def fetch_sheet_range(sheet_id, date_key):

    ws = get_worksheet(sheet_id)
    if not ws:
        return None

    for attempt in range(3):
        try:
            return ws.get("A1:Z500")

        except Exception:
            time.sleep(1.5 * (attempt + 1))

    return None

# =========================================================
# SEQUENTIAL FETCH (🔥 REMOVED THREADPOOL ISSUE)
# =========================================================

def fetch_branch(branch, date_key):
    sid = branch.get("SheetID")
    if not sid:
        return branch["BranchName"], None

    return branch["BranchName"], fetch_sheet_range(sid, date_key)

@st.cache_data(ttl=300)
def load_all_data(branches, date_key):

    results = []

    # 🔥 FIX: NO THREADPOOL (prevents API spikes)
    for b in branches:
        try:
            results.append(fetch_branch(b, date_key))
        except:
            continue

    return results

# =========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# BUTTONS
# =========================================================

col1 = st.columns(1)[0]

with col1:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# LOAD DATA
# =========================================================

all_data = load_all_data(branches, selected_date_str)

# =========================================================
# PROCESS STOCK (UNCHANGED LOGIC)
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

            text = " ".join(row).lower()

            if "daily item" in text:
                current_section = "daily"
                continue

            if "weekly item" in text:
                current_section = "weekly"
                continue

            if current_section is None:
                continue

            item = row[0].strip() if len(row) > 0 else ""
            sku = row[1].strip() if len(row) > 1 else ""
            uom = row[2].strip() if len(row) > 2 else ""

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
# DATAFRAME (🔥 SAFE EMPTY FIX)
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

    df = pd.DataFrame(rows)

    # 🔥 FIX: NEVER EMPTY (prevents Excel crash)
    if df.empty:
        df = pd.DataFrame(columns=["Item Name", "SKU", "UOM"] + branch_names)
        df.loc[0] = ["NO DATA", "", ""] + [0] * len(branch_names)

    return df.fillna(0)

daily_df = build_df(daily_items)
weekly_df = build_df(weekly_items)

# =========================================================
# GRID
# =========================================================

def render_grid(df, title):

    st.subheader(title)

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item Name", pinned="left")
    gb.configure_column("SKU", pinned="left")
    gb.configure_column("UOM", pinned="left")

    for col in branch_names:
        if col in df.columns:
            gb.configure_column(col)

    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    AgGrid(df, gridOptions=gb.build(), theme="streamlit")

render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# EXCEL EXPORT (SAFE VERSION)
# =========================================================

def create_excel(daily_df, weekly_df):

    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Dashboard"

    header_font = Font(bold=True)
    section_font = Font(bold=True, size=14)
    align_center = Alignment(horizontal="center")
    zebra = PatternFill("solid", fgColor="F5F5F5")

    def write_section(title, df, start_row):

        if df is None or df.empty:
            df = pd.DataFrame(columns=["Item Name", "SKU", "UOM"] + branch_names)
            df.loc[0] = ["NO DATA", "", ""] + [0] * len(branch_names)

        rows = list(dataframe_to_rows(df, index=False, header=True))

        total_cols = max(1, len(rows[0]))

        ws.merge_cells(start_row=start_row, start_column=1,
                       end_row=start_row, end_column=total_cols)

        ws.cell(row=start_row, column=1, value=title).font = section_font

        header_row = start_row + 2

        for i, val in enumerate(rows[0], 1):
            cell = ws.cell(row=header_row, column=i, value=val)
            cell.font = header_font

        data_start = header_row + 1

        for r_i, row in enumerate(rows[1:]):
            for c_i, val in enumerate(row, 1):
                cell = ws.cell(row=data_start + r_i, column=c_i, value=val)
                if r_i % 2 == 1:
                    cell.fill = zebra

        return data_start + len(rows[1:]) + 2

    next_row = write_section("DAILY STOCK", daily_df, 1)
    write_section("WEEKLY STOCK", weekly_df, next_row)

    for col in range(1, ws.max_column + 1):
        col_letter = get_column_letter(col)
        max_len = max(
            (len(str(ws.cell(row=r, column=col).value or "")) for r in range(1, ws.max_row + 1)),
            default=10
        )
        ws.column_dimensions[col_letter].width = max_len + 2

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
