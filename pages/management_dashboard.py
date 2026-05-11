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
# BRANCHES (LESS FREQUENT REFRESH)
# =========================================================

@st.cache_data(ttl=21600)  # 6 hours
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SHEET ACCESS (FIXED: PER SHEET CACHE, NO GLOBAL DICT)
# =========================================================

@st.cache_resource
def get_sheet(sheet_id):
    try:
        return client.open_by_key(sheet_id)
    except:
        return None

# =========================================================
# FAST FETCH (CACHE PER SHEET + DATE)
# =========================================================

@st.cache_data(ttl=600)
def fetch_sheet_range(sheet_id, date_key):
    try:
        sheet = get_sheet(sheet_id)
        if not sheet:
            return None
        ws = sheet.worksheet("Stocks")
        return ws.get("A1:Z500")
    except:
        return None

def fetch_branch(branch, date_key):
    sid = branch.get("SheetID")
    if not sid:
        return branch["BranchName"], None

    return branch["BranchName"], fetch_sheet_range(sid, date_key)

# =========================================================
# LOAD DATA (REDUCED THREAD LOAD)
# =========================================================

@st.cache_data(ttl=300)
def load_all_data(branches, date_key):
    results = []

    # safer than heavy thread pool for Google API
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(fetch_branch, b, date_key) for b in branches]
        for f in futures:
            results.append(f.result())

    return results

# =========================================================
# DATE INPUT
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# BUTTONS (SAFE RERUN CONTROL)
# =========================================================

col1 = st.columns(1)[0]

with col1:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# SNAPSHOT (IMPORTANT: STOPS FULL REFETCH ON UI CHANGES)
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
# WIDTH FUNCTION (UNCHANGED)
# =========================================================

def get_width(series, min_width):

    try:
        series = series.fillna("").astype(str)
        max_len = series.map(len).max()

        if pd.isna(max_len) or max_len is None:
            return min_width

        width = int(max_len * 5 + 25)
        return max(width, min_width)

    except:
        return min_width

# =========================================================
# AGGRID (UNCHANGED)
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

    AgGrid(df, gridOptions=gb.build(), theme="streamlit", fit_columns_on_grid_load=False)

# =========================================================
# DISPLAY
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

    header_font = Font(bold=True, color="000000")
    section_font = Font(bold=True, size=14)
    align_center = Alignment(horizontal="center", vertical="center")
    zebra_fill = PatternFill("solid", fgColor="F5F5F5")

    def write_section(title, df, start_row):

        rows = list(dataframe_to_rows(df, index=False, header=True))
        total_cols = len(rows[0])

        ws.merge_cells(start_row=start_row, start_column=1,
                       end_row=start_row, end_column=total_cols)

        ws.cell(row=start_row, column=1, value=title).font = section_font
        ws.cell(row=start_row, column=1).alignment = align_center

        row_idx = start_row + 2

        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=3)
        ws.cell(row=row_idx, column=1, value="Item Info").font = header_font

        ws.merge_cells(start_row=row_idx, start_column=4, end_row=row_idx, end_column=total_cols)
        ws.cell(row=row_idx, column=4, value="Branch Stocks").font = header_font

        header_row = row_idx + 1

        for col_idx, value in enumerate(rows[0], 1):
            cell = ws.cell(row=header_row, column=col_idx, value=value)
            cell.font = header_font
            cell.alignment = align_center

        ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

        data_start = header_row + 1

        for i, row in enumerate(rows[1:], start=0):
            for j, value in enumerate(row, 1):
                c = ws.cell(row=data_start + i, column=j, value=value)
                c.alignment = align_center

                if i % 2 == 1:
                    c.fill = zebra_fill

        total_row = data_start + len(rows[1:])
        ws.cell(row=total_row, column=1, value="TOTAL").font = header_font

        for col in range(4, total_cols + 1):
            col_letter = ws.cell(row=header_row, column=col).column_letter
            ws.cell(row=total_row, column=col,
                    value=f"=SUM({col_letter}{data_start}:{col_letter}{total_row-1})")

        return total_row + 3

    next_row = write_section("📦 DAILY STOCK", daily_df, 1)
    write_section("📦 WEEKLY STOCK", weekly_df, next_row)

    from openpyxl.utils import get_column_letter

    for col_idx in range(1, ws.max_column + 1):
        max_len = 0
        col_letter = get_column_letter(col_idx)

        for row in range(1, ws.max_row + 1):
            cell = ws.cell(row=row, column=col_idx)
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_len + 3

    wb.save(output)
    output.seek(0)
    return output

excel_file = create_excel(daily_df, weekly_df)

st.download_button(
    "📥 Download Stock Report (Daily + Weekly Excel)",
    excel_file,
    file_name="stock_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
