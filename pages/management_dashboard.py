import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime

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

# ---------------- LOAD MASTER SHEET ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branches = load_branches()

# KEEP EXACT NAMES (IMPORTANT)
branch_names = [b["BranchName"] for b in branches]

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")

selected_date_str = selected_date.strftime("%Y-%m-%d")

all_items = {}





if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
# ---------------- FETCH SHEET ----------------
@st.cache_data(ttl=300)
def get_sheet(sheet_id):
    file = client.open_by_key(sheet_id)
    ws = file.worksheet("Stocks")
    return ws.get_all_values()

# ---------------- PROCESS ----------------
for branch in branches:
    branch_name = branch["BranchName"]
    sheet_id = branch["SheetID"]

    try:
        raw = get_sheet(sheet_id)

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]
        rows = raw[1:]

        df = pd.DataFrame(rows, columns=headers)

        item_col = headers[0]

        # ---------------- FIND DATE COLUMN (YOUR FORMAT: YYYY-MM-DD) ----------------
        if selected_date_str not in headers:
            continue

        chosen_col = selected_date_str

        # ---------------- BUILD DATA ----------------
        for _, row in df.iterrows():
            item = str(row[item_col]).strip()
            qty = row.get(chosen_col, "")

            if item not in all_items:
                all_items[item] = {bn: 0 for bn in branch_names}

            try:
                all_items[item][branch_name] = float(qty) if qty != "" else 0
            except:
                all_items[item][branch_name] = 0

    except Exception as e:
        st.error(f"{branch_name} error: {e}")

# ---------------- FINAL DATAFRAME ----------------
rows = []
for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- DISPLAY ----------------
st.subheader("📊 Stock Data")
st.dataframe(df, use_container_width=True)

# ---------------- LOW STOCK HIGHLIGHT ----------------
st.markdown("## ⚠️ Low Stock Highlight")

if df.empty:
    st.warning("No stock data found for selected date")
    st.stop()

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

# SAFE COLUMN SELECTION
valid_columns = [col for col in branch_names if col in df.columns]

styled_df = df.style.applymap(highlight_low, subset=valid_columns)

st.dataframe(styled_df, use_container_width=True)
