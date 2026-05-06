import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime
import time

st.set_page_config(layout="wide", page_title="Stock Overview")

st.title("📦 BART - Stock Management (All Branches)")

# ---------------- GOOGLE AUTH ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = get_client()

# ---------------- MASTER SHEET ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ---------------- DATE ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ---------------- REFRESH ----------------
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ---------------- FETCH ----------------
@st.cache_data(ttl=600)
def get_all_sheets(branches):
    results = []
    cache = {}

    for branch in branches:
        sheet_id = branch["SheetID"]
        branch_name = branch["BranchName"]

        try:
            if sheet_id not in cache:
                cache[sheet_id] = client.open_by_key(sheet_id)

            ws = cache[sheet_id].worksheet("Stocks")
            raw = ws.get_all_values()

            results.append((branch_name, raw))
            time.sleep(0.2)

        except Exception:
            results.append((branch_name, None))

    return results

all_data = get_all_sheets(branches)

# =========================================================
# 📦 CLEAN STRUCTURES
# =========================================================

daily_items = {}
weekly_items = {}

# =========================================================
# 📦 PROCESS EACH BRANCH
# =========================================================

for branch_name, raw in all_data:

    if not raw or len(raw) < 2:
        continue

    headers = raw[0]
    rows = raw[1:]

    current_section = None

    # DAILY COLUMNS (dates)
    date_columns = headers[1:] if len(headers) > 1 else []

    for row in rows:

        if not row:
            continue

        row_text = " ".join(row).strip().lower()

        # detect sections
        if "daily item" in row_text:
            current_section = "daily"
            continue

        if "weekly item" in row_text:
            current_section = "weekly"
            continue

        if current_section is None:
            continue

        item = str(row[0]).strip()

        if not item:
            continue

        # skip headers accidentally repeated
        if "daily item" in item.lower() or "weekly item" in item.lower():
            continue

        values = row[1:]

        # =====================================================
        # DAILY LOGIC (MATCH BY DATE COLUMN)
        # =====================================================
        if current_section == "daily":

            if selected_date_str not in headers:
                continue

            col_index = headers.index(selected_date_str)

            # safe extraction (NO CRASH EVER)
            val = ""
            if col_index < len(row):
                val = row[col_index]

            if item not in daily_items:
                daily_items[item] = {bn: "" for bn in branch_names}

            daily_items[item][branch_name] = val

        # =====================================================
        # WEEKLY LOGIC (RAW ROW FIRST VALUE ONLY)
        # =====================================================
        elif current_section == "weekly":

            val = values[0] if len(values) > 0 else ""

            if item not in weekly_items:
                weekly_items[item] = {bn: "" for bn in branch_names}

            weekly_items[item][branch_name] = val

# =========================================================
# 📊 DAILY DATAFRAME
# =========================================================

daily_rows = []
for i, (item, values) in enumerate(daily_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    daily_rows.append(row)

df_daily = pd.DataFrame(daily_rows)

# =========================================================
# 📊 WEEKLY DATAFRAME
# =========================================================

weekly_rows = []
for i, (item, values) in enumerate(weekly_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    weekly_rows.append(row)

df_weekly = pd.DataFrame(weekly_rows)

# =========================================================
# 📊 DISPLAY
# =========================================================

st.subheader("📦 Daily Items Stock")
st.dataframe(df_daily, use_container_width=True)

st.subheader("📦 Weekly Items Stock")
st.dataframe(df_weekly, use_container_width=True)
