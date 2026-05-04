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

# ---------------- MASTER ----------------
master = client.open("MASTERBRANCHSHEET").sheet1
branches = master.get_all_records()

# 🔥 IMPORTANT:
# Code = display
# Name = real sheet source
branch_codes = [b["BranchCode"] for b in branches]

# mapping
branch_map = {
    b["BranchCode"]: {
        "name": b["BranchName"],   # used for sheet access
        "sheet": b["SheetID"]
    }
    for b in branches
}

# ---------------- CACHE ----------------
@st.cache_data(ttl=300)
def load_data(sheet_id):
    file = client.open_by_key(sheet_id)
    sheet = file.worksheet("Stocks")
    return pd.DataFrame(sheet.get_all_records())

# ---------------- DATE ----------------
selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%d/%m/%y").lstrip("0").replace("/0", "/")

# ---------------- DATA ----------------
all_items = {}

# ---------------- FETCH (IMPORTANT FIX HERE) ----------------
for code in branch_codes:
    branch_name = branch_map[code]["name"]   # 👈 REAL SHEET SOURCE
    sheet_id = branch_map[code]["sheet"]

    try:
        data = load_data(sheet_id)

        if not data.empty:
            item_col = data.columns[0]

            for _, row in data.iterrows():
                item = str(row[item_col]).strip()

                if item not in all_items:
                    all_items[item] = {"branches": {}}

                # store using CODE but data comes from NAME sheet
                all_items[item]["branches"][code] = row

    except Exception as e:
        st.error(f"{code} ({branch_name}) error: {e}")

# ---------------- BUILD TABLE ----------------
rows = []

for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}

    for code in branch_codes:
        try:
            branch_row = values.get("branches", {}).get(code, {})
            qty = branch_row.get(selected_date_str, 0)
        except:
            qty = 0

        row[code] = qty   # 👈 DISPLAY IS CODE

    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- DISPLAY ----------------
st.dataframe(df, use_container_width=True)

# ---------------- LOW STOCK ----------------
def highlight_low(val):
    try:
        if float(val) == 0:
            return "background-color: red; color: white;"
        elif float(val) < 5:
            return "background-color: orange;"
    except:
        return ""
    return ""

styled_df = df.style.applymap(highlight_low, subset=branch_codes)

st.dataframe(styled_df, use_container_width=True)
