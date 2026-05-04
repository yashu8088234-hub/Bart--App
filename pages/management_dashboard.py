import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime
import time
import random

st.set_page_config(layout="wide", page_title="Stock Overview")

st.title("📦 BART - Stock Management (All Branches)")

# ---------------- GOOGLE AUTH ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ---------------- RETRY WRAPPER (QUOTA SAFE) ----------------
def safe_call(func, retries=5):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            wait = (2 ** i) + random.random()
            time.sleep(wait)
    return None

# ---------------- LOAD MASTER (CACHED) ----------------
@st.cache_data(ttl=600)
def load_branches():
    master = client.open("MASTERBRANCHSHEET").sheet1
    return master.get_all_records()

branches = load_branches()

# KEEP EXACT NAMES
branch_names = [b["BranchName"] for b in branches]

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")

all_items = {}

# ---------------- FETCH DATA (OPTIMIZED) ----------------
for branch in branches:
    branch_name = branch["BranchName"]
    sheet_id = branch["SheetID"]

    try:
        file = client.open_by_key(sheet_id)
        stock_sheet = file.worksheet("Stocks")

        # ⚡ FASTER THAN get_all_records()
        data = safe_call(lambda: stock_sheet.get_all_values())

        if not data or len(data) < 2:
            continue

        headers = data[0]
        rows_data = data[1:]

        item_col = headers[0]

        # ---------------- DATE MAP ----------------
        date_map = {}
        for idx, col in enumerate(headers[1:], start=1):
            try:
                col_date = datetime.datetime.strptime(col, "%d/%m/%y").date()
                date_map[col_date] = idx
            except:
                continue

        if selected_date not in date_map:
            continue

        col_index = date_map[selected_date]

        # ---------------- PROCESS ROWS ----------------
        for row in rows_data:
            if len(row) <= col_index:
                continue

            item = str(row[0]).strip()
            qty = row[col_index]

            if item not in all_items:
                all_items[item] = {bn: 0 for bn in branch_names}

            try:
                all_items[item][branch_name] = float(qty) if qty != "" else 0
            except:
                all_items[item][branch_name] = 0

    except Exception as e:
        st.warning(f"{branch_name} error: {e}")

# ---------------- FINAL TABLE ----------------
rows = []
for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- DISPLAY ----------------
st.subheader("📊 Stock Data")
st.dataframe(df, use_container_width=True)

# ---------------- LOW STOCK ----------------
st.markdown("## ⚠️ Low Stock Highlight")

def highlight_low(val):
    try:
        val = float(val)
        if val == 0:
            return "background-color: red; color: white;"
        elif val < 5:
            return "background-color: orange;"
    except:
        return ""
    return ""

styled_df = df.style.applymap(highlight_low, subset=branch_names)

st.dataframe(styled_df, use_container_width=True)
