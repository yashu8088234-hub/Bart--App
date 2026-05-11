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
# BRANCHES
# =========================================================

@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
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
# FAST FETCH
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
# LOAD DATA
# =========================================================

@st.cache_data(ttl=300)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=10) as ex:
        return list(ex.map(fetch_branch, branches))

all_data = load_all_data(branches)

# =========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# REFRESH + BACK
# =========================================================

col1 = st.columns(1)[0]

with col1:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔙 Back"):
        st.switch_page("app.py")

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
# WIDTH FUNCTION (RESTORED)
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
# AGGRID RENDER (RESTORED)
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
        minWidth=get_width(df["Item Name"], 90)
    )

    gb.configure_column(
        "SKU",
        pinned="left",
        minWidth=get_width(df["SKU"], 40)
    )

    gb.configure_column(
        "UOM",
        pinned="left",
        minWidth=get_width(df["UOM"], 40)
    )

    for col in branch_names:
        if col in df.columns:
            gb.configure_column(col, minWidth=get_width(df[col], 120))

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        fit_columns_on_grid_load=False
    )

# =========================================================
# DISPLAY
# =========================================================

render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# ⭐ WOW EXCEL DOWNLOAD (SINGLE BUTTON)
# =========================================================

def create_excel(daily_df, weekly_df):

    output = BytesIO()
    wb = Workbook()

    def add_sheet(df, name):

        ws = wb.create_sheet(title=name)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="1F4E79")
        align = Alignment(horizontal="center")

        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            ws.append(row)

            for cell in ws[r_idx]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = align

        # Auto width
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter

            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))

            ws.column_dimensions[col_letter].width = max_len + 3

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    add_sheet(daily_df, "Daily Stock")
    add_sheet(weekly_df, "Weekly Stock")

    wb.remove(wb["Sheet"])
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
