import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
from gspread.exceptions import APIError
import time
import os
import pickle

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")


# =========================================================
# CACHE FILES
# =========================================================

CACHE_FILE = "stock_cache.pkl"
SYNC_FILE = "sync_meta.pkl"
SYNC_LOCK_SECONDS = 300  # 5 minutes

# =========================================================
# HELPERS (CACHE LOAD/SAVE)
# =========================================================

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return None

def save_cache(data):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data, f)

def load_sync_meta():
    if os.path.exists(SYNC_FILE):
        with open(SYNC_FILE, "rb") as f:
            return pickle.load(f)
    return {"last_sync": 0}

def save_sync_meta(meta):
    with open(SYNC_FILE, "wb") as f:
        pickle.dump(meta, f)

sync_meta = load_sync_meta()

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
# BRANCH LOAD (ONLY USED DURING SYNC)
# =========================================================

def load_branches_live():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [
        b for b in data
        if b.get("SheetID") and b.get("BranchName")
    ]

# =========================================================
# FETCH SHEET
# =========================================================

def fetch_sheet(sheet_id):
    try:
        ss = client.open_by_key(sheet_id)
        ws = ss.worksheet("Stocks")
        return ws.get_all_values()
    except:
        return None

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

            item = str(row[0]).strip()
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

# =========================================================
# SYNC CONTROL
# =========================================================

now = time.time()
can_sync = (now - sync_meta.get("last_sync", 0)) > SYNC_LOCK_SECONDS
remaining = int(SYNC_LOCK_SECONDS - (now - sync_meta.get("last_sync", 0)))
remaining = max(0, remaining)

# =========================================================
# SYNC BUTTON (MAIN ACTION)
# =========================================================

col1, col2 = st.columns([2, 1])

with col1:

    if st.button("🔄 SYNC DATA (Fetch All Branches)"):

        if not can_sync:
            st.warning(f"⏳ Sync locked. Wait {remaining} seconds.")
            st.stop()

        with st.spinner("Fetching all 28 branches from Google Sheets..."):

            try:
                branches = load_branches_live()
                branch_names = [b["BranchName"] for b in branches]

                all_data = [
                    (b["BranchName"], fetch_sheet(b["SheetID"]))
                    for b in branches
                ]

                selected_date_str = st.date_input(
                    "📅 Select Date"
                ).strftime("%Y-%m-%d")

                daily, weekly = process_stock(
                    all_data,
                    selected_date_str,
                    branch_names
                )

                cache_data = {
                    "branches": branches,
                    "branch_names": branch_names,
                    "daily": daily,
                    "weekly": weekly,
                    "timestamp": now
                }

                save_cache(cache_data)

                sync_meta["last_sync"] = now
                save_sync_meta(sync_meta)

                st.success("✅ Sync Completed Successfully")
                st.rerun()

            except APIError as e:
                st.error("Google API Error")
                st.error(str(e))

                old = load_cache()
                if old:
                    st.info("⚠️ Loaded previous cached data instead")

# =========================================================
# LOAD CACHE FOR DISPLAY
# =========================================================

cache = load_cache()

if not cache:
    st.warning("No cached data found. Please click SYNC DATA.")
    st.stop()

branches = cache["branches"]
branch_names = cache["branch_names"]
daily_items = cache["daily"]
weekly_items = cache["weekly"]

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

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        height=500,
        fit_columns_on_grid_load=False
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
    ws.title = "Stock Dashboard"

    def write_section(title, df, start_row):

        rows = list(dataframe_to_rows(df, index=False, header=True))

        if not rows:
            return start_row + 2

        cols = len(rows[0])

        ws.merge_cells(start_row=start_row, start_column=1,
                       end_row=start_row, end_column=cols)

        ws.cell(row=start_row, column=1, value=title).font = Font(bold=True)

        r0 = start_row + 2

        for r_i, row in enumerate(rows):
            for c_i, val in enumerate(row, 1):
                ws.cell(row=r0 + r_i, column=c_i, value=val)

        return r0 + len(rows) + 3

    next_row = write_section("DAILY STOCK", daily_df, 1)
    write_section("WEEKLY STOCK", weekly_df, next_row)

    wb.save(output)
    output.seek(0)
    return output

excel_file = create_excel(daily_df, weekly_df)

st.download_button(
    "📥 Download Stock Report",
    excel_file,
    file_name="stock_report.xlsx"
)

# =========================================================
# SYNC INFO
# =========================================================

st.caption(f"Last Sync: {time.ctime(sync_meta.get('last_sync', 0))}")
if not can_sync:
    st.warning(f"🔒 Sync locked for {remaining} seconds")
