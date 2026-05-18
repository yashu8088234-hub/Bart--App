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
import time

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# ERROR HANDLER
# =========================================================
def show_api_error(msg="Google Sheets API Error"):
    st.error(msg)
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
# BRANCH LOADING (NO SILENT FILTERING)
# =========================================================
@st.cache_data(ttl=300)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()

    # ❗ DO NOT FILTER SILENTLY
    # keep all rows, handle errors later
    return data

try:
    branches = load_branches()
except:
    show_api_error()

branch_names = [b.get("BranchName", "") for b in branches]

# =========================================================
# FETCH ONE BRANCH (SAFE)
# =========================================================
def fetch_branch(branch):
    try:
        sid = branch.get("SheetID")
        name = branch.get("BranchName", "UNKNOWN")

        if not sid:
            return name, []

        ws = client.open_by_key(sid).worksheet("Stocks")
        data = ws.get_all_values()

        return name, data

    except Exception as e:
        return branch.get("BranchName", "UNKNOWN"), []

# =========================================================
# LOAD ALL DATA (CONTROLLED REFRESH)
# =========================================================
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(fetch_branch, branches))

# =========================================================
# REFRESH CONTROL
# =========================================================
REFRESH_COOLDOWN = 120

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0

remaining = REFRESH_COOLDOWN - (time.time() - st.session_state.last_refresh)
can_refresh = remaining <= 0

# =========================================================
# DATE INPUT
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

    label = "🔴 Refresh Data" if can_refresh else f"⏳ Wait {int(remaining)}s"

    if st.button(label, disabled=not can_refresh):

        with st.spinner("Refreshing all branches..."):

            st.cache_data.clear()

            branches = load_branches()

            branch_names = [b.get("BranchName", "") for b in branches]

            all_data = load_all_data(branches)

            st.session_state.last_refresh = time.time()

            st.success("✅ Updated from Google Sheets")

            st.rerun()

with col3:
    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# INITIAL LOAD
# =========================================================
all_data = load_all_data(branches)

# =========================================================
# DEBUG MISSING BRANCHES (IMPORTANT)
# =========================================================
loaded_names = [x[0] for x in all_data]
missing = set(branch_names) - set(loaded_names)

if missing:
    st.warning(f"⚠️ Missing branches detected: {missing}")

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

            text = " ".join(map(str, row)).lower()

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
                for b in branch_names:
                    target[key][b] = 0

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

    for v in data_dict.values():

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

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        key=title
    )

render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# EXCEL EXPORT
# =========================================================
def create_excel(daily_df, weekly_df):

    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock"

    def write(df, title, start):

        ws.cell(row=start, column=1, value=title).font = Font(bold=True)

        rows = dataframe_to_rows(df, index=False, header=True)

        r = start + 2

        for i, row in enumerate(rows):
            for c, v in enumerate(row, 1):
                ws.cell(row=r+i, column=c, value=v)

        return r + len(df) + 3

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
