import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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

branch_names = [b["BranchName"] for b in branches]

all_items = {}

# ---------------- FETCH DATA ----------------
for branch in branches:
    branch_name = branch["BranchName"]
    sheet_id = branch["SheetID"]

    try:
        file = client.open_by_key(sheet_id)
        stock_sheet = file.worksheet("Stocks")
        data = pd.DataFrame(stock_sheet.get_all_records())

        if not data.empty:
            item_col = data.columns[0]
            latest_col = data.columns[-1]

            for _, row in data.iterrows():
                item = str(row[item_col]).strip()
                qty = row[latest_col]

                if item not in all_items:
                    all_items[item] = {bn: 0 for bn in branch_names}

                all_items[item][branch_name] = qty

    except Exception as e:
        st.error(f"{branch_name} error: {e}")

# ---------------- BUILD FINAL TABLE ----------------
rows = []
for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
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

styled_df = df.style.applymap(highlight_low, subset=branch_names)

st.dataframe(styled_df, use_container_width=True)









