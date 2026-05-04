import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Stock Overview")

st.title("📦 BART - Stock Management (All Branches)")

# ---------------- GOOGLE AUTH (OPTIMIZED) ----------------
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

# ---------------- LOAD MASTER (CACHE ONLY) ----------------
@st.cache_data(ttl=600)
def load_branches():
    master = client.open("MASTERBRANCHSHEET").sheet1
    return master.get_all_records()

branches = load_branches()

branch_names = [b["BranchName"] for b in branches]

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")

all_items = {}

# ---------------- CACHE SHEET DATA ONLY ----------------
@st.cache_data(ttl=300)
def get_sheet_data(sheet_id):
    file = client.open_by_key(sheet_id)
    sheet = file.worksheet("Stocks")
    return sheet.get_all_records()

# ---------------- FETCH DATA ----------------
for branch in branches:
    branch_name = branch["BranchName"]
    sheet_id = branch["SheetID"]

    try:
        data = pd.DataFrame(get_sheet_data(sheet_id))

        if data.empty:
            continue

        item_col = data.columns[0]

        # ---------------- DATE MAP ----------------
        date_map = {}
        for col in data.columns[1:]:
            try:
                col_date = datetime.datetime.strptime(col, "%d/%m/%y").date()
                date_map[col_date] = col
            except:
                pass

        if selected_date not in date_map:
            continue

        chosen_col = date_map[selected_date]

        # ---------------- BUILD DATA ----------------
        for _, row in data.iterrows():
            item = str(row[item_col]).strip()
            qty = row[chosen_col]

            if item not in all_items:
                all_items[item] = {bn: 0 for bn in branch_names}

            all_items[item][branch_name] = qty

    except Exception as e:
        st.error(f"{branch_name} error: {e}")

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
