import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import time
import hashlib

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
# RETRY SETTINGS
# ========================================================

MAX_RETRIES = 10
RETRY_DELAY = 10

branch_cache = {}

# ========================================================
# FETCH BRANCH
# ========================================================

def fetch_branch(branch):

    name = branch["BranchName"]

    try:

        ws = client.open_by_key(
            branch["SheetID"]
        ).worksheet("Stocks")

        data = ws.get_all_values()

        branch_cache[name] = data

        return {
            "branch": name,
            "success": True,
            "data": data
        }

    except Exception:

        if name in branch_cache:

            return {
                "branch": name,
                "success": False,
                "data": branch_cache[name]
            }

        return {
            "branch": name,
            "success": False,
            "data": []
        }

# ========================================================
# LOAD ALL DATA
# ========================================================

@st.cache_data(ttl=None)
def load_all_data(branches):

    completed = {}
    failed = []

    progress = st.progress(0)
    status = st.empty()

    with ThreadPoolExecutor(max_workers=3) as ex:

        futures = {
            ex.submit(fetch_branch, b): b
            for b in branches
        }

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

    round_no = 1

    while failed and round_no <= MAX_RETRIES:

        failed_names = [b["BranchName"] for b in failed]

        with status.container():
            st.info(
                f"Retry {round_no}/{MAX_RETRIES} → "
                f"{', '.join(failed_names)}"
            )

        time.sleep(RETRY_DELAY)

        new_failed = []

        with ThreadPoolExecutor(max_workers=3) as ex:

            futures = {
                ex.submit(fetch_branch, b): b
                for b in failed
            }

            for f in as_completed(futures):

                r = f.result()

                name = r["branch"]

                if r["success"] or r["data"]:
                    completed[name] = r["data"]
                else:
                    new_failed.append(futures[f])

        failed = new_failed
        round_no += 1

    if failed:
        status.warning("Some branches still failed")
    else:
        status.empty()

    return [
        (
            b["BranchName"],
            completed.get(b["BranchName"], [])
        )
        for b in branches
    ]

all_data = load_all_data(branches)

# ========================================================
# REFRESH BUTTON
# ========================================================

if st.button("🔄 Refresh Data"):

    branch_cache.clear()
    st.cache_data.clear()
    st.cache_resource.clear()

    st.rerun()

# ========================================================
# DATE SELECTOR
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
            sku = str(row[1]).strip() if len(row) > 1 else ""
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
# BUILD DATAFRAME
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
# CATEGORY LOGIC
# ========================================================

def normalize_sku(value):
    return str(value).strip().upper()

def detect_category(sku):

    s = normalize_sku(sku)

    if s in FOOD_SKUS:
        return "FOOD ITEMS"

    if s in DRY_SKUS:
        return "DRY ITEMS"

    if s in MISC_SKUS:
        return "MISC ITEMS"

    return "MISC ITEMS"

def build_category(df):

    cats = {
        "FOOD ITEMS": [],
        "DRY ITEMS": [],
        "MISC ITEMS": []
    }

    for _, row in df.iterrows():

        cat = detect_category(row["SKU"])
        cats[cat].append(row.to_dict())

    for k in cats:
        cats[k] = sorted(
            cats[k],
            key=lambda x: str(x["Item Name"]).lower()
        )

    return cats

# ========================================================
# SAFE GRID KEY (FIX FOR ERROR 252)
# ========================================================

def stable_key(prefix, name):
    return prefix + "_" + hashlib.md5(str(name).encode()).hexdigest()

# ========================================================
# AGGRID (UNCHANGED VISUAL SPACING)
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
        width=250, minWidth=250, maxWidth=350,
    )

    gb.configure_column(
        "SKU",
        pinned="left",
        lockPinned=True,
        width=100, minWidth=100, maxWidth=350,
    )

    gb.configure_column(
        "UOM",
        pinned="left",
        lockPinned=True,
        width=100, minWidth=100, maxWidth=350,
    )

    for b in branch_names:

        gb.configure_column(
            b,
            type=["numericColumn"],
            wrapText=False,
            width=120, minWidth=120, maxWidth=350,
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

    AgGrid(
        df,
        gridOptions=gb.build(),
        custom_css={
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
        },
        theme="streamlit",
        fit_columns_on_grid_load=False,
        enable_enterprise_modules=False,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
        height=500,
        width="100%",
        key=key
    )

# ========================================================
# CATEGORY VIEW
# ========================================================

st.subheader("📊 Category Wise Stock Overview")

category_data = build_category(daily_df)

for cat, rows in category_data.items():

    with st.expander(f"📂 {cat} ({len(rows)})", expanded=False):

        if not rows:
            st.info("No items")
            continue

        df = pd.DataFrame(rows)

        make_grid(df, stable_key("cat", cat))

# ========================================================
# MAIN TABLES
# ========================================================

def render(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    make_grid(df, stable_key("grid", title))

render(daily_df, "📦 Daily Items Stock")
render(weekly_df, "📦 Weekly Items Stock")
