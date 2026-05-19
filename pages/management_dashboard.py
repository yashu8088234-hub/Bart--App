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


@st.cache_data(ttl=600)
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

    round_no = 1

    while failed and round_no <= MAX_RETRIES:

        failed_names = [b["BranchName"] for b in failed]

        with status.container():
            st.info(f"Retry {round_no}/{MAX_RETRIES} → {', '.join(failed_names)}")

        time.sleep(RETRY_DELAY)

        new_failed = []

        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {ex.submit(fetch_branch, b): b for b in failed}

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
# CLEANING + TOKEN SYSTEM (FIXED)
# ========================================================

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[\u0600-\u06FF]+", " ", text)
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_tokens(text):
    return set(clean_text(text).split())

# ========================================================
# STOCK PROCESSING (UNCHANGED LOGIC)
# ========================================================

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


daily_items, weekly_items = process_stock(all_data, selected_date_str, branch_names)

# ========================================================
# DATAFRAME BUILDER (UNCHANGED)
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
# CATEGORY RULES (UNCHANGED)
# ========================================================

CATEGORY_RULES = {
    "Food Items": [
        "cake","sauce","bread","chocolate","ice cream","juice","coffee",
        "milk","syrup","oil","egg","kunafa","kitkat","nutella","kinder",
        "galaxy","vanilla","cinnamon","sugar","pudding","lotus"
    ],

    "Packaging Items": [
        "cup","cups","lid","lids","box","boxes","tray","trays","bag","bags",
        "holder","holders","sticker","stickers","container","napkin","roll"
    ],

    "Cleaning & Hygiene": [
        "glove","gloves","mask","masks","apron","tissue","tissues",
        "sanitizer","scotch","sponge","hair net","cleaner"
    ],

    "Miscellaneous": [
        "toy","figurine","keychain","tool","plug","accessory"
    ]
}

# ========================================================
# CATEGORY FIXED ENGINE (MAIN FIX)
# ========================================================

def detect_category(name):

    text_tokens = normalize_tokens(name)
    text_clean = clean_text(name)

    best_category = "Miscellaneous"
    best_score = 0

    for category, keywords in CATEGORY_RULES.items():
        score = 0

        for k in keywords:
            k_clean = clean_text(k)
            k_tokens = set(k_clean.split())

            # SMART MATCH (token overlap OR substring fallback)
            if k_tokens & text_tokens:
                score += 1
            elif k_clean in text_clean:
                score += 1

        if score > best_score:
            best_score = score
            best_category = category

    return best_category


def build_category(df):

    cats = {
        "Food Items": [],
        "Packaging Items": [],
        "Cleaning & Hygiene": [],
        "Miscellaneous": []
    }

    for _, row in df.iterrows():
        cat = detect_category(row["Item Name"])
        cats[cat].append(row)

    # alphabetical sorting
    for k in cats:
        cats[k] = sorted(
            cats[k],
            key=lambda x: clean_text(x["Item Name"])
        )

    return cats

# ========================================================
# CATEGORY UI (FIXED AGGRID)
# ========================================================

st.subheader("📊 Category Wise Stock Overview")

category_data = build_category(daily_df)

for cat, rows in category_data.items():

    with st.expander(f"📂 {cat} ({len(rows)})"):

        if not rows:
            st.info("No items")
            continue

        df = pd.DataFrame(rows)

        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_default_column(
            resizable=True,
            sortable=True,
            filter=True,
            minWidth=90
        )

        gb.configure_grid_options(domLayout='autoHeight')

        AgGrid(
            df,
            gridOptions=gb.build(),
            theme="streamlit",
            fit_columns_on_grid_load=True,
            key=f"cat_{cat}"
        )

# ========================================================
# DAILY / WEEKLY TABLES (FIXED AGGRID)
# ========================================================

def render(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        minWidth=90
    )

    gb.configure_grid_options(domLayout='autoHeight')

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        fit_columns_on_grid_load=True,
        key=title
    )


render(daily_df, "📦 Daily Items Stock")
render(weekly_df, "📦 Weekly Items Stock")
