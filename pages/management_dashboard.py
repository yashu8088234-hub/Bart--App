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

# ---------------- DATE (kept for consistency) ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

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
# 📦 DAILY + WEEKLY SEPARATION (FIXED LOGIC)
# =========================================================

daily_items = {}
weekly_items = {}

for branch_name, raw in all_data:

    if not raw or len(raw) < 2:
        continue

    headers = raw[0]
    rows = raw[1:]

    item_col = headers[0]

    df = pd.DataFrame(rows, columns=headers)

    current_section = None

    for _, row in df.iterrows():

        # detect section from row content (same as your Stock View logic)
        row_text = " ".join(str(x) for x in row.values).strip().lower()

        if "daily item" in row_text:
            current_section = "daily"
            continue

        if "weekly item" in row_text:
            current_section = "weekly"
            continue

        if current_section is None:
            continue

        item = str(row[item_col]).strip()

        if item == "" or item.lower() in ["daily item", "weekly item"]:
            continue

        values = row[1:]

        # convert safely
        total = 0
        for v in values:
            try:
                total += float(v) if v != "" else 0
            except:
                pass

        if current_section == "daily":
            if item not in daily_items:
                daily_items[item] = {bn: 0 for bn in branch_names}
            daily_items[item][branch_name] = total

        elif current_section == "weekly":
            if item not in weekly_items:
                weekly_items[item] = {bn: 0 for bn in branch_names}
            weekly_items[item][branch_name] = total

# =========================================================
# 📦 DAILY DATAFRAME
# =========================================================

daily_rows = []
for i, (item, values) in enumerate(daily_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    daily_rows.append(row)

df_daily = pd.DataFrame(daily_rows)

# =========================================================
# 📦 WEEKLY DATAFRAME
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

st.subheader("📦 Daily Items Stock (All Branches)")
st.dataframe(df_daily, use_container_width=True)

st.subheader("📦 Weekly Items Stock (All Branches)")
st.dataframe(df_weekly, use_container_width=True)
