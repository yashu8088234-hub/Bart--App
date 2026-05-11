import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from ai_core import run_ai

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
# BRANCH LIST
# =========================================================

@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SHEET CACHE
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
# FETCH DATA
# =========================================================

def fetch_branch(branch):
    try:
        sid = branch.get("SheetID")
        if not sid or sid not in sheet_cache:
            return branch["BranchName"], None

        ws = sheet_cache[sid].worksheet("Stocks")
        return branch["BranchName"], ws.get_all_values()

    except:
        return branch["BranchName"], None

# =========================================================
# LOAD ALL DATA
# =========================================================

@st.cache_data(ttl=300)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=3) as ex:
        return list(ex.map(fetch_branch, branches))

all_data = load_all_data(branches)

# =========================================================
# DATE INPUT
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# PROCESS STOCK (DAILY + WEEKLY LOGIC PRESERVED)
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

            # KEEP ORIGINAL LOGIC
            if "daily item" in text:
                current_section = "daily"
                continue

            if "weekly item" in text:
                current_section = "weekly"
                continue

            if current_section is None:
                continue

            # FIRST 3 COLUMNS FIXED
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

            # VALUE FROM DATE COLUMN
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
# DATAFRAME (FIRST 3 FIXED COLUMNS)
# =========================================================

# DAILY
daily_rows = []

for i, (_, v) in enumerate(daily_items.items()):

    row = {
        "Sl No": i + 1,
        "Item Name": v["Item Name"],
        "SKU": v["SKU"],
        "UOM": v["UOM"]
    }

    for b in branch_names:
        row[b] = v.get(b, 0)

    daily_rows.append(row)

daily_df = pd.DataFrame(daily_rows)

# WEEKLY
weekly_rows = []

for i, (_, v) in enumerate(weekly_items.items()):

    row = {
        "Sl No": i + 1,
        "Item Name": v["Item Name"],
        "SKU": v["SKU"],
        "UOM": v["UOM"]
    }

    for b in branch_names:
        row[b] = v.get(b, 0)

    weekly_rows.append(row)

weekly_df = pd.DataFrame(weekly_rows)

# =========================================================
# DISPLAY
# =========================================================

st.subheader("📦 Daily Items Stock")
st.dataframe(daily_df, use_container_width=True)

st.subheader("📦 Weekly Items Stock")
st.dataframe(weekly_df, use_container_width=True)

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
