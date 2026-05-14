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
# CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (Flexible Parser)")

CACHE_FILE = "stock_cache.pkl"
SYNC_FILE = "sync_meta.pkl"
SYNC_LOCK = 300

# =========================================================
# CACHE
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
# SAFE FETCH
# =========================================================

def fetch_sheet(sheet_id):
    try:
        ss = client.open_by_key(sheet_id)
        ws = ss.worksheet("Stocks")
        return ws.get_all_values() or []
    except:
        return []

# =========================================================
# FLEXIBLE STOCK PROCESSOR (FIXED CORE)
# =========================================================

def process_stock(all_data, selected_date_str, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw in all_data:

        if not raw:
            continue

        headers = [str(h).strip() for h in raw[0]]

        # =====================================================
        # FLEXIBLE DATE MATCH
        # =====================================================
        date_index = None
        for i, h in enumerate(headers):
            clean = str(h).strip().replace("/", "-")
            if selected_date_str in clean:
                date_index = i
                break

        current_section = "unknown"

        # =====================================================
        # PROCESS ROWS (NEVER SKIP)
        # =====================================================
        for row in raw[1:]:

            row = list(row) if row else []

            while len(row) < 3:
                row.append("")

            text = " ".join(map(str, row)).lower()

            # =================================================
            # FLEXIBLE SECTION DETECTION
            # =================================================
            if "daily" in text:
                current_section = "daily"
                continue

            if "weekly" in text:
                current_section = "weekly"
                continue

            # =================================================
            # ALWAYS ACCEPT ROW
            # =================================================
            item = str(row[0]).strip() or "UNKNOWN"
            sku = str(row[1]).strip()
            uom = str(row[2]).strip()

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
                    qty = float(val) if str(val).strip() != "" else 0
            except:
                qty = 0

            target[key][branch_name] = qty

    return daily, weekly

# =========================================================
# SYNC LOCK
# =========================================================

now = time.time()
can_sync = (now - sync_meta.get("last_sync", 0)) > SYNC_LOCK
remaining = max(0, int(SYNC_LOCK - (now - sync_meta.get("last_sync", 0))))

# =========================================================
# UI
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Date"):
        st.rerun()

with col2:
    if st.button("🔄 SYNC DATA"):

        if not can_sync:
            st.error(f"⛔ Locked for {remaining}s")
            st.stop()

        with st.spinner("Loading all branches..."):

            try:
                branches = load_branches_live()
                branch_names = [b["BranchName"] for b in branches]

                all_data = [
                    (b["BranchName"], fetch_sheet(b["SheetID"]))
                    for b in branches
                ]

                daily_items, weekly_items = process_stock(
                    all_data,
                    selected_date_str,
                    branch_names
                )

                save_cache({
                    "branches": branches,
                    "branch_names": branch_names,
                    "daily": daily_items,
                    "weekly": weekly_items
                })

                sync_meta["last_sync"] = now
                save_sync(sync_meta)

                st.success("Sync Done")
                st.rerun()

            except APIError as e:
                st.error(e)

with col3:
    if st.button("Back"):
        st.switch_page("app.py")

# =========================================================
# LOAD CACHE
# =========================================================

cache = load_cache()

if not cache:
    st.warning("No data. Run SYNC first.")
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
# AGGRID
# =========================================================

def get_width(series, min_width):
    try:
        series = series.fillna("").astype(str)
        return max(series.map(len).max() * 5 + 25, min_width)
    except:
        return min_width

def render_grid(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item Name", pinned="left", minWidth=180)
    gb.configure_column("SKU", pinned="left", minWidth=100)
    gb.configure_column("UOM", pinned="left", minWidth=90)

    for col in df.columns:
        if col not in ["Item Name", "SKU", "UOM"]:
            gb.configure_column(col, minWidth=get_width(df[col], 120))

    AgGrid(df, gridOptions=gb.build(), height=500, theme="streamlit")

render_grid(daily_df, "Daily Stock")
render_grid(weekly_df, "Weekly Stock")
