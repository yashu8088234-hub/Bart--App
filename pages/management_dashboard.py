import streamlit as st
import psycopg2
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

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# POSTGRES CONNECTION (ADDED - SAFE)
# =========================================================
def get_conn():
    return psycopg2.connect(
        host="localhost",
        database="bart",
        user="postgres",
        password="YOUR_PASSWORD",  # 🔴 CHANGE THIS
        port=5432
    )

# =========================================================
# POSTGRES TEST (ADDED - SAFE UI BLOCK)
# =========================================================
st.sidebar.subheader("🗄️ Database Check")

if st.sidebar.button("Test PostgreSQL"):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 'PostgreSQL Connected';")
        result = cur.fetchone()

        st.sidebar.success(result[0])

        cur.close()
        conn.close()

    except Exception as e:
        st.sidebar.error(f"DB Error: {e}")

# =========================================================
# ERROR HANDLER
# =========================================================
def show_api_error():
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
except:
    show_api_error()

# =========================================================
# BRANCH LIST
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
# SAFE SHEET FETCH
# =========================================================
def safe_get_all_values(ws):
    try:
        return ws.get_all_values()
    except:
        return None

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
    except:
        return name, None

# =========================================================
# LOAD ALL DATA
# =========================================================
@st.cache_data(ttl=1800)
def load_all_data(branches):
    results = []
    for b in branches:
        results.append(fetch_branch(b))
    return results

with st.spinner("Loading stock data..."):
    all_data = load_all_data(branches)

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

    return pd.DataFrame(rows) if rows else pd.DataFrame()

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

    AgGrid(df, gridOptions=gb.build(), theme="streamlit")

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

    def write_section(title, df, start_row):

        rows = list(dataframe_to_rows(df, index=False, header=True))

        if not rows:
            return start_row + 2

        ws.merge_cells(start_row=start_row, start_column=1,
                       end_row=start_row, end_column=len(rows[0]))

        ws.cell(row=start_row, column=1, value=title).font = Font(bold=True)

        row_idx = start_row + 2

        for r_i, row in enumerate(rows):
            for c_i, val in enumerate(row, 1):
                ws.cell(row=row_idx + r_i, column=c_i, value=val)

        return row_idx + len(rows) + 3

    next_row = write_section("DAILY STOCK", daily_df, 1)
    write_section("WEEKLY STOCK", weekly_df, next_row)

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

# =========================================================
# BACK BUTTON (UNCHANGED)
# =========================================================
if st.button("🔙 Back"):
    st.switch_page("app.py")
