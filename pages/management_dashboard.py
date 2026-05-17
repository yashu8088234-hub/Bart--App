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
from gspread.exceptions import APIError
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# ERROR HANDLER
# =========================================================

def show_api_error(error=None):
    if error:
        st.error(f"API Error: {str(error)}")
    else:
        st.error("API Error Occurred. Please try again later.")
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
# MASTER SHEET CACHE
# =========================================================

@st.cache_resource
def get_master_sheet():
    return client.open("MASTERBRANCHSHEET").sheet1

# =========================================================
# LOAD BRANCHES
# =========================================================

@st.cache_data(ttl=600)
def load_branches():

    sheet = get_master_sheet()

    data = sheet.get_all_records()

    return [
        b for b in data
        if b.get("SheetID") and b.get("BranchName")
    ]

try:
    branches = load_branches()
except Exception as e:
    show_api_error(e)

branch_names = [b["BranchName"] for b in branches]

# =========================================================
# REFRESH BUTTON
# =========================================================

col1, col2 = st.columns([1, 8])

with col1:
    if st.button("🔄 Refresh Data"):

        st.cache_data.clear()

        st.success("Cache Cleared. Reloading Fresh Data...")

        st.rerun()

# =========================================================
# SAFE FETCH
# =========================================================

def safe_get_all_values(ws):

    try:
        return ws.get_all_values()

    except Exception as e:
        st.warning(f"Worksheet Fetch Failed: {str(e)}")
        return None

# =========================================================
# FETCH BRANCH
# =========================================================

def fetch_branch(branch):

    sid = branch.get("SheetID")
    name = branch["BranchName"]

    if not sid:
        return name, None

    try:

        ss = client.open_by_key(sid)

        ws = ss.worksheet("Stocks")

        data = safe_get_all_values(ws)

        return name, data

    except Exception as e:

        st.warning(f"{name}: {str(e)}")

        return name, None

# =========================================================
# LOAD ALL DATA (PARALLEL + CACHED)
# =========================================================

@st.cache_data(ttl=1800)
def load_all_data(branches_tuple):

    branch_objects = [
        {
            "BranchName": b[0],
            "SheetID": b[1]
        }
        for b in branches_tuple
    ]

    with ThreadPoolExecutor(max_workers=10) as executor:

        results = list(
            executor.map(fetch_branch, branch_objects)
        )

    return results

# =========================================================
# HASHABLE BRANCHES
# =========================================================

branches_tuple = tuple(
    (b["BranchName"], b["SheetID"])
    for b in branches
)

# =========================================================
# LOAD DATA
# =========================================================

with st.spinner("Loading stock data..."):

    all_data = load_all_data(branches_tuple)

# =========================================================
# DATE INPUT
# =========================================================

selected_date = st.date_input("📅 Select Date")

selected_date_str = selected_date.strftime("%Y-%m-%d")

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
    tuple(branch_names)
)

# =========================================================
# BUILD DATAFRAME
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
# GRID HELPERS
# =========================================================

def get_width(series, min_width):

    try:

        series = series.fillna("").astype(str)

        max_len = series.map(len).max()

        return max(int(max_len * 5 + 25), min_width)

    except:

        return min_width

# =========================================================
# GRID RENDER
# =========================================================

def render_grid(df, title):

    st.subheader(title)

    if df is None or df.empty:

        st.warning("No Data")

        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column(
        "Item Name",
        pinned="left",
        minWidth=160,
        flex=0
    )

    gb.configure_column(
        "SKU",
        pinned="left",
        minWidth=90,
        flex=0
    )

    gb.configure_column(
        "UOM",
        pinned="left",
        minWidth=80,
        flex=0
    )

    for col in branch_names:

        if col in df.columns:

            gb.configure_column(
                col,
                minWidth=get_width(df[col], 120)
            )

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )

    gb.configure_grid_options(
        domLayout='normal',
        suppressHorizontalScroll=False
    )

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        fit_columns_on_grid_load=False,
        height=600,
        key=title
    )

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

    header_font = Font(bold=True)

    align_center = Alignment(
        horizontal="center",
        vertical="center"
    )

    zebra_fill = PatternFill(
        "solid",
        fgColor="F5F5F5"
    )

    def write_section(title, df, start_row):

        rows = list(
            dataframe_to_rows(
                df,
                index=False,
                header=True
            )
        )

        if not rows:
            return start_row + 2

        total_cols = len(rows[0]) or 1

        ws.merge_cells(
            start_row=start_row,
            start_column=1,
            end_row=start_row,
            end_column=total_cols
        )

        ws.cell(
            row=start_row,
            column=1,
            value=title
        ).font = Font(
            bold=True,
            size=14
        )

        row_idx = start_row + 2

        for r_i, row in enumerate(rows):

            for c_i, val in enumerate(row, 1):

                c = ws.cell(
                    row=row_idx + r_i,
                    column=c_i,
                    value=val
                )

                c.alignment = align_center

                if r_i == 0:

                    c.font = header_font

                elif r_i % 2 == 0:

                    c.fill = zebra_fill

        return row_idx + len(rows) + 3

    next_row = write_section(
        "📦 DAILY STOCK",
        daily_df,
        1
    )

    write_section(
        "📦 WEEKLY STOCK",
        weekly_df,
        next_row
    )

    for col in ws.columns:

        try:
            column = get_column_letter(col[0].column)

        except:
            continue

        max_length = 0

        for cell in col:

            if cell.value:

                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws.column_dimensions[column].width = min(
            max_length + 3,
            40
        )

    wb.save(output)

    output.seek(0)

    return output

excel_file = create_excel(
    daily_df,
    weekly_df
)

# =========================================================
# DOWNLOAD
# =========================================================

st.download_button(
    "📥 Download Stock Report (Daily + Weekly Excel)",
    excel_file,
    file_name="stock_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================================================
# BACK BUTTON
# =========================================================

if st.button("🔙 Back"):

    st.switch_page("app.py")
