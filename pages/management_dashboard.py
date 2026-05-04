import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide", page_title="Stock Overview")

st.title("📦 BART - Stock Management (All Branches)")

# ---------------- GOOGLE AUTH ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ---------------- LOAD MASTER ----------------
master = client.open("MASTERBRANCHSHEET").sheet1
branches = master.get_all_records()

# 🔁 CHANGED: Branch Name → Branch Code
branch_codes = [b["BranchCode"] for b in branches]

all_items = {}

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%d/%m/%y").lstrip("0").replace("/0", "/")

# ---------------- FETCH DATA ----------------
for branch in branches:
    branch_code = branch["BranchCode"]
    sheet_id = branch["SheetID"]

    try:
        file = client.open_by_key(sheet_id)
        stock_sheet = file.worksheet("Stocks")
        data = pd.DataFrame(stock_sheet.get_all_records())

        if not data.empty:
            item_col = data.columns[0]

            for _, row in data.iterrows():
                item = str(row[item_col]).strip()

                if item not in all_items:
                    all_items[item] = {"raw_data": {}}

                # 🔁 CHANGED: store by branch_code
                all_items[item]["raw_data"][branch_code] = row

    except Exception as e:
        st.error(f"{branch_code} error: {e}")

# ---------------- BUILD FINAL TABLE ----------------
rows = []

for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}

    # 🔁 CHANGED: branch_code used
    for branch_code in branch_codes:
        try:
            branch_row = values.get("raw_data", {}).get(branch_code, {})
            qty = branch_row.get(selected_date_str, 0)
        except:
            qty = 0

        row[branch_code] = qty

    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- DISPLAY ----------------
st.dataframe(df, use_container_width=True)

# ---------------- LOW STOCK ALERT ----------------
st.markdown("## ⚠️ Low Stock Highlight")

def highlight_low(val):
    try:
        if float(val) == 0:
            return "background-color: red; color: white;"
        elif float(val) < 5:
            return "background-color: orange;"
    except:
        return ""
    return ""

# 🔁 CHANGED: subset uses branch_codes
styled_df = df.style.applymap(highlight_low, subset=branch_codes)

st.dataframe(styled_df, use_container_width=True)
