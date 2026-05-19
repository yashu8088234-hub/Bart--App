import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
import time

# ========================================================
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
# RETRY CONFIG
# =========================================================

MAX_RETRIES = 10
RETRY_DELAY = 60

branch_cache = {}

# ========================================================
# FETCH BRANCH
# =========================================================

def fetch_branch(branch):
    branch_name = branch["BranchName"]

    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        data = ws.get_all_values()

        branch_cache[branch_name] = data

        return {
            "branch": branch_name,
            "success": True,
            "data": data
        }

    except Exception as e:

        if branch_name in branch_cache:
            return {
                "branch": branch_name,
                "success": False,
                "data": branch_cache[branch_name]
            }

        return {
            "branch": branch_name,
            "success": False,
            "data": []
        }

# ========================================================
# LOAD ALL DATA (ROBUST)
# =========================================================

@st.cache_data(ttl=600)
def load_all_data(branches):

    completed = {}
    failed = []

    progress = st.progress(0)
    status = st.empty()

    # INITIAL LOAD
    with ThreadPoolExecutor(max_workers=3) as ex:

        futures = {ex.submit(fetch_branch, b): b for b in branches}

        done = 0

        for f in as_completed(futures):

            res = f.result()
            name = res["branch"]

            if res["success"] or res["data"]:
                completed[name] = res["data"]
            else:
                failed.append(futures[f])

            done += 1
            progress.progress(done / len(branches))

    # RETRY LOOP (compact UI)
    retry_round = 1

    while failed and retry_round <= MAX_RETRIES:

        failed_names = [b["BranchName"] for b in failed]

        with status.container():
            st.info(
                f"Retry {retry_round}/{MAX_RETRIES}\n\nFailed: {', '.join(failed_names)}"
            )

        time.sleep(RETRY_DELAY)

        new_failed = []

        with ThreadPoolExecutor(max_workers=3) as ex:

            futures = {ex.submit(fetch_branch, b): b for b in failed}

            for f in as_completed(futures):

                res = f.result()
                name = res["branch"]

                if res["success"] or res["data"]:
                    completed[name] = res["data"]
                else:
                    new_failed.append(futures[f])

        failed = new_failed
        retry_round += 1

    if failed:
        status.warning("Some branches still failed")
    else:
        status.empty()

    ordered = []
    for b in branches:
        ordered.append((b["BranchName"], completed.get(b["BranchName"], [])))

    return ordered

all_data = load_all_data(branches)

# ========================================================
# REFRESH
# =========================================================

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.cache_resource.clear()
    branch_cache.clear()
    st.rerun()

# ========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ========================================================
# PROCESS STOCK
# =========================================================

@st.cache_data(ttl=600)
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

        current = None

        for row in raw:

            if not row:
                continue

            text = " ".join(str(x) for x in row).lower()

            if "daily item" in text:
                current = "daily"
                continue

            if "weekly item" in text:
                current = "weekly"
                continue

            if not current:
                continue

            item = str(row[0]).strip() if len(row) > 0 else ""
            sku = str(row[1]).strip() if len(row) > 1 else ""
            uom = str(row[2]).strip() if len(row) > 2 else ""

            if not item:
                continue

            key = f"{item}_{sku}_{uom}"

            target = daily if current == "daily" else weekly

            if key not in target:
                target[key] = {"Item Name": item, "SKU": sku, "UOM": uom}
                for bn in branch_names:
                    target[key][bn] = 0

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

# ========================================================
# CATEGORY SYSTEM (NEW ADDITION ONLY)
# =========================================================

CATEGORY_MAP = {
    "Food Items": [
        "cake","sauce","bread","chocolate","ice cream","juice",
        "coffee","milk","syrup","oil","egg","kunafa","kitkat",
        "nutella","kinder","galaxy","vanilla","cinnamon","sugar"
    ],

    "Packaging Items": [
        "cup","lid","box","tray","bag","holder","sticker",
        "paper cup","plastic cup","container","napkin","roll"
    ],

    "Cleaning & Hygiene": [
        "glove","mask","apron","tissue","sanitizer",
        "scotch","sponge","hair net","cleaner"
    ],

    "Miscellaneous": [
        "toy","figurine","keychain","tool","plug","accessory"
    ]
}

def detect_category(name):

    name = str(name).lower()

    for cat, keys in CATEGORY_MAP.items():
        for k in keys:
            if k in name:
                return cat

    return "Miscellaneous"


def build_category(df):

    categories = {
        "Food Items": [],
        "Packaging Items": [],
        "Cleaning & Hygiene": [],
        "Miscellaneous": []
    }

    for _, row in df.iterrows():

        cat = detect_category(row["Item Name"])
        categories[cat].append(row)

    for k in categories:
        categories[k] = sorted(categories[k], key=lambda x: str(x["Item Name"]).lower())

    return categories

# ========================================================
# CATEGORY UI (NEW TOP SECTION)
# =========================================================

st.subheader("📊 Category Wise Stock Overview")

category_data = build_category(daily_df)

for cat, rows in category_data.items():

    with st.expander(f"📂 {cat} ({len(rows)})"):

        if not rows:
            st.info("No items")
            continue

        df = pd.DataFrame(rows)

        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_column("Item Name", pinned="left", minWidth=150)
        gb.configure_column("SKU", minWidth=80)
        gb.configure_column("UOM", minWidth=80)

        for col in branch_names:
            if col in df.columns:
                gb.configure_column(col, minWidth=100)

        gb.configure_default_column(resizable=True, sortable=True, filter=True)

        AgGrid(
            df,
            gridOptions=gb.build(),
            theme="streamlit",
            fit_columns_on_grid_load=True,
            key=f"cat_{cat}"
        )

# ========================================================
# DAILY / WEEKLY (UNCHANGED)
# =========================================================

def render(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item Name", pinned="left")
    gb.configure_column("SKU", pinned="left")
    gb.configure_column("UOM", pinned="left")

    for col in branch_names:
        gb.configure_column(col, minWidth=120)

    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    AgGrid(df, gridOptions=gb.build(), theme="streamlit", fit_columns_on_grid_load=True, key=title)

render(daily_df, "📦 Daily Items Stock")
render(weekly_df, "📦 Weekly Items Stock")
