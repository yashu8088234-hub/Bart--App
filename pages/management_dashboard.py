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

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ---------------- SAFE FETCH ----------------
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
# 📊 DAILY + WEEKLY DATA BUILD
# =========================================================

daily_items = {}
weekly_items = {}

for branch_name, raw in all_data:

    if not raw or len(raw) < 2:
        continue

    headers = raw[0]
    rows = raw[1:]

    df = pd.DataFrame(rows, columns=headers)
    item_col = headers[0]

    # ---------------- DAILY (selected date) ----------------
    if selected_date_str in headers:

        for _, row in df.iterrows():
            item = str(row[item_col]).strip()
            qty = row.get(selected_date_str, "")

            if item not in daily_items:
                daily_items[item] = {bn: 0 for bn in branch_names}

            try:
                daily_items[item][branch_name] = float(qty) if qty != "" else 0
            except:
                daily_items[item][branch_name] = 0

    # ---------------- WEEKLY (last 7 columns sum) ----------------
    date_cols = headers[1:]
    last_7 = date_cols[-7:] if len(date_cols) >= 7 else date_cols

    for _, row in df.iterrows():
        item = str(row[item_col]).strip()

        if item not in weekly_items:
            weekly_items[item] = {bn: 0 for bn in branch_names}

        total = 0
        for d in last_7:
            try:
                total += float(row.get(d, 0) or 0)
            except:
                pass

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

st.subheader("📊 Daily Stock Data (All Branches)")
st.dataframe(df_daily, use_container_width=True)

st.subheader("📊 Weekly Stock Data (All Branches)")
st.dataframe(df_weekly, use_container_width=True)
