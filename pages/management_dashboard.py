import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from dateutil import parser
import time

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
# LOAD BRANCHES
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
# FETCH DATA
# ========================================================

def fetch_branch(branch):
    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        data = ws.get_all_values()

        return {
            "branch": branch["BranchName"],
            "success": True,
            "data": data
        }
    except:
        return {
            "branch": branch["BranchName"],
            "success": False,
            "data": []
        }

# ========================================================
# LOAD ALL DATA
# ========================================================

@st.cache_data(ttl=None)
def load_all_data(branches):

    results = []

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(fetch_branch, b) for b in branches]

        for f in as_completed(futures):
            r = f.result()
            results.append((r["branch"], r["data"]))

    return results

all_data = load_all_data(branches)

# ========================================================
# REFRESH
# ========================================================

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# ========================================================
# DATE
# ========================================================

selected_date = st.date_input("Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ========================================================
# PROCESS STOCK (FIXED DATE MATCH)
# ========================================================

def process_stock(all_data, selected_date_str, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        # FIX: robust header parsing
        headers = []
        for x in raw[0]:
            try:
                headers.append(parser.parse(str(x)).strftime("%Y-%m-%d"))
            except:
                headers.append(str(x).strip())

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

            if "weekly item" in text:
                mode = "weekly"
                continue

            if not mode:
                continue

            item = str(row[0]).strip() if len(row) > 0 else ""
            sku = str(row[1]).strip().upper() if len(row) > 1 else ""
            uom = str(row[2]).strip() if len(row) > 2 else ""

            if not item:
                continue

            key = f"{item}_{sku}_{uom}"

            target = daily if mode == "daily" else weekly

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
                    qty = 0 if val in ["", None] else float(val)
            except:
                qty = 0

            target[key][branch_name] = qty

    return daily, weekly

daily_items, weekly_items = process_stock(all_data, selected_date_str, branch_names)

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
weekly_df = build_df(weekly_items)

# ========================================================
# SKU LISTS
# ========================================================

FOOD_SKUS = {"B034","F066","CB032","B029","K072","CB009","F081","B019","B018"}
DRY_SKUS = {"C013","P244","P254","P320","P322","P321","P095","P296"}
MISC_SKUS = {"T063","T060","T066","TOY1","T026"}

# ========================================================
# CATEGORY (FIXED SIMPLE MATCH)
# ========================================================

def detect_category(sku):

    sku = str(sku).strip().upper()

    if sku in FOOD_SKUS:
        return "FOOD ITEMS"

    if sku in DRY_SKUS:
        return "DRY ITEMS"

    if sku in MISC_SKUS:
        return "Miscellaneous"

    return "Uncategorized"

# ========================================================
# CATEGORY BUILD
# ========================================================

def build_category(df):

    cats = {
        "FOOD ITEMS": [],
        "DRY ITEMS": [],
        "Miscellaneous": [],
        "Uncategorized": []
    }

    for _, row in df.iterrows():
        cats[detect_category(row["SKU"])].append(row.to_dict())

    return cats

# ========================================================
# GRID
# ========================================================

def make_grid(df, key):

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(sortable=True, filter=True)

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        update_mode=GridUpdateMode.NO_UPDATE,
        height=500,
        key=key
    )

# ========================================================
# CATEGORY VIEW
# ========================================================

st.subheader("Category Wise Stock")

category_data = build_category(daily_df)

for cat, rows in category_data.items():

    with st.expander(f"{cat} ({len(rows)})"):

        if not rows:
            st.info("No items")
            continue

        make_grid(pd.DataFrame(rows), cat)

# ========================================================
# TABLES
# ========================================================

st.subheader("Daily Stock")
make_grid(daily_df, "daily")

st.subheader("Weekly Stock")
make_grid(weekly_df, "weekly")
