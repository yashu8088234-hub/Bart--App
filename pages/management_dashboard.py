import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from ai_core import run_ai
from st_aggrid import AgGrid, GridOptionsBuilder

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
# SHEET CACHE (IMPORTANT SPEED BOOST)
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
# FAST FETCH (RANGE ONLY = BIG SPEED BOOST)
# =========================================================

@st.cache_data(ttl=600)
def fetch_sheet_range(sheet_id):
    try:
        ws = sheet_cache[sheet_id].worksheet("Stocks")
        return ws.get("A1:Z500")   # FAST instead of full sheet
    except:
        return None

def fetch_branch(branch):
    sid = branch.get("SheetID")
    if not sid or sid not in sheet_cache:
        return branch["BranchName"], None

    data = fetch_sheet_range(sid)
    return branch["BranchName"], data

# =========================================================
# LOAD ALL DATA (PARALLEL FAST)
# =========================================================

@st.cache_data(ttl=300)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=10) as ex:
        return list(ex.map(fetch_branch, branches))

all_data = load_all_data(branches)

# =========================================================
# DATE INPUT
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

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

        # FIND DATE COLUMN
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

            # FIRST 3 COLUMNS ONLY
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

# =========================================================
# RUN PROCESS
# =========================================================

daily_items, weekly_items = process_stock(
    all_data,
    selected_date_str,
    branch_names
)

# =========================================================
# DATAFRAME (NO SL NO)
# =========================================================

daily_rows = []

for _, v in daily_items.items():

    row = {
        "Item Name": v["Item Name"],
        "SKU": v["SKU"],
        "UOM": v["UOM"]
    }

    for b in branch_names:
        row[b] = v.get(b, 0)

    daily_rows.append(row)

daily_df = pd.DataFrame(daily_rows)

weekly_rows = []

for _, v in weekly_items.items():

    row = {
        "Item Name": v["Item Name"],
        "SKU": v["SKU"],
        "UOM": v["UOM"]
    }

    for b in branch_names:
        row[b] = v.get(b, 0)

    weekly_rows.append(row)

weekly_df = pd.DataFrame(weekly_rows)

# =========================================================
# AGGRID (FROZEN COLUMNS)
# =========================================================

st.subheader("📦 Daily Items Stock")

if not daily_df.empty:

    gb = GridOptionsBuilder.from_dataframe(daily_df)

    gb.configure_columns(
        ["Item Name", "SKU", "UOM"],
        pinned="left"
    )

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )

    AgGrid(
        daily_df,
        gridOptions=gb.build(),
        fit_columns_on_grid_load=True
    )

else:
    st.warning("No Daily Data")

# ---------------- WEEKLY ----------------

st.subheader("📦 Weekly Items Stock")

if not weekly_df.empty:

    gb = GridOptionsBuilder.from_dataframe(weekly_df)

    gb.configure_columns(
        ["Item Name", "SKU", "UOM"],
        pinned="left"
    )

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )

    AgGrid(
        weekly_df,
        gridOptions=gb.build(),
        fit_columns_on_grid_load=True
    )

else:
    st.warning("No Weekly Data")

# =========================================================
# DOWNLOAD
# =========================================================

st.download_button(
    "📥 Download Daily CSV",
    daily_df.to_csv(index=False),
    file_name="daily_stock.csv",
    mime="text/csv"
)

st.download_button(
    "📥 Download Weekly CSV",
    weekly_df.to_csv(index=False),
    file_name="weekly_stock.csv",
    mime="text/csv"
)
