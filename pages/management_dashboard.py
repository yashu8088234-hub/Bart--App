import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
import time
import re

# ========================================================
# PAGE CONFIG
# ========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# ========================================================
# GOOGLE AUTH
# ========================================================

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

# ========================================================
# BRANCHES
# ========================================================

@st.cache_data(ttl=None)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()

    branches = []
    for b in data:
        if b.get("SheetID") and b.get("BranchName"):
            branches.append({
                "BranchName": str(b["BranchName"]).strip(),
                "SheetID": str(b["SheetID"]).strip()
            })

    return branches

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ========================================================
# RETRY SYSTEM
# ========================================================

MAX_RETRIES = 10
RETRY_DELAY = 60
branch_cache = {}

def fetch_branch(branch):
    name = branch["BranchName"]

    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        data = ws.get_all_values()

        branch_cache[name] = data

        return {"branch": name, "success": True, "data": data}

    except Exception:
        if name in branch_cache:
            return {"branch": name, "success": False, "data": branch_cache[name]}

        return {"branch": name, "success": False, "data": []}


@st.cache_data(ttl=None)
def load_all_data(branches):

    completed = {}
    failed = []

    progress = st.progress(0)
    status = st.empty()

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_branch, b): b for b in branches}

        done = 0

        for f in as_completed(futures):
            r = f.result()
            name = r["branch"]

            if r["success"] or r["data"]:
                completed[name] = r["data"]
            else:
                failed.append(futures[f])

            done += 1
            progress.progress(done / len(branches))

    return [(b["BranchName"], completed.get(b["BranchName"], [])) for b in branches]


all_data = load_all_data(branches)

# ========================================================
# REFRESH
# ========================================================

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.cache_resource.clear()
    branch_cache.clear()
    st.rerun()

# ========================================================
# DATE
# ========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ========================================================
# CLEANING
# ========================================================

def clean_text(text):
    text = str(text).replace("\xa0", " ")
    text = text.lower()
    text = re.sub(r"[\u0600-\u06FF]+", " ", text)
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ========================================================
# STOCK PROCESSING
# ========================================================

@st.cache_data(ttl=None)
def process_stock(all_data, selected_date_str, branch_names):

    daily = {}

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = [str(x).strip() for x in raw[0]]

        date_index = None
        for i, h in enumerate(headers):
            if h == selected_date_str:
                date_index = i
                break

        mode = None

        for row in raw:

            if not row:
                continue

            text = " ".join(str(x) for x in row).lower()

            if "daily item" in text:
                mode = "daily"
                continue

            if not mode:
                continue

            item = str(row[0]).strip() if len(row) > 0 else ""
            sku = str(row[1]).strip() if len(row) > 1 else ""
            uom = str(row[2]).strip() if len(row) > 2 else ""

            if not item:
                continue

            key = f"{item}_{sku}_{uom}"

            if key not in daily:
                daily[key] = {
                    "Item Name": item,
                    "SKU": sku,
                    "UOM": uom
                }

                for b in branch_names:
                    daily[key][b] = 0

            qty = 0
            try:
                if date_index is not None and len(row) > date_index:
                    val = row[date_index]
                    qty = 0 if val in ["", None] else float(val)
            except:
                qty = 0

            daily[key][branch_name] = qty

    return daily


daily_items = process_stock(all_data, selected_date_str, branch_names)

# ========================================================
# DATAFRAME
# ========================================================

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

# ========================================================
# CATEGORY SYSTEM (KEEPING SIMPLE)
# ========================================================

def detect_category(name):
    return "FOOD ITEMS"

def build_category(df):
    return {"FOOD ITEMS": df.to_dict("records")}

# ========================================================
# TOTAL ROW BUILDER (NEW)
# ========================================================

def build_total_row(df):

    total = {
        "Item Name": "TOTAL",
        "SKU": "",
        "UOM": ""
    }

    for col in df.columns:
        if col not in ["Item Name", "SKU", "UOM"]:
            total[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).sum()

    return total

# ========================================================
# GRID (STICKY + PIN + TOTAL ROW)
# ========================================================

def make_grid(df, key):

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        wrapText=False,
        autoHeight=True
    )

    # PIN FIRST 3
    gb.configure_column("Item Name", pinned="left")
    gb.configure_column("SKU", pinned="left")
    gb.configure_column("UOM", pinned="left")

    # STICKY HEADER
    gb.configure_grid_options(
        domLayout='normal',
        suppressColumnVirtualisation=False,
        enableStickyHeader=True
    )

    # TOTAL ROW (PINNED BOTTOM)
    pinned_bottom = [build_total_row(df)]

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        height=550,
        pinnedBottomRowData=pinned_bottom,
        key=key
    )

# ========================================================
# CATEGORY UI
# ========================================================

st.subheader("📊 Category Wise Stock Overview")

category_data = build_category(daily_df)

for cat, rows in category_data.items():

    with st.expander(f"📂 {cat} ({len(rows)})"):

        df = pd.DataFrame(rows)
        make_grid(df, f"cat_{cat}")

# ========================================================
# TABLE
# ========================================================

st.subheader("📦 Daily Items Stock")
make_grid(daily_df, "daily")
