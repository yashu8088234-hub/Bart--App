import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from dateutil import parser
import time
import re

# ========================================================
# PAGE CONFIG
# ========================================================

st.set_page_config(
    layout="wide",
    page_title="Stock Overview"
)

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
# CACHE
# ========================================================

branch_cache = {}

# ========================================================
# FETCH BRANCH
# ========================================================

def fetch_branch(branch):

    name = branch["BranchName"]

    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        data = ws.get_all_values()

        branch_cache[name] = data

        return {"branch": name, "success": True, "data": data}

    except Exception:
        return {
            "branch": name,
            "success": False,
            "data": branch_cache.get(name, [])
        }

# ========================================================
# LOAD ALL DATA
# ========================================================

@st.cache_data(ttl=None)
def load_all_data(branches):

    completed = {}
    failed = []

    progress = st.progress(0)

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
# DATE
# ========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ========================================================
# PROCESS STOCK
# ========================================================

@st.cache_data(ttl=None)
def process_stock(all_data, selected_date_str, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = [str(x).strip() for x in raw[0]]

        date_index = None

        for i, h in enumerate(headers):
            try:
                parsed = parser.parse(str(h)).strftime("%Y-%m-%d")
                if parsed == selected_date_str:
                    date_index = i
                    break
            except:
                pass

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
            sku = (
                re.sub(r"[^A-Z0-9()&-]", "", str(row[1]).upper())
                if len(row) > 1 else ""
            )
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

daily_items, weekly_items = process_stock(
    all_data,
    selected_date_str,
    branch_names
)

# ========================================================
# DATAFRAME BUILDER (FIXED)
# ========================================================

def build_df(data_dict):

    df = pd.DataFrame(list(data_dict.values()))

    if df.empty:
        return df

    # ensure all branch columns exist
    for b in branch_names:
        if b not in df.columns:
            df[b] = 0

    # force correct order
    df = df[["Item Name", "SKU", "UOM"] + branch_names]

    # numeric cleanup
    for b in branch_names:
        df[b] = pd.to_numeric(df[b], errors="coerce").fillna(0)

    return df

daily_df = build_df(daily_items)
weekly_df = build_df(weekly_items)

# ========================================================
# CATEGORY DETECTION (UNCHANGED LOGIC)
# ========================================================

MISC_SKUS = set(["T063","T060","T066","TOY1","T026","SVP","P089","P130"])

DRY_SKUS = set([
    "C013","P244","P254","P320","P322","P321","P095","P296","C014",
    "P337","P125","P298","P178","P343(1)","P343","CF009"
])

FOOD_SKUS = set([
    "B034","F066","CB032","B029","K072","CB009","F081","-","B019",
    "B018","CF007","CF006","F148"
])

def detect_category(sku):

    sku = re.sub(r"[^A-Z0-9()&-]", "", str(sku).upper())

    if sku in FOOD_SKUS:
        return "FOOD ITEMS"

    if sku in DRY_SKUS:
        return "DRY ITEMS"

    if sku in MISC_SKUS:
        return "Miscellaneous"

    return "Uncategorized"

def filter_category(df, cat_name):

    if df.empty:
        return df

    df2 = df.copy()
    df2["Category"] = df2["SKU"].apply(detect_category)

    return df2[df2["Category"] == cat_name].drop(columns=["Category"])

# ========================================================
# AGGRID (YOUR ORIGINAL UI — RESTORED)
# ========================================================

def make_grid(df, key):

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        resizable=False,
        sortable=True,
        filter=True,
        editable=False,
        wrapText=False,
        autoHeight=False,
        cellStyle={
            "display": "flex",
            "alignItems": "center",
            "fontSize": "13px",
            "paddingTop": "0px",
            "paddingBottom": "0px"
        }
    )

    gb.configure_column(
        "Item Name",
        pinned="left",
        lockPinned=True,
        width=250,
        minWidth=250,
        maxWidth=350,
    )

    gb.configure_column(
        "SKU",
        pinned="left",
        lockPinned=True,
        width=100,
        minWidth=100,
        maxWidth=350,
    )

    gb.configure_column(
        "UOM",
        pinned="left",
        lockPinned=True,
        width=100,
        minWidth=100,
        maxWidth=350,
    )

    for b in branch_names:
        gb.configure_column(
            b,
            type=["numericColumn"],
            wrapText=False,
            width=120,
            minWidth=120,
            maxWidth=350,
            autoHeight=False,
            cellStyle={
                "textAlign": "center",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "fontSize": "13px",
                "paddingTop": "0px",
                "paddingBottom": "0px"
            }
        )

    gb.configure_grid_options(
        headerHeight=38,
        rowHeight=32,
        suppressHorizontalScroll=False,
        alwaysShowHorizontalScroll=True,
        alwaysShowVerticalScroll=True
    )

    custom_css = {
        ".ag-header-cell-label": {
            "justify-content": "center",
            "font-size": "12px",
            "font-weight": "600"
        },
        ".ag-header-cell": {
            "padding-top": "0px",
            "padding-bottom": "0px"
        },
        ".ag-cell": {
            "padding-top": "0px",
            "padding-bottom": "0px"
        }
    }

    AgGrid(
        df,
        gridOptions=gb.build(),
        custom_css=custom_css,
        theme="streamlit",
        fit_columns_on_grid_load=False,
        enable_enterprise_modules=False,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True,
        reload_data=True,
        height=500,
        width="100%",
        key=key
    )

# ========================================================
# CATEGORY VIEW (FIXED ONLY DATA PART)
# ========================================================

st.subheader("📊 Category Wise Stock Overview")

for cat in ["FOOD ITEMS", "DRY ITEMS", "Miscellaneous", "Uncategorized"]:

    with st.expander(f"📂 {cat} ({len(daily_df) if not daily_df.empty else 0})", expanded=False):

        df_cat = filter_category(daily_df, cat)

        if not df_cat.empty:
            df_cat = df_cat[["Item Name", "SKU", "UOM"] + branch_names]

        make_grid(df_cat, f"cat_{cat}")

# ========================================================
# MAIN TABLES
# ========================================================

def render(df, title):
    st.subheader(title)
    make_grid(df, title)

render(daily_df, "📦 Daily Items Stock")
render(weekly_df, "📦 Weekly Items Stock")

# ========================================================
# REFRESH
# ========================================================

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.cache_resource.clear()
    branch_cache.clear()
    st.rerun()
