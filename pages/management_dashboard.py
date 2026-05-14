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
SYNC_LOCK = 300  # 5 min

# =========================================================
# CACHE HELPERS
# =========================================================

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return None

def save_cache(data):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data, f)

def load_sync():
    if os.path.exists(SYNC_FILE):
        with open(SYNC_FILE, "rb") as f:
            return pickle.load(f)
    return {"last_sync": 0}

def save_sync(data):
    with open(SYNC_FILE, "wb") as f:
        pickle.dump(data, f)

sync_meta = load_sync()

# =========================================================
# GOOGLE AUTH (UNCHANGED)
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
# BRANCHES (ONLY USED ON SYNC)
# =========================================================

def load_branches_live():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

# =========================================================
# SHEET FETCH (UNCHANGED LOGIC)
# =========================================================

def fetch_sheet(sheet_id):
    try:
        ss = client.open_by_key(sheet_id)
        ws = ss.worksheet("Stocks")
        return ws.get_all_values()
    except:
        return None

# =========================================================
# SYNC LOCK LOGIC
# =========================================================

now = time.time()
can_sync = (now - sync_meta.get("last_sync", 0)) > SYNC_LOCK

remaining = int(SYNC_LOCK - (now - sync_meta.get("last_sync", 0)))
remaining = max(0, remaining)

# =========================================================
# SYNC BUTTON (ONLY DATA REFRESH)
# =========================================================

if st.button("🔄 SYNC DATA"):

    if not can_sync:
        st.warning(f"⏳ Please wait {remaining} seconds before syncing again")
        st.stop()

    with st.spinner("Fetching all 28 branches..."):

        try:
            branches = load_branches_live()
            branch_names = [b["BranchName"] for b in branches]

            selected_date_str = st.date_input("📅 Select Date").strftime("%Y-%m-%d")

            # reuse YOUR original logic unchanged
            all_data = [
                (b["BranchName"], fetch_sheet(b["SheetID"]))
                for b in branches
            ]

            daily_items, weekly_items = process_stock(
                all_data,
                selected_date_str,
                branch_names
            )

            cache_data = {
                "branches": branches,
                "branch_names": branch_names,
                "daily": daily_items,
                "weekly": weekly_items
            }

            save_cache(cache_data)

            sync_meta["last_sync"] = now
            save_sync(sync_meta)

            st.success("✅ Sync Completed")
            st.rerun()

        except APIError as e:
            st.error(e)

            old = load_cache()
            if old:
                st.info("⚠️ Loaded previous cached data")

# =========================================================
# LOAD CACHE (DEFAULT VIEW)
# =========================================================

cache = load_cache()

if not cache:
    st.warning("No data found. Please click SYNC DATA.")
    st.stop()

branches = cache["branches"]
branch_names = cache["branch_names"]
daily_items = cache["daily"]
weekly_items = cache["weekly"]

# =========================================================
# BUILD DF (UNCHANGED)
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
# AGGRID (UNCHANGED - NO MODIFICATION)
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
# FOOTER
# =========================================================

st.caption(f"Last Sync: {time.ctime(sync_meta.get('last_sync', 0))}")

if not can_sync:
    st.warning(f"🔒 Sync locked for {remaining} seconds")
